"""
Fix failed HTML to Markdown conversions
Identify and convert the 23 files that failed
"""

import gzip
import re
import html
from pathlib import Path
from bs4 import BeautifulSoup
import chardet

# List of files that failed in the batch conversion
failed_files = [
    "act_102.html.gz", "act_104.html.gz", "act_115.html.gz", "act_127.html.gz",
    "act_133.html.gz", "act_134.html.gz", "act_140.html.gz", "act_145.html.gz",
    "act_149.html.gz", "act_159.html.gz", "act_160.html.gz", "act_170.html.gz",
    "act_175.html.gz", "act_177.html.gz", "act_178.html.gz", "act_243.html.gz",
    "act_244.html.gz", "act_245.html.gz", "act_275.html.gz", "act_276.html.gz",
    "act_277.html.gz", "act_290.html.gz", "act_294.html.gz"
]


def aggressive_html_extract(raw_content: bytes) -> str:
    """More aggressive extraction for problematic files"""

    # Try multiple decodings
    text = ""
    for encoding in ['utf-8', 'utf-16', 'utf-16-be', 'latin-1', 'windows-1252']:
        try:
            text = raw_content.decode(encoding, errors='ignore')
            break
        except:
            continue

    if not text:
        # Force decode with UTF-8 ignore
        text = raw_content.decode('utf-8', errors='ignore')

    # Clean up various encoding artifacts
    text = text.replace('\ufffd', '')  # Replacement character
    text = text.replace('\ufeff', '')  # BOM
    text = text.replace('ï¿½', '')     # Another form of replacement char

    # Handle double-encoded HTML
    if '&lt;' in text or '&gt;' in text:
        text = html.unescape(text)

    # Extract from wrapper if present
    if '<html><body>' in text:
        match = re.search(r'<html><body>(.*?)</body></html>', text, re.DOTALL)
        if match:
            text = html.unescape(match.group(1))

    return text


def extract_minimal_text(html_content: str) -> dict:
    """Extract text with minimal requirements for failed files"""

    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove all scripts, styles, etc.
    for element in soup(['script', 'style', 'meta', 'link', 'nav', 'header', 'footer']):
        element.decompose()

    result = {
        'title': '',
        'content': ''
    }

    # Try to find title in multiple ways
    title_sources = [
        soup.find('h3'),
        soup.find('h2'),
        soup.find('h1'),
        soup.find('title'),
        soup.find('div', class_='text-center'),
    ]

    for elem in title_sources:
        if elem:
            title = elem.get_text(strip=True)
            if title and len(title) > 5:
                result['title'] = title
                break

    # If still no title, try to extract from meta or URL patterns
    if not result['title']:
        meta_title = soup.find('meta', {'name': 'Description'})
        if meta_title:
            desc = meta_title.get('content', '')
            if 'Act' in desc:
                # Extract act name from description
                result['title'] = desc.split('.')[0].strip()

    # Get all text content
    text_content = soup.get_text(separator='\n', strip=True)

    # Clean up the text
    lines = text_content.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        # Skip navigation, menu items, and very short lines
        if line and len(line) > 3:
            # Skip common navigation patterns
            skip_patterns = [
                r'^Home\s*$', r'^About\s*$', r'^Contact\s*$',
                r'^Menu\s*$', r'^Search\s*$', r'^Related Links\s*$',
                r'^Footer\s*$', r'^Navigation\s*$'
            ]

            if not any(re.match(pattern, line, re.IGNORECASE) for pattern in skip_patterns):
                cleaned_lines.append(line)

    # Join the content
    result['content'] = '\n'.join(cleaned_lines)

    # If we have very little content, try to get raw text
    if len(result['content']) < 200:
        # Get all visible text
        for elem in soup.find_all(text=True):
            parent = elem.parent
            if parent.name not in ['script', 'style', 'meta', 'link']:
                text = elem.strip()
                if text and len(text) > 10:
                    result['content'] += '\n' + text

    return result


def process_failed_file(input_path: Path, output_path: Path) -> bool:
    """Process a single failed file with aggressive extraction"""

    try:
        # Read as bytes first
        if input_path.suffix == '.gz':
            with gzip.open(input_path, 'rb') as f:
                raw_bytes = f.read()
        else:
            with open(input_path, 'rb') as f:
                raw_bytes = f.read()

        # Aggressive HTML extraction
        html_content = aggressive_html_extract(raw_bytes)

        # Extract whatever text we can find
        extracted = extract_minimal_text(html_content)

        # Build markdown
        markdown_lines = []

        if extracted['title']:
            markdown_lines.append(f"# {extracted['title']}")
            markdown_lines.append("")
        else:
            # Use filename as title
            act_num = input_path.stem.replace('act_', '').replace('.html', '')
            markdown_lines.append(f"# Act {act_num}")
            markdown_lines.append("")

        if extracted['content']:
            # Clean up content
            content = re.sub(r'\n{3,}', '\n\n', extracted['content'])
            markdown_lines.append(content)

        markdown = '\n'.join(markdown_lines)

        # Save if we have meaningful content
        if len(markdown) >= 50:  # Lower threshold for failed files
            with gzip.open(output_path, 'wt', encoding='utf-8') as f:
                f.write(markdown)
            return True
        else:
            return False

    except Exception as e:
        print(f"    Error: {str(e)}")
        return False


def fix_failed_files():
    """Fix all failed files"""

    data_dir = Path("../../data/raw/acts")

    print("=" * 70)
    print("FIXING FAILED HTML CONVERSIONS")
    print("=" * 70)
    print(f"Files to fix: {len(failed_files)}")
    print("-" * 70)

    fixed_count = 0
    still_failed = []

    for filename in failed_files:
        input_path = data_dir / filename
        # Output to corresponding .md.gz file
        output_path = data_dir / filename.replace('.html.gz', '.md.gz')

        if not input_path.exists():
            print(f"\n[SKIP] {filename} - File not found")
            continue

        print(f"\nProcessing: {filename}")

        success = process_failed_file(input_path, output_path)

        if success:
            print(f"  [OK] Fixed and saved to {output_path.name}")

            # Show what was extracted
            with gzip.open(output_path, 'rt', encoding='utf-8') as f:
                content = f.read()
                print(f"  Size: {len(content)} characters")

                # Show title
                if content.startswith('#'):
                    title_line = content.split('\n')[0]
                    print(f"  Title: {title_line}")

            fixed_count += 1
        else:
            print(f"  [FAIL] Still failed - insufficient content")
            still_failed.append(filename)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total files to fix: {len(failed_files)}")
    print(f"Successfully fixed: {fixed_count}")
    print(f"Still failed: {len(still_failed)}")

    if still_failed:
        print(f"\nFiles that still failed:")
        for f in still_failed:
            print(f"  - {f}")

    success_rate = (fixed_count / len(failed_files)) * 100 if failed_files else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")

    if fixed_count > 0:
        print(f"\n[SUCCESS] Fixed {fixed_count} additional files!")
        print("Ready for re-ingestion")

    return fixed_count, still_failed


if __name__ == "__main__":
    fix_failed_files()