import re
import json
from pathlib import Path
from typing import List, Dict

import re
from typing import Tuple, Dict

import re
import json
from typing import Dict, Tuple, Optional


def mask_links(
    text: str,
    url_registry: Dict[str, Dict],
    start_idx: int,
    save_json_path: Optional[str] = None
) -> Tuple[str, Dict[str, Dict], int]:

    link_map = {}
    counter = start_idx

    def get_placeholder(url: str, link_type: str) -> str:
        nonlocal counter

        if url in url_registry:
            url_registry[url]["types"].add(link_type)
            return url_registry[url]["placeholder"]

        placeholder = f"{{url_{counter:03d}}}"
        url_registry[url] = {
            "placeholder": placeholder,
            "types": {link_type}
        }
        counter += 1
        return placeholder

    def record_link(placeholder, url, label, link_type):
        link_map[placeholder] = {
            "url": url,
            "text": label,
            "type": link_type
        }

    # Markdown 이미지 ![alt](url)
    text = re.sub(
        r'!\[([^\]]*)\]\((https?://[^\)]+)\)',
        lambda m: (
            (ph := get_placeholder(m.group(2), "markdown_image")) or
            record_link(ph, m.group(2), m.group(1), "markdown_image") or
            ph
        ),
        text
    )

    # HTML 이미지 <img src="...">
    text = re.sub(
        r'<img\s+[^>]*src=["\'](https?://[^"\']+)["\'][^>]*>',
        lambda m: (
            (ph := get_placeholder(m.group(1), "html_image")) or
            record_link(ph, m.group(1), "", "html_image") or
            ph
        ),
        text,
        flags=re.IGNORECASE
    )

    # Markdown 링크 [text](url)
    text = re.sub(
        r'\[([^\]]+)\]\((https?://[^\)]+)\)',
        lambda m: (
            (ph := get_placeholder(m.group(2), "markdown_link")) or
            record_link(ph, m.group(2), m.group(1), "markdown_link") or
            ph
        ),
        text
    )

    # HTML 링크 <a href="...">text</a> 또는 <a href="...">text (</a> 없음)
    text = re.sub(
        r'<a\s+[^>]*href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)(?:</a>)?',
        lambda m: (
            (ph := get_placeholder(m.group(1), "html_link")) or
            record_link(ph, m.group(1), m.group(2).strip() if m.group(2) else "", "html_link") or
            ph
        ),
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    # -----------------------------
    # JSON 저장
    # -----------------------------
    if save_json_path:
        json_ready = {
            info["placeholder"].strip("{}"): {
                "url": url,
                "types": sorted(list(info["types"]))
            }
            for url, info in url_registry.items()
        }

        with open(save_json_path, "w", encoding="utf-8") as f:
            json.dump(json_ready, f, ensure_ascii=False, indent=2)

    return text, link_map, counter

MERGE_TARGET_TYPES = {
    "list_item",
    "html_br",
    "newline",
    "section_boundary"
}

FLUSH_TRIGGER_TYPES = {
    "sentence",
    "code_block",
    "header"
}

import re
from typing import List, Dict

def parsing_md_sentence(md: str, masking_path=None) -> List[Dict]:
    patterns = [
        ('code_block', r'\n```[\s\S]*?```'),
        ('header', r'^(#{1,6}\s[^\n]*|<h[1-6][^>]*>.*?</h[1-6]>)'),
        ('section_boundary', r'<-SectionBoundary->'),
        ('list_item', r'^[ \t]*([-*+]|\d+\.)\s[^\n]*'),
        ('html_br', r'<br\s*/?>'),
        ('newline', r'\n'),
        ('sentence', r'[^ \n].*?(?:[.!?]|다\.)(?=\s|$)')
    ]

    master_regex = re.compile(
        '|'.join(f'(?P<{name}>{pattern})' for name, pattern in patterns),
        re.MULTILINE
    )

    chunks = []
    buffer_text = []
    buffer_links = []

    url_registry = {}
    url_counter = 1
    last_idx = 0


    def flush_buffer():
        if not buffer_text:
            return
        
        meaningful_text = [x for x in buffer_text if x != '\n']
        
        if len("".join(meaningful_text)) <= 10 :
            return

        chunks.append({
            "label": 0,
            "type": "merged_block",
            "text": "".join(buffer_text),
            "metadata": {
                "category": "structural_element",
                "links": buffer_links.copy()
            }
        })
        buffer_text.clear()
        buffer_links.clear()

    for match in master_regex.finditer(md):
        start, end = match.span()

        # 패턴 사이 일반 텍스트
        if start > last_idx:
            raw = md[last_idx:start]
            masked, links, url_counter = mask_links(
                raw, url_registry, url_counter, masking_path
            )
            buffer_text.append(masked)
            buffer_links.extend(links)

        group = match.lastgroup
        raw = match.group(group)

        masked, links, url_counter = mask_links(
            raw, url_registry, url_counter, masking_path
        )

        # 🔹 1. 병합 대상이거나 짧은 텍스트
        if len(masked) <= 10:
            buffer_text.append(masked)
            buffer_links.extend(links)

        # 🔹 2. flush 트리거 + 충분히 긴 텍스트
        elif len(masked) >= 10:
            flush_buffer()

            metadata = {
                "category": "structural_element",
                "links": links
            }

            if group == "code_block":
                lang_match = re.match(r'```(\w+)', raw)
                metadata["category"] = "code"
                metadata["language"] = (
                    lang_match.group(1) if lang_match else "text"
                )

            chunks.append({
                "label": 0,
                "type": group,
                "text": masked,
                "metadata": metadata
            })

        last_idx = end

    # 남은 텍스트 처리
    if last_idx < len(md):
        raw = md[last_idx:]
        masked, links, _ = mask_links(
            raw, url_registry, url_counter, masking_path
        )
        buffer_text.append(masked)
        buffer_links.extend(links)

    # 마지막 buffer flush
    flush_buffer()

    return chunks

