import json
from modules.data_parsing import parsing_md_sentence
from modules.data_labeling import labeling_md_sentence, labeling_md_sentence_with_boundary
from modules.data_categorize import build_sections, build_context, build_index_prompt, build_user_prompt, generate_index, update_category_from_prompt
import time
from dotenv import load_dotenv

load_dotenv()

def create_embedding_dataset(data: str, output_path):
    parsed_data = parsing_md_sentence(data)
    labeled_data = labeling_md_sentence(parsed_data, window=5)

    with open(output_path, "w", encoding="utf-8") as f:
        for i in range(len(labeled_data) - 1):
            original_label = int(labeled_data[i]["label"])
            inverted_label = 1 - original_label  # 핵심

            record = {
                "text_a": labeled_data[i]["text"],
                "text_b": labeled_data[i + 1]["text"],
                "label": inverted_label
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

def create_category_dataset(data: str, output_path, category, model="gpt-4o-mini", section_boudary=False, masking_path=None) :
    parsed_data = parsing_md_sentence(data, masking_path)
    if section_boudary is True:
        labeled_data = labeling_md_sentence_with_boundary(parsed_data)
    else:
        labeled_data = labeling_md_sentence(parsed_data, window=3)
    sections = build_sections(labeled_data)

    results = []

    updated_category = category

    for i, item in enumerate(sections):
        # 프롬프트용 맥락
        context_text = build_context(sections, i)

        # 색인 생성
        system_prompt = build_index_prompt(context_text)
        user_prompt = build_user_prompt(category, item)
        index = generate_index(system_prompt, user_prompt, model_name=model)
        time.sleep(0.5)

        final_index, category = update_category_from_prompt(index, category)
        print(item["header_path"])
        print(final_index)
        

        results.append({
            "text": item["text"],
            "index": final_index,
            "header_path": item["header_path"]
        })
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return updated_category