import re
from typing import List, Dict
from sentence_transformers import util

from typing import List
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("AI Parser")

def parse_markdown_sentences(text: str) -> List[str]:
    sentences = []
    buf = []
    i = 0
    n = len(text)

    in_code_block = False
    code_fence = None  # ``` or ~~~

    def flush():
        if buf:
            sentences.append("".join(buf))
            buf.clear()

    while i < n:
        # CODE BLOCK DETECTION
        if text.startswith(("```", "~~~"), i):
            fence = text[i:i+3]

            if not in_code_block:
                flush()
                in_code_block = True
                code_fence = fence
            elif fence == code_fence:
                in_code_block = False
                code_fence = None

            buf.append(fence)
            i += 3
            continue

        ch = text[i]

        # CODE BLOCK MODE
        if in_code_block:
            buf.append(ch)
            i += 1
            continue

        # NEWLINE = HARD SENTENCE BOUNDARY
        if ch == "\n":
            # 연속 개행 전부 흡수
            while i < n and text[i] == "\n":
                buf.append(text[i])
                i += 1

            # 마지막 개행 뒤에서 문장 분리
            flush()
            continue

        # NORMAL CHARACTER
        buf.append(ch)

        # SENTENCE TERMINATION (.?!)
        if ch in ".?!":
            prev = text[i - 1] if i > 0 else ""
            j = i + 1

            # 1. 다음이 공백 1칸 이상
            if j < n and text[j] == " ":
                # 2. 바로 앞 문자가 숫자가 아닐 때만
                if not prev.isdigit():
                    flush()
                    i += 1
                    continue

        i += 1

    flush()
    return sentences

def header_level(text: str) -> int:
    stripped = text.lstrip()
    if not stripped.startswith("#"):
        return 0

    level = 0
    for ch in stripped:
        if ch == "#":
            level += 1
        else:
            break
    return level

def is_single_line_paragraph(text: str) -> bool:
    """
    문단 내부에 개행이 없고,
    개행이 있다면 맨 끝에만 있는 경우 True
    """
    stripped = text.rstrip("\n")
    return "\n" not in stripped

def leading_spaces(s: str) -> int:
    return len(s) - len(s.lstrip(" "))

def is_single_line_with_one_newline(s: str) -> bool:
    return (
        s.count("\n") == 1
        and s.endswith("\n")
        and "\n" not in s[:-1]
    )

def is_boundary(model, sent1: str, sent2: str, threshold=0.7):
    """
    return:
        boundary (1: 문단 분리, 0: 같은 문단)
        similarity
    """

    if sent2.lstrip().startswith("#"):
        return 1, None

    if sent2.lstrip().startswith("-"):
        return 1, None

    if not re.search(r"[A-Za-z0-9가-힣]", sent2):
        return 0, None

    emb1 = model.encode(sent1, convert_to_tensor=True)
    emb2 = model.encode(sent2, convert_to_tensor=True)

    similarity = util.cos_sim(emb1, emb2).item()
    boundary = 1 if similarity < threshold else 0
    if similarity > threshold :
        logger.info(f"유사도 기반 병합 | Sent1 : {sent1[:10]} ... | Sent2 : {sent2[:10]} ... | Similarity : {similarity}")

    return boundary, similarity

def postprocess_paragraphs(
    paragraphs: List[str],
    short_len: int = 15,
) -> List[str]:
    """
    paragraphs에 대해 후처리를 수행한다.

    규칙 (순서대로 적용):
    1. 리스트(-) 문단 연속 병합
    2. 헤더(#) 문단은 아래 문단과 병합
    3. 짧은 문단(short_len 이하)은 앞 문단과 병합
       - 첫 문단이면 뒤 문단과 병합
    """


    # 1. 리스트 문단 병합
    merged: List[str] = []
    i = 0

    while i < len(paragraphs):
        curr = paragraphs[i]
        curr_strip = curr.lstrip()

        if curr_strip.startswith("-"):
            combined = curr
            curr_indent = leading_spaces(curr)
            j = i + 1

            # 연속 리스트 병합 (들여쓰기 >= 현재 문단만)
            while (
                j < len(paragraphs)
                and paragraphs[j].lstrip().startswith("-")
                and leading_spaces(paragraphs[j]) >= curr_indent
            ):
                logger.info(f"리스트 병합 | Sent1 : {json.dumps(combined[:10], ensure_ascii=False)} ... | Sent2 : {json.dumps(paragraphs[j][:10], ensure_ascii=False)} ...")
                combined += paragraphs[j]
                j += 1

            # 하위 설명 문단 병합
            if j < len(paragraphs):
                next_para = paragraphs[j]

                if (
                    is_single_line_with_one_newline(curr)
                    and leading_spaces(next_para) > curr_indent
                ):
                    logger.info(f"리스트 병합 | Sent1 : {json.dumps(combined[:10], ensure_ascii=False)} ... | Sent2 : {json.dumps(next_para[:10], ensure_ascii=False)} ...")
                    combined += next_para
                    j += 1

            merged.append(combined)
            i = j
        else:
            merged.append(curr)
            i += 1

    paragraphs = merged

    # 2. 헤더 문단 병합
    merged: List[str] = []
    i = 0

    while i < len(paragraphs):
        curr = paragraphs[i]
        curr_level = header_level(curr)

        if (
            curr_level > 1
            and is_single_line_paragraph(curr)
            and i + 1 < len(paragraphs)
        ):
            next_para = paragraphs[i + 1]
            next_level = header_level(next_para)

            # case 1: 다음이 본문
            if next_level == 0:
                logger.info(f"헤더 병합 | Sent1 : {json.dumps(curr[:10], ensure_ascii=False)} ... | Sent2 : {json.dumps(next_para[:10], ensure_ascii=False)} ...")
                merged.append(curr + next_para)
                i += 2
                continue

            # case 2: 다음이 헤더 + 더 하위 레벨
            if next_level > curr_level:
                logger.info(f"헤더 병합 | Sent1 : {json.dumps(curr[:10], ensure_ascii=False)} ... | Sent2 : {json.dumps(next_para[:10], ensure_ascii=False)} ...")
                merged.append(curr + next_para)
                i += 2
                continue

            # next_level <= curr_level → 병합 안 함

        merged.append(curr)
        i += 1

    paragraphs = merged

    # 3. 짧은 문단 병합
    merged = []

    i = 0
    while i < len(paragraphs):
        curr = paragraphs[i]

        if len(curr) <= short_len:
            if merged:
                logger.info(f"길이 병합 | Sent1 : {json.dumps(merged[-1][:10], ensure_ascii=False)} ... | Sent2 : {json.dumps(curr[:10], ensure_ascii=False)} ...")
                merged[-1] += curr
                i += 1
            elif i + 1 < len(paragraphs):
                # 첫 문단 → 뒤 문단과 병합
                logger.info(f"길이 병합 | Sent1 : {json.dumps(curr[:10], ensure_ascii=False)} ... | Sent2 : {json.dumps(paragraphs[i+1][:10], ensure_ascii=False)} ...")
                merged.append(curr + paragraphs[i + 1])
                i += 2
            else:
                merged.append(curr)
                i += 1
        else:
            merged.append(curr)
            i += 1

    return merged

def parse_section(
    text: str,
    model,
    threshold: float = 0.6,
) -> List[str]:
    """
    Markdown 문서를 문장 단위로 파싱한 뒤,
    의미 유사도(is_boundary)만으로 문단 단위 병합을 수행한다.

    return:
        문단 단위 문자열 리스트 (lossless)
    """

    sentences = parse_markdown_sentences(text)
    if not sentences:
        return []

    paragraphs: List[str] = []
    current_para = sentences[0]

    for i in range(1, len(sentences)):
        boundary, similarity = is_boundary(
            model,
            current_para.strip(),
            sentences[i].strip(),
            threshold=threshold,
        )

        if boundary == 0:
            # 같은 문단
            current_para += sentences[i]
        else:
            # 문단 분리
            paragraphs.append(current_para)
            current_para = sentences[i]

    paragraphs.append(current_para)

    paragraphs = postprocess_paragraphs(paragraphs)

    return paragraphs