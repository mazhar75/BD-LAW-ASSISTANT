"""
Batch HTML to Markdown Converter for all Bangladesh Law Documents
Converts all HTML files to clean markdown and replaces the existing .md.gz files
"""

import gzip
import re
import html
from pathlib import Path
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
from datetime import datetime


def decode_html_content(raw_content: str) -> str:
    """Decode double-encoded HTML content"""

    # First, unescape HTML entities
    content = html.unescape(raw_content)

    # Remove BOM and other weird characters
    content = content.replace('\ufeff', '')  # BOM
    content = content.replace('�', '')  # Replacement character

    # Extract the actual HTML from the wrapper
    if '<html><body>' in content:
        match = re.search(r'<html><body>(.*?)</body></html>', content, re.DOTALL)
        if match:
            content = match.group(1)
            content = html.unescape(content)

    return content


def extract_law_text(html_content: str) -> dict:
    """Extract structured text from law HTML"""

    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'meta', 'link']):
        element.decompose()

    result = {
        'title': '',
        'act_number': '',
        'date': '',
        'preamble': '',
        'sections': []
    }

    # Extract title
    title_elem = soup.find('h3')
    if title_elem:
        result['title'] = title_elem.get_text(strip=True)

    # Extract act number
    act_elem = soup.find('h4')
    if act_elem:
        result['act_number'] = act_elem.get_text(strip=True).replace('(', '').replace(')', '').strip()

    # Extract date
    date_elem = soup.find('p', class_='publish-date')
    if date_elem:
        result['date'] = date_elem.get_text(strip=True).replace('[', '').replace(']', '').strip()

    # Extract preamble
    for row in soup.find_all('div', class_='row'):
        if 'Preamble' in row.get_text():
            preamble_content = row.find('div', class_='col-md-10')
            if preamble_content:
                result['preamble'] = preamble_content.get_text(strip=True)
                break

    # Extract sections
    section_rows = soup.find_all('div', class_='row lineremoves')
    for row in section_rows:
        heading_div = row.find('div', class_='txt-head')
        content_div = row.find('div', class_='txt-details')

        if heading_div and content_div:
            section = {
                'heading': heading_div.get_text(strip=True),
                'content': content_div.get_text(strip=True)
            }
            # Clean up content
            section['content'] = re.sub(r'\s+', ' ', section['content'])
            result['sections'].append(section)

    return result


def convert_to_markdown(law_data: dict) -> str:
    """Convert structured law data to clean markdown"""

    lines = []

    # Title
    if law_data['title']:
        lines.append(f"# {law_data['title']}")
        lines.append("")

    # Act number and date
    if law_data['act_number']:
        # Clean up act number formatting
        act_num = ' '.join(law_data['act_number'].split())
        lines.append(f"**{act_num}**")
        lines.append("")

    if law_data['date']:
        lines.append(f"*Date: {law_data['date']}*")
        lines.append("")

    # Preamble
    if law_data['preamble']:
        lines.append("## Preamble")
        lines.append("")
        lines.append(law_data['preamble'])
        lines.append("")

    # Sections
    for section in law_data['sections']:
        if section['heading'] and section['content']:
            lines.append(f"## {section['heading']}")
            lines.append("")
            lines.append(section['content'])
            lines.append("")

    return '\n'.join(lines)


def process_file(input_path: Path, output_path: Path) -> tuple:
    """Process a single HTML file and return (success, char_count)"""

    try:
        # Read the file
        with gzip.open(input_path, 'rt', encoding='utf-8', errors='ignore') as f:
            raw_content = f.read()

        # Decode the HTML
        html_content = decode_html_content(raw_content)

        # Extract structured data
        law_data = extract_law_text(html_content)

        # Convert to markdown
        markdown = convert_to_markdown(law_data)

        if not markdown or len(markdown) < 100:
            return False, 0

        # Save the clean markdown
        with gzip.open(output_path, 'wt', encoding='utf-8') as f:
            f.write(markdown)

        return True, len(markdown)

    except Exception as e:
        return False, 0


def batch_convert():
    """Convert all HTML files to clean markdown"""

    data_dir = Path("../../data/raw/acts")

    print("=" * 70)
    print("BATCH HTML TO MARKDOWN CONVERTER")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Find all HTML files
    html_files = sorted(data_dir.glob("act_*.html.gz"))

    print(f"\nFound {len(html_files)} HTML files to convert")

    if not html_files:
        print("No HTML files found!")
        return

    # Statistics
    success_count = 0
    failed_count = 0
    total_chars = 0
    failed_files = []

    print("\nConverting files...")
    print("-" * 70)

    # Process each file with progress bar
    for html_file in tqdm(html_files, desc="Converting"):
        # Replace .html.gz with .md.gz for output
        output_file = html_file.parent / html_file.name.replace('.html.gz', '.md.gz')

        success, char_count = process_file(html_file, output_file)

        if success:
            success_count += 1
            total_chars += char_count
        else:
            failed_count += 1
            failed_files.append(html_file.name)

    # Summary
    print("\n" + "=" * 70)
    print("CONVERSION SUMMARY")
    print("=" * 70)

    print(f"Total files processed: {len(html_files)}")
    print(f"Successfully converted: {success_count}")
    print(f"Failed conversions: {failed_count}")

    if success_count > 0:
        avg_chars = total_chars / success_count
        print(f"Average document size: {avg_chars:.0f} characters")
        print(f"Total text extracted: {total_chars:,} characters")

    if failed_files:
        print(f"\nFailed files ({len(failed_files)}):")
        for f in failed_files[:10]:  # Show first 10
            print(f"  - {f}")
        if len(failed_files) > 10:
            print(f"  ... and {len(failed_files) - 10} more")

    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Success rate
    success_rate = (success_count / len(html_files)) * 100 if html_files else 0

    print("\n" + "=" * 70)
    if success_rate >= 90:
        print(f"✓ BATCH CONVERSION SUCCESSFUL ({success_rate:.1f}% success rate)")
        print("Ready for re-ingestion!")
    elif success_rate >= 70:
        print(f"⚠ PARTIAL SUCCESS ({success_rate:.1f}% success rate)")
        print("Most files converted, check failed files")
    else:
        print(f"✗ CONVERSION FAILED ({success_rate:.1f}% success rate)")
        print("Too many failures, please investigate")
    print("=" * 70)

    return success_count, failed_count


if __name__ == "__main__":
    batch_convert()