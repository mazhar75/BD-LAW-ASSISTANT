"""
Fixed HTML to Markdown Converter for Bangladesh Law Documents
Properly handles the UTF-16BE encoded HTML files
"""

import gzip
import re
from pathlib import Path
from bs4 import BeautifulSoup
import chardet

def fix_encoding(content: bytes) -> str:
    """Fix encoding issues in the HTML content"""
    # Try to detect encoding
    detection = chardet.detect(content[:10000])
    encoding = detection['encoding'] if detection['encoding'] else 'utf-8'

    try:
        # Try detected encoding
        return content.decode(encoding, errors='ignore')
    except:
        # Try common encodings
        for enc in ['utf-16-be', 'utf-16', 'utf-8', 'latin-1', 'windows-1252']:
            try:
                return content.decode(enc, errors='ignore')
            except:
                continue

    # Last resort - force UTF-8 with ignore
    return content.decode('utf-8', errors='ignore')


def extract_clean_text(html_content: str) -> str:
    """Extract clean text from Bangladesh law HTML"""

    # Remove the weird characters
    html_content = html_content.replace('�', '')

    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove unwanted elements
    for element in soup(['script', 'style', 'meta', 'link', 'nav', 'header', 'footer']):
        element.decompose()

    # Extract title
    title = ""
    title_elem = soup.find('h3')
    if title_elem:
        title = title_elem.get_text(strip=True)
    elif soup.find('title'):
        title = soup.find('title').get_text(strip=True)

    # Extract act number
    act_number = ""
    h4_elem = soup.find('h4', style="color: #fff;")
    if h4_elem:
        act_number = h4_elem.get_text(strip=True)

    # Extract date
    date = ""
    date_elem = soup.find('p', class_='publish-date')
    if date_elem:
        date = date_elem.get_text(strip=True)

    # Build markdown
    markdown_lines = []

    if title:
        markdown_lines.append(f"# {title}\n")

    if act_number:
        markdown_lines.append(f"**{act_number}**\n")

    if date:
        markdown_lines.append(f"*{date}*\n")

    markdown_lines.append("")  # Empty line

    # Extract preamble
    preamble_div = soup.find('div', string=re.compile(r'Preamble', re.I))
    if preamble_div:
        preamble_content = preamble_div.find_next_sibling('div')
        if preamble_content:
            text = preamble_content.get_text(strip=True)
            if text:
                markdown_lines.append("## Preamble\n")
                markdown_lines.append(text + "\n")

    # Extract sections - look for the section rows
    section_rows = soup.find_all('div', class_='row lineremoves')

    for row in section_rows:
        # Find section heading
        heading_elem = row.find('div', class_='txt-head')
        content_elem = row.find('div', class_='txt-details')

        if heading_elem and content_elem:
            heading = heading_elem.get_text(strip=True)
            content = content_elem.get_text(strip=True)

            # Clean up the content
            content = re.sub(r'\s+', ' ', content)

            if heading and content:
                markdown_lines.append(f"## {heading}\n")
                markdown_lines.append(f"{content}\n")

    # If no structured sections found, try to extract main content
    if len(markdown_lines) < 5:
        main_content = soup.find('section', class_='padding-bottom-20')
        if not main_content:
            main_content = soup.find('div', class_='col-md-11')

        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
            # Clean up
            text = re.sub(r'\n{3,}', '\n\n', text)
            markdown_lines.append(text)

    return '\n'.join(markdown_lines).strip()


def convert_file(input_path: Path, output_path: Path) -> bool:
    """Convert a single HTML file to clean markdown"""

    print(f"Processing: {input_path.name}")

    try:
        # Read the HTML file as bytes first
        if input_path.suffix == '.gz':
            with gzip.open(input_path, 'rb') as f:
                content_bytes = f.read()
        else:
            with open(input_path, 'rb') as f:
                content_bytes = f.read()

        # Fix encoding
        html_content = fix_encoding(content_bytes)

        # Extract clean text
        markdown = extract_clean_text(html_content)

        if not markdown or len(markdown) < 100:
            print(f"  [WARNING] Little or no content extracted")
            return False

        # Save clean markdown
        with gzip.open(output_path, 'wt', encoding='utf-8') as f:
            f.write(markdown)

        print(f"  [OK] Extracted {len(markdown)} characters")

        # Show preview (ASCII safe)
        preview = markdown[:300].encode('ascii', 'ignore').decode('ascii')
        preview_lines = preview.split('\n')[:5]
        print(f"  Preview:")
        for line in preview_lines:
            if line.strip():
                print(f"    {line[:80]}")

        return True

    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False


def test_conversion():
    """Test conversion on sample files"""

    data_dir = Path("../../data/raw/acts")

    print("=" * 70)
    print("HTML TO MARKDOWN CONVERSION TEST - FIXED VERSION")
    print("=" * 70)

    # Test files
    test_files = [
        ("act_2.html.gz", "act_2.clean.md.gz"),
        ("act_100.html.gz", "act_100.clean.md.gz")
    ]

    success_count = 0

    for input_name, output_name in test_files:
        input_path = data_dir / input_name
        output_path = data_dir / output_name

        if input_path.exists():
            print(f"\n--- File: {input_name} ---")
            if convert_file(input_path, output_path):
                success_count += 1

                # Check the output
                print(f"  Output saved to: {output_name}")
        else:
            print(f"\n[ERROR] {input_name} not found")

    print("\n" + "=" * 70)
    print(f"RESULTS: {success_count}/{len(test_files)} files converted successfully")
    print("=" * 70)

    return success_count > 0


if __name__ == "__main__":
    test_conversion()