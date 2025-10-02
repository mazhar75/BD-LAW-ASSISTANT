"""
HTML to Markdown Converter for Bangladesh Law Documents
Extracts clean text from HTML files and converts to markdown
"""

import gzip
import re
from pathlib import Path
from bs4 import BeautifulSoup
import html2text

def extract_clean_text_from_html(html_content: str) -> str:
    """Extract clean text from HTML content"""

    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script and style elements
    for script in soup(["script", "style", "meta", "link", "noscript"]):
        script.decompose()

    # Find the main content area (specific to bdlaws.minlaw.gov.bd)
    main_content = None

    # Try different content containers
    content_divs = [
        soup.find('div', {'class': 'act-content'}),
        soup.find('div', {'class': 'content'}),
        soup.find('div', {'id': 'content'}),
        soup.find('main'),
        soup.find('article'),
        soup.find('div', {'class': 'container'})
    ]

    for div in content_divs:
        if div:
            main_content = div
            break

    # If no specific container found, use body
    if not main_content:
        main_content = soup.find('body')

    if not main_content:
        return ""

    # Extract title
    title = ""
    title_elem = soup.find('title')
    if title_elem:
        title = title_elem.get_text(strip=True)
        # Clean up title
        title = re.sub(r'\s+', ' ', title)
        title = title.replace(' | Laws of Bangladesh', '').strip()

    # Use html2text for better markdown conversion
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.body_width = 0  # Don't wrap lines
    h.unicode_snob = True

    # Convert main content to markdown
    markdown_text = h.handle(str(main_content))

    # Clean up the markdown
    # Remove excessive newlines
    markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)

    # Remove navigation elements
    lines = markdown_text.split('\n')
    cleaned_lines = []
    skip_patterns = [
        r'^\s*\*\s*Home\s*$',
        r'^\s*\*\s*About\s*$',
        r'^\s*\*\s*Contact\s*$',
        r'^\s*Search\s*$',
        r'^\s*Menu\s*$',
        r'^\s*Navigation\s*$',
        r'^\s*Footer\s*$'
    ]

    for line in lines:
        # Skip navigation and menu items
        if any(re.match(pattern, line, re.IGNORECASE) for pattern in skip_patterns):
            continue
        # Skip lines that are just symbols or very short
        if line.strip() and len(line.strip()) > 2:
            cleaned_lines.append(line)

    markdown_text = '\n'.join(cleaned_lines)

    # Add title as H1 if found
    if title:
        markdown_text = f"# {title}\n\n{markdown_text}"

    return markdown_text.strip()


def convert_html_to_markdown(html_file_path: Path, output_path: Path = None):
    """Convert a single HTML file to markdown"""

    print(f"Processing: {html_file_path.name}")

    # Read HTML file
    if html_file_path.suffix == '.gz':
        with gzip.open(html_file_path, 'rt', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
    else:
        with open(html_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()

    # Extract clean text
    markdown_content = extract_clean_text_from_html(html_content)

    if not markdown_content:
        print(f"  WARNING: No content extracted from {html_file_path.name}")
        return False

    # Determine output path
    if output_path is None:
        # Save alongside the HTML file with .clean.md.gz extension
        output_path = html_file_path.parent / html_file_path.name.replace('.html.gz', '.clean.md.gz')

    # Save clean markdown
    if output_path.suffix == '.gz':
        with gzip.open(output_path, 'wt', encoding='utf-8') as f:
            f.write(markdown_content)
    else:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

    # Show preview
    preview = markdown_content[:500] if len(markdown_content) > 500 else markdown_content
    # Clean preview for display
    preview_clean = preview[:200].encode('ascii', 'ignore').decode('ascii')
    print(f"  [OK] Converted successfully")
    print(f"  Preview: {preview_clean}...")
    print(f"  Total length: {len(markdown_content)} characters")
    print(f"  Saved to: {output_path.name}")

    return True


def test_conversion():
    """Test conversion with 2 sample files"""

    data_dir = Path("../../data/raw/acts")

    # Test with act_2 and act_100 (both have HTML content)
    test_files = [
        data_dir / "act_2.html.gz",
        data_dir / "act_100.html.gz"
    ]

    print("=" * 70)
    print("HTML TO MARKDOWN CONVERSION TEST")
    print("=" * 70)

    for html_file in test_files:
        if html_file.exists():
            print(f"\n--- Testing {html_file.name} ---")
            success = convert_html_to_markdown(html_file)

            if success:
                # Also check what was in the original .md.gz file for comparison
                md_file = html_file.parent / html_file.name.replace('.html.gz', '.md.gz')
                if md_file.exists():
                    print(f"\n  Original .md.gz file comparison:")
                    with gzip.open(md_file, 'rt', encoding='utf-8', errors='ignore') as f:
                        original = f.read()

                    if original.startswith('<!DOCTYPE') or original.startswith('<'):
                        print(f"  [OK] Original was HTML (needs replacement)")
                    else:
                        print(f"  [!] Original might be markdown")
                    # Clean original preview for display
                    original_preview = original[:100].encode('ascii', 'ignore').decode('ascii')
                    print(f"  Original preview: {original_preview}...")
        else:
            print(f"  ERROR: {html_file.name} not found")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    # Show the clean files created
    clean_files = list(data_dir.glob("*.clean.md.gz"))
    if clean_files:
        print(f"\nClean markdown files created: {len(clean_files)}")
        for f in clean_files[:5]:
            print(f"  - {f.name}")


if __name__ == "__main__":
    test_conversion()