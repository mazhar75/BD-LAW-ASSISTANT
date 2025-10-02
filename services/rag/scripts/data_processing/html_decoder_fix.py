"""
HTML Decoder and Text Extractor for Bangladesh Law Documents
Handles double-encoded HTML with proper decoding
"""

import gzip
import re
import html
from pathlib import Path
from bs4 import BeautifulSoup


def decode_html_content(raw_content: str) -> str:
    """Decode double-encoded HTML content"""

    # First, unescape HTML entities
    content = html.unescape(raw_content)

    # Remove BOM and other weird characters
    content = content.replace('\ufeff', '')  # BOM
    content = content.replace('�', '')  # Replacement character

    # Extract the actual HTML from the wrapper
    # The content appears to be wrapped in <html><body>ACTUAL_CONTENT</body></html>
    if '<html><body>' in content:
        # Extract content between <html><body> and </body></html>
        match = re.search(r'<html><body>(.*?)</body></html>', content, re.DOTALL)
        if match:
            content = match.group(1)
            # Unescape again as the inner content is also escaped
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
        lines.append(f"**{law_data['act_number']}**")
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


def process_file(input_path: Path, output_path: Path) -> bool:
    """Process a single HTML file"""

    print(f"\nProcessing: {input_path.name}")

    try:
        # Read the file
        if input_path.suffix == '.gz':
            with gzip.open(input_path, 'rt', encoding='utf-8', errors='ignore') as f:
                raw_content = f.read()
        else:
            with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_content = f.read()

        # Decode the HTML
        html_content = decode_html_content(raw_content)

        # Extract structured data
        law_data = extract_law_text(html_content)

        # Convert to markdown
        markdown = convert_to_markdown(law_data)

        if not markdown or len(markdown) < 100:
            print(f"  [WARNING] Insufficient content extracted ({len(markdown)} chars)")
            return False

        # Save the clean markdown
        with gzip.open(output_path, 'wt', encoding='utf-8') as f:
            f.write(markdown)

        print(f"  [OK] Converted successfully")
        print(f"  Title: {law_data['title'][:80] if law_data['title'] else 'N/A'}")
        print(f"  Sections found: {len(law_data['sections'])}")
        print(f"  Total size: {len(markdown)} characters")

        return True

    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False


def test_conversion():
    """Test the conversion process"""

    data_dir = Path("../../data/raw/acts")

    print("=" * 70)
    print("HTML DECODER AND TEXT EXTRACTOR TEST")
    print("=" * 70)

    # Test with problematic files
    test_files = [
        "act_2.html.gz",
        "act_100.html.gz"
    ]

    results = []

    for filename in test_files:
        input_path = data_dir / filename
        output_path = data_dir / filename.replace('.html.gz', '.clean.md.gz')

        if input_path.exists():
            success = process_file(input_path, output_path)
            results.append((filename, success))

            if success:
                # Show a preview of the output
                print(f"\n  Preview of {output_path.name}:")
                with gzip.open(output_path, 'rt', encoding='utf-8') as f:
                    preview = f.read(500)
                    for line in preview.split('\n')[:10]:
                        if line.strip():
                            print(f"    {line[:80]}")
        else:
            print(f"\n[ERROR] {filename} not found")
            results.append((filename, False))

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    success_count = sum(1 for _, success in results if success)
    print(f"Successfully converted: {success_count}/{len(results)}")

    for filename, success in results:
        status = "[OK]" if success else "[FAIL]"
        print(f"  {status} {filename}")

    return success_count > 0


if __name__ == "__main__":
    test_conversion()