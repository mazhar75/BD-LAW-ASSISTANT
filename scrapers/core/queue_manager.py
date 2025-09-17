"""
Redis-based queue management for distributed scraping
"""
import redis
import json
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import pickle

from scrapers.config.settings import get_settings
from scrapers.utils.logger import get_logger


class QueuePriority(Enum):
    """Queue priority levels"""
    HIGH = 1
    NORMAL = 5
    LOW = 10


class QueueStatus(Enum):
    """Task status in queue"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class QueueTask:
    """Task object for queue"""
    id: str
    type: str
    url: str
    data: Dict[str, Any]
    priority: int
    status: QueueStatus
    created_at: datetime
    updated_at: datetime
    attempts: int = 0
    max_retries: int = 3
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for Redis storage"""
        return {
            'id': self.id,
            'type': self.type,
            'url': self.url,
            'data': self.data,
            'priority': self.priority,
            'status': self.status.value if isinstance(self.status, QueueStatus) else self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'attempts': self.attempts,
            'max_retries': self.max_retries,
            'error': self.error
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'QueueTask':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            type=data['type'],
            url=data['url'],
            data=data.get('data', {}),
            priority=data.get('priority', QueuePriority.NORMAL.value),
            status=QueueStatus(data['status']) if isinstance(data['status'], str) else data['status'],
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at'],
            updated_at=datetime.fromisoformat(data['updated_at']) if isinstance(data['updated_at'], str) else data['updated_at'],
            attempts=data.get('attempts', 0),
            max_retries=data.get('max_retries', 3),
            error=data.get('error')
        )


class RedisQueueManager:
    """
    Redis-based queue manager for scalable task processing
    """

    def __init__(self, queue_name: str = "scraper_queue"):
        self.settings = get_settings()
        self.logger = get_logger("queue_manager")
        self.queue_name = queue_name

        # Connect to Redis
        self.redis_client = redis.Redis(
            host=self.settings.redis.host,
            port=self.settings.redis.port,
            db=self.settings.redis.db,
            password=self.settings.redis.password,
            decode_responses=False  # Use binary for complex objects
        )

        # Queue keys
        self.pending_queue = f"{queue_name}:pending"
        self.processing_queue = f"{queue_name}:processing"
        self.completed_queue = f"{queue_name}:completed"
        self.failed_queue = f"{queue_name}:failed"
        self.dead_letter_queue = f"{queue_name}:dead_letter"

        # Task hash for storing task details
        self.task_hash = f"{queue_name}:tasks"

        # Statistics key
        self.stats_key = f"{queue_name}:stats"

        # Initialize statistics
        self._initialize_stats()

    def _initialize_stats(self):
        """Initialize queue statistics"""
        if not self.redis_client.exists(self.stats_key):
            stats = {
                'total_enqueued': '0',
                'total_processed': '0',
                'total_failed': '0',
                'total_completed': '0',
                'started_at': datetime.now().isoformat()
            }
            # Use hmset or individual hset calls for older Redis versions
            for key, value in stats.items():
                self.redis_client.hset(self.stats_key, key, value)

    def enqueue(self, url: str, task_type: str = "scrape", priority: QueuePriority = QueuePriority.NORMAL,
                data: Dict = None, **kwargs) -> str:
        """
        Add a task to the queue

        Args:
            url: URL to process
            task_type: Type of task
            priority: Task priority
            data: Additional task data
            **kwargs: Additional task parameters

        Returns:
            Task ID
        """
        # Generate unique task ID
        task_id = f"{task_type}_{int(time.time() * 1000)}_{hash(url) & 0xFFFFFFFF}"

        # Create task object
        task = QueueTask(
            id=task_id,
            type=task_type,
            url=url,
            data=data or {},
            priority=priority.value if isinstance(priority, QueuePriority) else priority,
            status=QueueStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            **kwargs
        )

        # Store task data
        self.redis_client.hset(
            self.task_hash,
            task_id,
            pickle.dumps(task.to_dict())
        )

        # Add to pending queue with priority (lower score = higher priority)
        self.redis_client.zadd(
            self.pending_queue,
            {task_id: task.priority}
        )

        # Update statistics
        self.redis_client.hincrby(self.stats_key, 'total_enqueued', 1)

        self.logger.logger.info(
            "task_enqueued",
            task_id=task_id,
            url=url,
            type=task_type,
            priority=priority.name if isinstance(priority, QueuePriority) else priority
        )

        return task_id

    def enqueue_batch(self, urls: List[str], task_type: str = "scrape",
                      priority: QueuePriority = QueuePriority.NORMAL) -> List[str]:
        """
        Enqueue multiple URLs

        Args:
            urls: List of URLs
            task_type: Type of task
            priority: Task priority

        Returns:
            List of task IDs
        """
        task_ids = []
        pipe = self.redis_client.pipeline()

        for url in urls:
            task_id = f"{task_type}_{int(time.time() * 1000)}_{hash(url) & 0xFFFFFFFF}"

            task = QueueTask(
                id=task_id,
                type=task_type,
                url=url,
                data={},
                priority=priority.value if isinstance(priority, QueuePriority) else priority,
                status=QueueStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            pipe.hset(self.task_hash, task_id, pickle.dumps(task.to_dict()))
            pipe.zadd(self.pending_queue, {task_id: task.priority})
            task_ids.append(task_id)

        pipe.hincrby(self.stats_key, 'total_enqueued', len(urls))
        pipe.execute()

        self.logger.logger.info(
            "batch_enqueued",
            count=len(urls),
            task_type=task_type
        )

        return task_ids

    def dequeue(self, timeout: int = 0) -> Optional[QueueTask]:
        """
        Get next task from queue

        Args:
            timeout: Blocking timeout in seconds (0 = non-blocking)

        Returns:
            QueueTask or None
        """
        # Get highest priority task (lowest score) - compatible with older Redis
        # First get the item with lowest score
        items = self.redis_client.zrange(self.pending_queue, 0, 0, withscores=True)

        if not items:
            if timeout > 0:
                # Simple polling for blocking behavior
                end_time = time.time() + timeout
                while time.time() < end_time:
                    items = self.redis_client.zrange(self.pending_queue, 0, 0, withscores=True)
                    if items:
                        break
                    time.sleep(0.1)

                if not items:
                    return None
            else:
                return None

        # Remove the item from the queue
        task_id = items[0][0]
        self.redis_client.zrem(self.pending_queue, task_id)

        # Get task data
        task_data = self.redis_client.hget(self.task_hash, task_id)
        if not task_data:
            return None

        task_dict = pickle.loads(task_data)
        task = QueueTask.from_dict(task_dict)

        # Update task status
        task.status = QueueStatus.PROCESSING
        task.updated_at = datetime.now()
        task.attempts += 1

        # Update task in hash
        self.redis_client.hset(
            self.task_hash,
            task_id,
            pickle.dumps(task.to_dict())
        )

        # Add to processing queue
        self.redis_client.zadd(
            self.processing_queue,
            {task_id: time.time()}
        )

        self.logger.logger.info(
            "task_dequeued",
            task_id=task.id,
            url=task.url,
            attempts=task.attempts
        )

        return task

    def mark_completed(self, task_id: str, result: Any = None):
        """Mark task as completed"""
        # Get task data
        task_data = self.redis_client.hget(self.task_hash, task_id)
        if not task_data:
            return

        task_dict = pickle.loads(task_data)
        task = QueueTask.from_dict(task_dict)

        # Update task status
        task.status = QueueStatus.COMPLETED
        task.updated_at = datetime.now()
        if result:
            task.data['result'] = result

        # Update task in hash
        self.redis_client.hset(
            self.task_hash,
            task_id,
            pickle.dumps(task.to_dict())
        )

        # Remove from processing queue
        self.redis_client.zrem(self.processing_queue, task_id)

        # Add to completed queue
        self.redis_client.zadd(
            self.completed_queue,
            {task_id: time.time()}
        )

        # Update statistics
        self.redis_client.hincrby(self.stats_key, 'total_completed', 1)
        self.redis_client.hincrby(self.stats_key, 'total_processed', 1)

        self.logger.logger.info(
            "task_completed",
            task_id=task_id,
            url=task.url
        )

    def mark_failed(self, task_id: str, error: str):
        """Mark task as failed and potentially retry"""
        # Get task data
        task_data = self.redis_client.hget(self.task_hash, task_id)
        if not task_data:
            return

        task_dict = pickle.loads(task_data)
        task = QueueTask.from_dict(task_dict)

        task.error = error
        task.updated_at = datetime.now()

        # Check if should retry
        if task.attempts < task.max_retries:
            task.status = QueueStatus.RETRYING

            # Update task in hash
            self.redis_client.hset(
                self.task_hash,
                task_id,
                pickle.dumps(task.to_dict())
            )

            # Remove from processing queue
            self.redis_client.zrem(self.processing_queue, task_id)

            # Re-add to pending queue with lower priority (higher score)
            new_priority = task.priority + (task.attempts * 2)
            self.redis_client.zadd(
                self.pending_queue,
                {task_id: new_priority}
            )

            self.logger.logger.warning(
                "task_retrying",
                task_id=task_id,
                url=task.url,
                attempts=task.attempts,
                error=error
            )
        else:
            # Move to dead letter queue
            task.status = QueueStatus.FAILED

            self.redis_client.hset(
                self.task_hash,
                task_id,
                pickle.dumps(task.to_dict())
            )

            self.redis_client.zrem(self.processing_queue, task_id)
            self.redis_client.zadd(
                self.dead_letter_queue,
                {task_id: time.time()}
            )

            self.redis_client.hincrby(self.stats_key, 'total_failed', 1)

            self.logger.logger.error(
                "task_failed",
                task_id=task_id,
                url=task.url,
                attempts=task.attempts,
                error=error
            )

    def get_queue_status(self) -> Dict:
        """Get current queue status"""
        status = {
            'pending': self.redis_client.zcard(self.pending_queue),
            'processing': self.redis_client.zcard(self.processing_queue),
            'completed': self.redis_client.zcard(self.completed_queue),
            'failed': self.redis_client.zcard(self.dead_letter_queue),
        }

        # Get statistics
        stats = self.redis_client.hgetall(self.stats_key)
        for key, value in stats.items():
            try:
                status[key.decode()] = int(value.decode()) if value.isdigit() else value.decode()
            except:
                status[key.decode()] = value.decode()

        return status

    def get_task(self, task_id: str) -> Optional[QueueTask]:
        """Get task by ID"""
        task_data = self.redis_client.hget(self.task_hash, task_id)
        if task_data:
            return QueueTask.from_dict(pickle.loads(task_data))
        return None

    def clear_queue(self, queue_type: str = "all"):
        """Clear specified queue(s)"""
        queues_to_clear = []

        if queue_type == "all":
            queues_to_clear = [
                self.pending_queue,
                self.processing_queue,
                self.completed_queue,
                self.failed_queue,
                self.dead_letter_queue
            ]
        elif queue_type == "pending":
            queues_to_clear = [self.pending_queue]
        elif queue_type == "completed":
            queues_to_clear = [self.completed_queue]
        elif queue_type == "failed":
            queues_to_clear = [self.dead_letter_queue]

        for queue in queues_to_clear:
            self.redis_client.delete(queue)

        self.logger.logger.info("queue_cleared", queue_type=queue_type)

    def reprocess_failed(self) -> int:
        """Reprocess all failed tasks"""
        failed_tasks = self.redis_client.zrange(self.dead_letter_queue, 0, -1)
        count = 0

        for task_id in failed_tasks:
            task_data = self.redis_client.hget(self.task_hash, task_id)
            if task_data:
                task_dict = pickle.loads(task_data)
                task = QueueTask.from_dict(task_dict)

                # Reset task
                task.status = QueueStatus.PENDING
                task.attempts = 0
                task.error = None
                task.updated_at = datetime.now()

                # Update and re-queue
                self.redis_client.hset(
                    self.task_hash,
                    task_id,
                    pickle.dumps(task.to_dict())
                )
                self.redis_client.zadd(
                    self.pending_queue,
                    {task_id: task.priority}
                )
                count += 1

        # Clear dead letter queue
        self.redis_client.delete(self.dead_letter_queue)

        self.logger.logger.info("failed_tasks_reprocessed", count=count)
        return count

    def cleanup_old_tasks(self, days: int = 7):
        """Remove completed tasks older than specified days"""
        cutoff_time = time.time() - (days * 24 * 3600)

        # Get old completed tasks
        old_tasks = self.redis_client.zrangebyscore(
            self.completed_queue,
            '-inf',
            cutoff_time
        )

        # Remove from hash and queue
        if old_tasks:
            pipe = self.redis_client.pipeline()
            for task_id in old_tasks:
                pipe.hdel(self.task_hash, task_id)
                pipe.zrem(self.completed_queue, task_id)
            pipe.execute()

        self.logger.logger.info(
            "old_tasks_cleaned",
            count=len(old_tasks),
            days=days
        )