import json
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

MODEL_NAME = "gpt-4o-mini"

load_dotenv()
client = OpenAI()

SYSTEM_PROMPT = """
    You are a markdown boundary labeler.

    You are given markdown elements surrounding a target element.
    Your task is to decide whether a logical chunk boundary should occur
    AFTER the element at position pos = 0.

    Your goal is to create SEMANTICALLY COHERENT, HIGH-LEVEL chunks.
    Prefer fewer, larger chunks over overly fine-grained splits.

    Guidelines (priority order):

    1. Headers indicate the start of a new logical chunk.
    - A boundary BEFORE a header is usually correct.
    - Do NOT automatically create a boundary immediately after a header.

    2. Lists (bullet points or numbered items):
    - Treat a contiguous list as a SINGLE logical chunk by default.
    - Do NOT create boundaries between individual list items.
    - Only create a boundary after a list if the following content
        clearly introduces a new topic.

    3. Repeated or similar structures:
    - Similar formatting alone is NOT sufficient to create boundaries.
    - Split only when the semantic topic clearly changes.

    4. Paragraphs:
    - Multiple consecutive newlines MAY indicate a boundary
        only if there is a clear topic shift.
    - A single newline almost never indicates a boundary.

    5. Code blocks and tables:
    - NEVER create boundaries inside code blocks or tables.

    6. Default behavior:
    - When uncertain, choose NOT to create a boundary.

    Output rules (STRICT):
    - Output MUST be valid JSON.
    - Output MUST contain ONLY the following object.
    - Do NOT include explanations, comments, markdown, or extra text.
    - Do NOT wrap the JSON in code fences.

    Required output format:
    {
    "break": 0 or 1
    }

"""

"""
    data : data-parsing.py 에서 가져온 전체 데이터
    index : 현재 라벨링할 인덱스
    window : 확인해야할 주변 맥락 수
    max_text_len : 최대 텍스트 길이
"""
def build_context(
    data: List[Dict[str, Any]],
    index: int,
    window: int = 2,
    max_text_len: int = 240,
) -> List[Dict[str, Any]]:

    context = []

    for offset in range(-window, window + 1):
        i = index + offset
        if 0 <= i < len(data):
            text = data[i]["text"]
            if text is not None and len(text) > max_text_len:
                text = text[:max_text_len] + "…"

            context.append({
                "pos": offset,
                "type": data[i]["type"],
                "text": text
            })
        else:
            context.append({
                "pos": offset,
                "type": None,
                "text": None
            })

    return context

"""
    LLM 호출 전 처리 (호출 비용 절약)
    data : 현재 처리할 인덱스
"""
def heuristic_label(
    data: List[Dict[str, Any]], 
    index: int
) -> int | None:

    curr = data[index]
    curr_type = curr["type"]

    if index + 1 < len(data) and data[index + 1]["type"] in ("newline", "html_br","other"):
        return 0

    

    return None

def predict_boundary_with_llm(context: List[Dict[str, Any]]) -> int:
    user_payload = {
        "context": context,
        "target_pos": 0
    }

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
        ],
        temperature=0
    )

    content = response.choices[0].message.content
    result = json.loads(content)

    return int(result["break"])

def labeling_md_sentence(
    data: List[Dict[str, Any]],
    window: int = 2
) -> List[Dict[str, Any]]:

    for i in range(len(data)):
        heuristic = heuristic_label(data, i)
        if heuristic is not None:
            data[i]["label"] = heuristic
            curr = data[i]

            print(f"[{i}] LLM | type={curr['type']} | label={heuristic}")
            print(repr(curr["text"]))
            print("-" * 60)
            continue

        context = build_context(data, i, window=window)

        label = predict_boundary_with_llm(context)
        data[i]["label"] = label

        curr = data[i]

        print(f"[{i}] LLM | type={curr['type']} | label={label}")
        print(repr(curr["text"]))
        print("-" * 60)

    return data

SECTION_MARKER = "<-SectionBoundary->"

def labeling_md_sentence_with_boundary(
    data: List[Dict[str, Any]],
    window: int = 2
) -> List[Dict[str, Any]]:

    i = 0
    while i < len(data):
        curr = data[i]
        text = curr["text"]

        # 🔥 section boundary 처리
        if curr.get("type") == "section_boundary" or SECTION_MARKER in text:

            # 1️⃣ 이전 문장이 존재하면 label=1
            if i > 0:
                data[i - 1]["label"] = 1

            # 2️⃣ boundary 문장 제거
            print(f"[{i}] RULE | section boundary → remove")
            print(repr(text))
            print("-" * 60)

            data.pop(i)
            # pop 했으므로 i 증가 ❌
            continue

        # 일반 문장
        curr["label"] = 0
        print(f"[{i}] RULE | type={curr.get('type')} | label=0")
        print(repr(text))
        print("-" * 60)

        i += 1

    return data


def save_labeling_data(labeling_file_path, file_num, data) :
    with open(f"{labeling_file_path}/labeled_data_{file_num}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

