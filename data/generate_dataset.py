from pathlib import Path
import openai
import json
from dotenv import load_dotenv
from pathlib import Path
from modules.data_parsing import mask_links
from modules.data_parsing import parsing_md_sentence
from modules.data_categorize import update_category_from_prompt

load_dotenv()

output_path = Path("docs_data/category_list.json")

with output_path.open("r", encoding="utf-8") as f:
    category_list = json.load(f)

print("category list : ", category_list)

folder_path = Path("docs_data/before_raw_file/")

file_names = [f.stem for f in folder_path.glob("*.md")]

def convert_to_jsonl(doc):
    user_prompt = f"""
        다음 문서를 JSONL 학습용 데이터로 변환해주세요. 
        문서 내용은 아래와 같습니다:

        {doc}

        pgsql
        코드 복사

        출력 규칙은 시스템 프롬프트를 참고하여 그대로 적용합니다.
    """
    
    response = openai.chat.completions.create(
        model="gpt-5.1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
    )
    
    return response.choices[0].message.content

def create_index(file_name, section, category_list) :
    category = ""
    for i, depth_category in enumerate(category_list):
        category += f"\tdepth_{i} : "
        if len(depth_category) < 1 :
            category += "카테고리 생성 필요"
            continue
        for s in depth_category:
            category += (s+", ")
        category += "\n"

    section_summary = section["summary"]
    section_text = section["text"]

    indexing_system_prompt = """ 
        너는 기술 문서 색인 전문가야.

        아래 문서의 맥락을 참고해서
        "현재 섹션" 하나에 대한 색인 하나만 생성해.

        규칙:
        - 점(.)으로 구분된 계층 구조로 반드시 한 줄만 출력
        - 카테고리는 현재 존재하는 카테고리를 먼저 찾고, 내용과 유사한 카테고리가 존재하지 않을 경우 새 카테고리를 생성
        - 각 문서별 최상위 카테고리는 각 문서의 주제
        - 각 depth별 카테고리는 반드시 하나를 선택하거나 생성
        - 같은 이름의 카테고리는 서로 다른 depth에 존재하면 안됨
        - 문맥이 조금 달라도 같은 의미면 항상 같은 색인
        - **다른 문맥은 모두 서로 다른 색인을 가져야 함**
        - 색인만 출력 (설명 금지)

        색인 예시:
        AJC프로젝트기획서.기능소개.문서등록로직.태그(요약)-내용(정리)-형식(형식)계층기반.섹션분할및태그(요약)매핑
    """

    indexing_user_prompt = f"""
        파일 이름 :
            {file_name}
        섹션 요약 :
            {section_summary}

        섹션 내용 :
            {section_text}

        현재 존재하는 카테고리 :
            {category}
    """

    response = openai.chat.completions.create(
        model="gpt-5.1",
        messages=[
            {"role": "system", "content": indexing_system_prompt},
            {"role": "user", "content": indexing_user_prompt}
        ],
        temperature=0.0,
    )

    index, updated_category = update_category_from_prompt(response.choices[0].message.content, category_list)

    return index, updated_category

for FILE_NAME in file_names:
    system_prompt = """
        당신은 JSONL 학습 데이터 생성 전문가입니다.
        역할:
        - 입력 문서를 의미 단위로 섹션화
        - 각 섹션마다 JSON 객체 생성

        규칙:
        1. 출력 JSON 객체의 키:
        - "text": 원본 섹션 내용 그대로
        - "similar_text": 형식과 문장이 유사하지만 약간 다르게 표현된 내용
        - "warning_text": 형식은 유사하지만 문맥이 다른 내용
        - "summary": 섹션 한 줄 요약
        2. 섹션 사이 개행, 들여쓰기, 리스트 등 포맷 유지
        3. 섹션들을 결합하면 원본 문서와 100% 동일
        4. 출력은 JSONL 형식 (한 줄 = 한 섹션)
        5. 모든 문서는 GPT-5.1 모델을 기준으로 처리
    """

    md_path = Path(f"docs_data/before_raw_file/{FILE_NAME}.md")

    with md_path.open("r", encoding="utf-8") as f:
        doc = f.read()

    url_registry = {}

    masking_path = f"docs_data/masking_data/masking_{FILE_NAME}.json"
    masked_text, link_map, next_counter = mask_links(doc, url_registry, start_idx=1, save_json_path=masking_path)

    print(f"{FILE_NAME} masking complete")

    jsonl_text = convert_to_jsonl(masked_text)

    print(f"{FILE_NAME} pasing complete")


    jsonl_lines = jsonl_text.strip().split("\n")

    with open(f"docs_data/test_data/{FILE_NAME}.jsonl", "w", encoding="utf-8") as f:
        for line in jsonl_lines:
            f.write(line + "\n")


    texts = []
    with open(f"docs_data/test_data/{FILE_NAME}.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                obj = json.loads(line)
                texts.append(obj["text"])

    labeled_data = []
    for text in texts:
        chunks = parsing_md_sentence(text)
        if len(chunks) > 0:
            chunks[-1]['label'] = 1
            labeled_data.extend(chunks)
        

    OUTPUT_PATH = f"docs_data/embedding_data/embedding_{FILE_NAME}.jsonl"

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for i in range(len(labeled_data) - 1):
            original_label = int(labeled_data[i]["label"])
            inverted_label = 1 - original_label

            record = {
                "text_a": labeled_data[i]["text"],
                "text_b": labeled_data[i + 1]["text"],
                "label": inverted_label
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"{FILE_NAME} embedding complete")

    sections = []

    with open(f"docs_data/test_data/{FILE_NAME}.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                obj = json.loads(line)
                sections.append(obj)


    OUTPUT_PATH = f"docs_data/embedding_data/vector_similarity_{FILE_NAME}.jsonl"

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for section in sections:
            record = {
                "text_a": section["text"],
                "text_b": section["similar_text"],
                "label": 1
            }

            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            record = {
                "text_a": section["text"],
                "text_b": section["warning_text"],
                "label": 0
            }
            
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"{FILE_NAME} vector similarity complete")
    
    sections = []

    with open(f"docs_data/test_data/{FILE_NAME}.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                obj = json.loads(line)
                sections.append(obj)


    OUTPUT_PATH = f"docs_data/indexing_data/index_data_{FILE_NAME}.jsonl"

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for section in sections:

            index, category_list = create_index(FILE_NAME, section, category_list)

            record = {
                "text" : section["text"],
                "index" : index
            }
            
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"{FILE_NAME} indexing complete")


    output_path = Path("docs_data/category_list.json")

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(category_list, f, ensure_ascii=False, indent=2)
