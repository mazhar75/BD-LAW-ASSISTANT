"""
Test data migration without PostgreSQL
"""
import sys
from pathlib import Path
import gzip
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

print("="*60)
print("Testing Data Migration Logic")
print("="*60)

# Test file reading
data_dir = Path("../../data/raw/acts")

if data_dir.exists():
    # Find act files
    act_files = sorted(data_dir.glob("act_*.md.gz"))[:5]  # Test with first 5

    print(f"\nFound {len(act_files)} act files to test")
    print("-"*40)

    for act_file in act_files:
        try:
            # Extract act number
            act_number = int(act_file.stem.split('_')[1].split('.')[0])

            # Load markdown content
            with gzip.open(act_file, 'rt', encoding='utf-8') as f:
                content = f.read()

            # Load metadata if exists
            meta_file = act_file.parent / f"act_{act_number}.meta.json"
            metadata = {}
            if meta_file.exists():
                with open(meta_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

            # Extract title (first non-empty, non-header line)
            title = "Unknown Act"
            lines = content.split('\n')
            for line in lines[:10]:
                line = line.strip()
                if line and not line.startswith('#'):
                    title = line[:100]  # Limit title length
                    break

            print(f"\nAct {act_number}:")
            print(f"  Title: {title}")
            print(f"  Content size: {len(content)} chars")
            print(f"  Metadata: {list(metadata.keys())}")
            print(f"  URL: {metadata.get('url', 'N/A')}")

        except Exception as e:
            print(f"\nError processing {act_file.name}: {e}")

    print("\n" + "="*60)
    print("Migration test completed!")
    print("="*60)
    print("\nNOTE: To run actual migration to PostgreSQL:")
    print("1. Start PostgreSQL: docker-compose up -d postgres")
    print("2. Run setup: python services/rag/database/setup.py")
    print("3. Run migration: python services/rag/data_migration.py --test")

else:
    print(f"Data directory not found: {data_dir}")
    print("Make sure scraped data exists in data/raw/acts/")