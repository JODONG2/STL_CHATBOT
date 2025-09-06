import argparse
import json
import logging
import os
import re
from typing import Dict, Any, List, Tuple

from bs4 import BeautifulSoup


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def sanitize_filename(name: str, fallback: str) -> str:
    """Create a filesystem-safe filename from a page title."""
    cleaned = re.sub(r'[\\/:*?"<>|\n\r\t]', ' ', name).strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    if not cleaned:
        cleaned = fallback
    return cleaned[:180]


def extract_code_macros(soup: BeautifulSoup) -> None:
    """Replace Confluence code macros with fenced code blocks in-place.

    Confluence represents code blocks as ac:structured-macro with ac:name="code" and body in ac:plain-text-body.
    """
    def is_code_macro(tag):
        return (
            hasattr(tag, 'name')
            and tag.name in ('ac:structured-macro', 'structured-macro')
            and isinstance(tag.attrs, dict)
            and tag.attrs.get('ac:name') == 'code'
        )

    for macro in soup.find_all(is_code_macro):
        language = ''
        title = ''
        # Extract parameters
        for param in macro.find_all('ac:parameter'):
            name = param.attrs.get('ac:name')
            if name == 'language':
                language = (param.get_text() or '').strip()
            elif name == 'title':
                title = (param.get_text() or '').strip()
        # Extract code body
        code_body_el = macro.find('ac:plain-text-body')
        code_text = ''
        if code_body_el is not None:
            code_text = code_body_el.get_text() or ''
        fenced = []
        if title:
            fenced.append(f"[CODE: {title}]")
        fence_lang = language if language else ''
        fenced.append(f"```{fence_lang}")
        fenced.append(code_text.strip('\n'))
        fenced.append("```")
        new_text = "\n".join(fenced)
        macro.replace_with(new_text)


def clean_html_to_text(html: str) -> str:
    """Convert Confluence storage HTML to readable plain text.

    - Converts Confluence code macros to fenced code blocks
    - Strips tags and normalizes whitespace
    """
    if not html:
        return ''
    soup = BeautifulSoup(html, 'html.parser')
    extract_code_macros(soup)
    # Replace <br> with newlines for readability
    for br in soup.find_all('br'):
        br.replace_with('\n')
    text = soup.get_text(separator='\n')
    # Normalize excessive blank lines
    lines = [ln.strip() for ln in text.splitlines()]
    # Remove leading/trailing empties and collapse multiple blanks
    normalized: List[str] = []
    for ln in lines:
        if ln:
            normalized.append(ln)
        else:
            if normalized and normalized[-1] != '':
                normalized.append('')
    return "\n".join(normalized).strip()


def build_breadcrumb(titles: List[str]) -> str:
    return " > ".join([t for t in titles if t])


def extract_pages(data: Dict[str, Any], path_titles: List[str] = None) -> List[Tuple[Dict[str, Any], List[str]]]:
    """Recursively collect pages along with their breadcrumb path titles."""
    if path_titles is None:
        path_titles = []
    pages: List[Tuple[Dict[str, Any], List[str]]] = []
    current_title = data.get('title', '')
    current_path = path_titles + [current_title]
    pages.append((data, current_path))
    for child in data.get('children', []) or []:
        pages.extend(extract_pages(child, current_path))
    return pages


def render_page_text(page: Dict[str, Any], path_titles: List[str]) -> str:
    page_id = str(page.get('id', ''))
    title = page.get('title', '')
    url = page.get('url', '')
    version = page.get('version', {}) or {}
    version_num = version.get('number', '')
    status = page.get('status', '')
    breadcrumb = build_breadcrumb(path_titles)

    # Handle different body structures
    body = page.get('body', '')
    if isinstance(body, str):
        html = body
    elif isinstance(body, dict):
        html = (((body.get('storage') or {}).get('value')) or '')
    else:
        html = ''
    content = clean_html_to_text(html)

    header_lines = [
        f"Title: {title}",
        f"Page ID: {page_id}",
        f"URL: {url}",
        f"Status: {status}",
        f"Version: {version_num}",
        f"Breadcrumb: {breadcrumb}",
        "",
        "-----",
        "",
    ]
    body = content if content else "(본 페이지에는 본문 텍스트가 없습니다.)"
    return "\n".join(header_lines) + body


def write_pages_to_txt(pages: List[Tuple[Dict[str, Any], List[str]]], out_dir: str, min_chars: int) -> List[str]:
    os.makedirs(out_dir, exist_ok=True)

    used_names: Dict[str, int] = {}
    written_files: List[str] = []

    for page, path_titles in pages:
        title = page.get('title', '')
        page_id = str(page.get('id', ''))
        base_name = sanitize_filename(title, fallback=page_id or 'page')
        # Ensure uniqueness
        count = used_names.get(base_name, 0)
        used_names[base_name] = count + 1
        if count > 0:
            filename = f"{base_name}__{count+1}__{page_id}.txt"
        else:
            filename = f"{base_name}__{page_id}.txt"

        text = render_page_text(page, path_titles)
        if len(text) < min_chars:
            logger.info(f"Skip short page: {title} ({page_id}) chars={len(text)}")
            continue

        file_path = os.path.join(out_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        written_files.append(file_path)
        logger.info(f"Wrote: {file_path}")

    return written_files


def write_combined_file(file_paths: List[str], combined_path: str) -> None:
    if not file_paths:
        logger.warning("No files to combine.")
        return
    with open(combined_path, 'w', encoding='utf-8') as out:
        for idx, fp in enumerate(file_paths, start=1):
            out.write(f"\n\n===== DOCUMENT {idx}: {os.path.basename(fp)} =====\n\n")
            with open(fp, 'r', encoding='utf-8') as src:
                out.write(src.read())
    logger.info(f"Combined file written: {combined_path}")


def fix_json_syntax(content: str) -> str:
    """Fix common JSON syntax issues in Confluence data."""
    import re
    
    # 1. Remove non-breaking spaces
    content = content.replace('\u00a0', ' ')
    
    # 2. Fix unescaped quotes in JSON strings
    # Pattern: "text" followed by Korean text (not JSON structure)
    patterns = [
        (r'\"시스템 확정\"', r'\\\"시스템 확정\\\"'),
        (r'\"실패\"여도', r'\\\"실패\\\"여도'),
        (r'\"실패\"여도 대표혜택', r'\\\"실패\\\"여도 대표혜택'),
        (r'\"실패\"여도 대표혜택\+0원추가혜택은 결제가 된 것으로 봐야함', r'\\\"실패\\\"여도 대표혜택+0원추가혜택은 결제가 된 것으로 봐야함'),
        (r'\"시스템 확정\" 으로 시작', r'\\\"시스템 확정\\\" 으로 시작'),
        (r'\"시스템 확정\" 으로', r'\\\"시스템 확정\\\" 으로'),
        (r'\"시스템 확정\"으로', r'\\\"시스템 확정\\\"으로'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content


def convert_json_to_txt(input_json: str, out_dir: str, combined_out: str = None, min_chars: int = 200) -> None:
    if not os.path.exists(input_json):
        raise FileNotFoundError(f"Input JSON not found: {input_json}")
    
    # Read and fix JSON content
    with open(input_json, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix JSON syntax issues
    content = fix_json_syntax(content)
    
    # Try to parse JSON
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        logger.error(f"Error at line {e.lineno}, column {e.colno}")
        raise

    pages = extract_pages(data)
    logger.info(f"Total pages (including root): {len(pages)}")

    written = write_pages_to_txt(pages, out_dir, min_chars=min_chars)
    logger.info(f"Written files: {len(written)}")

    if combined_out:
        write_combined_file(written, combined_out)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert Confluence JSON to plain text files for embedding.")
    parser.add_argument('--input', '-i', default='stl_docs/confluence_data.json', help='Path to Confluence JSON file')
    parser.add_argument('--out-dir', '-o', default='stl_docs/txt', help='Directory to write page text files')
    parser.add_argument('--combined-out', '-c', default='stl_docs/combined_confluence.txt', help='Optional combined output file path')
    parser.add_argument('--min-chars', type=int, default=200, help='Minimum characters to keep a page')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    print(args)
    convert_json_to_txt(args.input, args.out_dir, args.combined_out, min_chars=args.min_chars) 