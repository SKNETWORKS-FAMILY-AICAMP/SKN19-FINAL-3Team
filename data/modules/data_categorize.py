from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, Optional, Tuple
import re

load_dotenv()
client = OpenAI()

def clean_header_text(text: str) -> str:
    # HTML 태그 제거
    text = re.sub(r"<[^>]+>", "", text)

    # Markdown 강조 제거
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"_(.*?)_", r"\1", text)

    return text.strip()

def parse_markdown_header(text: str) -> Optional[Tuple[int, str]]:
    """
    마크다운 헤더(#, ##, ### ...)를 파싱
    반환:
      - (depth, header_text)
      - 헤더가 아니면 None
    """
    text = text.strip()

    md_match = re.match(r"^(#{1,6})\s+(.*)", text)
    if md_match:
        depth = len(md_match.group(1))
        header_text = md_match.group(2)

        header_text = clean_header_text(header_text)
        return depth, header_text
    
    html_match = re.match(
        r"^<h([1-6])[^>]*>(.*?)</h\1>",
        text,
        flags=re.IGNORECASE
    )
    if html_match:
        depth = int(html_match.group(1))
        header_text = html_match.group(2)

        header_text = clean_header_text(header_text)
        return depth, header_text

    return None

def build_sections(data: Dict):
    """
    label=1을 기준으로 섹션 단위 텍스트를 생성
    원문 재조합 가능 (text 그대로 이어붙임)
    """
    sections = []
    buffer = []

    current_headers = {}

    for item in data:
        text = item["text"]
        buffer.append(text)

        # 🔹 헤더 문장 처리
        if item.get("type") == "header":
            parsed = parse_markdown_header(text)
            if parsed:
                depth, header_text = parsed

                # 현재 depth의 헤더 갱신
                current_headers[depth] = header_text

                # 하위 depth 제거 (MarkdownNodeParser와 동일)
                for d in list(current_headers.keys()):
                    if d > depth:
                        del current_headers[d]

        if item.get("label") == 1:
            header_path = "/" + "/".join(
                current_headers[d] for d in sorted(current_headers)
            )

            sections.append({
                "text": "".join(buffer),
                "header_path": header_path
            })

            buffer = []

    if buffer:
        header_path = "/" + "/".join(
            current_headers[d] for d in sorted(current_headers)
        )
        sections.append({
            "text": "".join(buffer),
            "header_path": header_path
        })

    return sections

def build_context(sections, idx, window=5):
    start = max(0, idx - window)
    end = min(len(sections), idx + window + 1)

    parts = []
    for i in range(start, end):
        parts.append(f"{sections[i]['text']}\n")

    return "\n\n".join(parts)

def build_user_prompt(category, sections):
    prompt = "header_path : " + sections["header_path"] + "\n" + "text : " + sections["text"] + "\n"
    str = "categories: \n"
    for i, depth_category in enumerate(category):
        str += f"\tdepth_{i} : "
        for s in depth_category:
            str += (s+", ")
        str += "\n"

    prompt += str
    return prompt

def build_index_prompt(context_text):
    return f"""
너는 기술 문서 색인 전문가야.

아래 문서의 맥락을 참고해서
"현재 섹션" 하나에 대한 색인 하나만 생성해.

규칙:
- 점(.)으로 구분된 계층 구조로 반드시 한 줄만 출력
- 카테고리는 현재 존재하는 카테고리를 최우선으로 찾고, 존재하지 않을 경우 새 카테고리를 생성
- **비슷한 이름의 카테고리는 반드시 하나로 통합**
- 각 depth별 카테고리는 반드시 하나를 선택하거나 생성되어야 함
- 문맥이 조금 달라도 같은 의미면 항상 같은 색인
- 색인만 출력 (설명 금지)

색인 예시:


문서 맥락:
----------------
{context_text}
----------------
"""

def generate_index(system_prompt: str, user_prompt: dict, model_name) -> str:
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0
    )

    return response.choices[0].message.content.strip()

def update_category_from_prompt(
    prompt: str,
    category: list
):
    lines = prompt.splitlines()
    return_prompt = prompt.replace("_", "").replace(" ", "")

    for line in lines:
        if not line.strip():
            continue

        parts = line.split(".")

        for depth, raw in enumerate(parts):
            # "_" 와 공백 제거
            cleaned = raw.replace("_", "").replace(" ", "").strip()

            if not cleaned:
                continue

            # category 깊이가 부족하면 자동 확장
            while depth >= len(category):
                category.append([])

            if cleaned not in category[depth]:
                category[depth].append(cleaned)

    return return_prompt, category

