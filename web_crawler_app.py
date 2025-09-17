"""
Scalable Web-based BD Laws Crawler with UI
Supports both English and Bengali content
"""
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import threading
import queue
import time
import json
from datetime import datetime
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from scrapers.bd_law_crawler import BDLawCrawler
from scrapers.utils.logger import get_logger

app = Flask(__name__)
CORS(app)

class CrawlerManager:
    """Manages crawler operations with monitoring"""

    def __init__(self):
        self.crawler = BDLawCrawler()
        self.logger = get_logger("web_crawler")
        self.current_job = None
        self.job_status = {}
        self.progress_queue = queue.Queue()
        self.is_running = False

    def crawl_range(self, start_act, end_act, language='en'):
        """Crawl a range of acts"""
        self.is_running = True
        self.current_job = {
            'start': start_act,
            'end': end_act,
            'language': language,
            'total': end_act - start_act + 1,
            'completed': 0,
            'successful': 0,
            'failed': 0,
            'current_act': None,
            'start_time': datetime.now().isoformat(),
            'status': 'running',
            'errors': []
        }

        # Test connection
        if not self.crawler.firecrawl.test_connection():
            self.current_job['status'] = 'failed'
            self.current_job['errors'].append('Failed to connect to Firecrawl API')
            self.is_running = False
            return False

        for act_num in range(start_act, end_act + 1):
            if not self.is_running:
                self.current_job['status'] = 'stopped'
                break

            # Build URL with language parameter
            if language == 'bn':
                url = f"http://bdlaws.minlaw.gov.bd/act-details-{act_num}.html?lang=bn"
            else:
                url = f"http://bdlaws.minlaw.gov.bd/act-details-{act_num}.html"

            self.current_job['current_act'] = act_num

            # Update progress
            progress_msg = {
                'act': act_num,
                'total': self.current_job['total'],
                'completed': self.current_job['completed'],
                'status': 'processing',
                'url': url
            }
            self.progress_queue.put(progress_msg)

            # Clear queue and add URL
            self.crawler.queue.clear_queue("all")
            self.crawler.queue_urls([url])

            # Process task
            task = self.crawler.queue.dequeue()
            if not task:
                self.current_job['failed'] += 1
                self.current_job['errors'].append(f"Act {act_num}: No task in queue")
            else:
                try:
                    success = self.crawler.process_task(task)
                    if success:
                        self.current_job['successful'] += 1
                        progress_msg['status'] = 'success'
                    else:
                        self.current_job['failed'] += 1
                        progress_msg['status'] = 'failed'
                except Exception as e:
                    self.current_job['failed'] += 1
                    self.current_job['errors'].append(f"Act {act_num}: {str(e)[:100]}")
                    progress_msg['status'] = 'error'

            self.current_job['completed'] += 1
            self.progress_queue.put(progress_msg)

            # Rate limiting
            time.sleep(2)

        # Mark job as complete
        self.current_job['status'] = 'completed'
        self.current_job['end_time'] = datetime.now().isoformat()
        self.is_running = False

        # Save job summary
        self.save_job_summary()

        return True

    def save_job_summary(self):
        """Save job summary to file"""
        summary_file = Path(f"data/logs/job_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        summary_file.parent.mkdir(parents=True, exist_ok=True)

        with open(summary_file, 'w') as f:
            json.dump(self.current_job, f, indent=2)

    def stop_crawling(self):
        """Stop current crawling job"""
        self.is_running = False
        if self.current_job:
            self.current_job['status'] = 'stopped'

    def get_status(self):
        """Get current crawler status"""
        if not self.current_job:
            return {'status': 'idle'}

        status = self.current_job.copy()

        # Calculate success rate
        if status['completed'] > 0:
            status['success_rate'] = (status['successful'] / status['completed']) * 100
        else:
            status['success_rate'] = 0

        # Calculate ETA
        if status['completed'] > 0 and status['status'] == 'running':
            elapsed = (datetime.now() - datetime.fromisoformat(status['start_time'])).total_seconds()
            avg_time_per_act = elapsed / status['completed']
            remaining = status['total'] - status['completed']
            eta_seconds = avg_time_per_act * remaining
            status['eta'] = f"{int(eta_seconds / 60)} minutes"
        else:
            status['eta'] = 'Unknown'

        return status

# Create global crawler manager
crawler_manager = CrawlerManager()

@app.route('/')
def index():
    """Main UI page"""
    return render_template('crawler_ui.html')

@app.route('/api/start', methods=['POST'])
def start_crawling():
    """Start crawling endpoint"""
    if crawler_manager.is_running:
        return jsonify({'error': 'Crawler is already running'}), 400

    data = request.json
    start_act = int(data.get('start', 1))
    end_act = int(data.get('end', 10))
    language = data.get('language', 'en')

    # Validate input
    if start_act < 1 or end_act > 1303 or start_act > end_act:
        return jsonify({'error': 'Invalid act range. Must be between 1-1303'}), 400

    # Start crawler in background thread
    thread = threading.Thread(
        target=crawler_manager.crawl_range,
        args=(start_act, end_act, language)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'message': 'Crawler started', 'start': start_act, 'end': end_act})

@app.route('/api/stop', methods=['POST'])
def stop_crawling():
    """Stop crawling endpoint"""
    crawler_manager.stop_crawling()
    return jsonify({'message': 'Crawler stopped'})

@app.route('/api/status')
def get_status():
    """Get crawler status"""
    return jsonify(crawler_manager.get_status())

@app.route('/api/progress')
def progress_stream():
    """Server-sent events for real-time progress"""
    def generate():
        while True:
            try:
                # Get progress update with timeout
                progress = crawler_manager.progress_queue.get(timeout=1)
                yield f"data: {json.dumps(progress)}\n\n"
            except:
                # Send heartbeat
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
            time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream")

@app.route('/api/stats')
def get_stats():
    """Get storage statistics"""
    data_dir = Path("data/raw/acts")

    stats = {
        'total_files': 0,
        'total_size_mb': 0,
        'acts_crawled': 0,
        'languages': {'en': 0, 'bn': 0}
    }

    if data_dir.exists():
        files = list(data_dir.glob("*.meta.json"))
        stats['acts_crawled'] = len(files)
        stats['total_files'] = len(list(data_dir.glob("*")))

        # Calculate total size
        total_size = sum(f.stat().st_size for f in data_dir.glob("*"))
        stats['total_size_mb'] = round(total_size / (1024 * 1024), 2)

        # Count languages
        for meta_file in files:
            with open(meta_file, 'r', encoding='utf-8') as f:
                try:
                    meta = json.load(f)
                    lang = meta.get('language', 'en')
                    if lang in stats['languages']:
                        stats['languages'][lang] += 1
                except:
                    pass

    return jsonify(stats)

@app.route('/api/recent')
def get_recent():
    """Get recently crawled acts"""
    data_dir = Path("data/raw/acts")
    recent = []

    if data_dir.exists():
        files = sorted(
            data_dir.glob("*.meta.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:10]

        for f in files:
            with open(f, 'r', encoding='utf-8') as file:
                try:
                    meta = json.load(file)
                    recent.append({
                        'act_id': f.stem.replace('act_', '').replace('.meta', ''),
                        'url': meta.get('url', ''),
                        'language': meta.get('language', 'en'),
                        'crawled_at': meta.get('crawled_at', ''),
                        'size': f.stat().st_size
                    })
                except:
                    pass

    return jsonify(recent)

if __name__ == '__main__':
    # Create templates directory
    Path("templates").mkdir(exist_ok=True)

    print("\n" + "="*60)
    print("BD LAWS CRAWLER WEB UI")
    print("="*60)
    print("\nStarting web server...")
    print("Open browser and go to: http://localhost:5000")
    print("\nFeatures:")
    print("  • Crawl any range of acts (1-1303)")
    print("  • Support for English and Bengali")
    print("  • Real-time progress monitoring")
    print("  • Storage statistics")
    print("  • Recent crawls display")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")

    app.run(debug=False, port=5000, host='0.0.0.0')