import asyncio
from typing import Any, List, Optional

import re
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer
from dotenv import load_dotenv
from google import genai
import google.generativeai as embedding_genai
import os
import json
import numpy as np
from app.modules.parse_section import parse_section
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("AI Engine")

SECTIONIZE_MODEL_PATH="app/model_data/paragraph_boundary_minilm"
SUMMARY_MODEL_PATH="app/model_data/gemma-2b-summary-model"
INDEXING_MODEL_PATH="app/model_data/gemma-2b-indexing-model"
EMBEDDING_MODEL_PATH="app/model_data/embedding-model"
CATEGORY_FILE_PATH="app/data/categories_with_vectors.json"

load_dotenv()

CUDA_IS_AVAILABLE = torch.cuda.is_available()

GEMINI_KEY=os.environ.get("GEMINI_API_KEY")

class DocTools:
        
    # 수정되지 않은 섹션 체크 및 변환
    @staticmethod
    def compare_section(before_section: list[dict[int, str]], current_text : str) -> list[Any] :
        """
        :param before_section: 기존 문서의 섹션 (비교할 내용)
        :type before_section: list[dict[int, str]]
        :param current_text: 현재 문서
        :type current_text: str
        :return: 기존 문서에 존재하던 부분은 text_seq 로 대체된 문자열, 정수형 리스트
        :rtype: list[Any]
        """
        targets = sorted(
            before_section,
            key=lambda x : len(x['original_text']),
            reverse=True
        )

        pattern = "|".join(re.escape(t["original_text"]) for t in targets)

        result = []
        last_idx = 0
        updated_section = []

        used_targets = set()   # id 기준 또는 tuple 기준

        for match in re.finditer(pattern, current_text):
            start, end = match.span()

            if start > last_idx:
                result.append(current_text[last_idx:start])

            match_text = match.group()

            for idx, t in enumerate(targets):
                if t["original_text"] == match_text:
                    result.append({
                        "section_seq": t["section_seq"],
                        "text_seq": t["text_seq"]
                    })
                    used_targets.add(idx)
                    break

            last_idx = end

        updated_section = [
            t for idx, t in enumerate(targets)
            if idx not in used_targets
        ]
        
        if last_idx < len(current_text):
            result.append(current_text[last_idx:])
            
        return result, updated_section

    @staticmethod
    def llm_is_updated(original_text: str, current_text: str):
        llm_start = time.perf_counter()
        prompt = f"""
            너는 문서 변경 판단기다.

            [기존 섹션]
            {original_text}

            [현재 텍스트]
            {current_text}

            내용을 비교했을 때, 현재 텍스트가 기존 섹션과의 유사도를
            0.0 ~ 1.0 사이의 실수로 평가해라.
            형식은 달라도 핵심 내용이 같으면 같은 것으로 평가하여라

            핵심 내용이 동일한 경우 0.9 이상을, 내용이 조금 변경되었지만 수정된 내용으로 보이는 경우 0.5 이상을 주어라.
            기존 내용과 전혀 관련이 없는 내용의 경우 0.5 이하의 점수를 주어라.
            단, {{}} 안의 마스킹된 정보는 단 한 자라도 변경된 경우 내용이 수정된 것으로 보아라.

            출력은 숫자 하나만 반환해라.
        """

        client = genai.Client(api_key=GEMINI_KEY)

        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt
        )

        llm_time = time.perf_counter() - llm_start
        logger.info(f"[문서 분할] LLM 호출 완료 | 응답 시간 : {llm_time}")

        return float(response.text.strip())


    @staticmethod
    def compare_section_updated(updated_section: list[dict], current_text) -> dict:
        most_similar_section_seq = 0
        most_similar_text_seq = 0
        most_similar_section_text = ""
        max_similarity = 0.6
        compare_start = time.perf_counter()
        current_vector = DocTools.create_essence_vector(current_text)
        for section in updated_section : 
            section_vector = DocTools.create_essence_vector(section["original_text"])
            cosine_similarity = DocTools.cosine_similarity(np.array(section_vector), np.array(current_vector))
            if cosine_similarity > max_similarity :
                max_similarity = cosine_similarity
                most_similar_section_seq = section["section_seq"]
                most_similar_text_seq = section["text_seq"]
                most_similar_section_text = section["original_text"]

        merge_action_type = "UNKNOWN"

        if most_similar_section_seq != 0 :

            confidence = DocTools.llm_is_updated(most_similar_section_text, current_text)
            if confidence < 0.5 :
                merge_action_type = "UNKNOWN"
                most_similar_section_seq = 0
                most_similar_text_seq = 0
            elif confidence < 0.9 :
                merge_action_type = "MERGE_SECTION"
            else :
                merge_action_type = "LINK_SECTION"
            logger.info(f"[문서 분할] 수정 여부 확인 완료 | 현재 텍스트 : {json.dumps(current_text[:10], ensure_ascii=False)} ... | 대상 텍스트 : {json.dumps(most_similar_section_text[:10], ensure_ascii=False)} ... | 최고 유사도 : {max_similarity} | confidence : {confidence}")
        else:
            logger.info(f"[문서 분할] 수정 여부 확인 완료 | 현재 텍스트 : {json.dumps(current_text[:10], ensure_ascii=False)} ...")
            
        data = {
            "merge_action_type" : merge_action_type,
            "section_seq" : most_similar_section_seq,
            "text_seq" : most_similar_text_seq,
            "original_text" : current_text
        }

        return data

    # 섹션 분할
    @staticmethod
    def split_chunk_by_section(chunk, model):
        result = parse_section(chunk, model)
        
        return result
    
    # 요약 생성
    @staticmethod
    def create_essence(section: str, model, tokenizer, device="cuda") -> str :

        if device == "cuda" :
            prompt = (
                "<start_of_turn>user\n"
                f"다음 내용을 요약해줘: {section}"
                "<end_of_turn>\n"
                "<start_of_turn>model\n"
            )

            inputs = tokenizer(prompt, return_tensors='pt').to(device)
            with torch.no_grad():
                outputs = model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    max_new_tokens=256,
                    temperature=0.3,
                    do_sample=True,
                    repetition_penalty=1.2,
                )

            result = tokenizer.decode(outputs[0], skip_special_tokens = True)
            essence = result.split("model\n")[-1]

        elif device == "cpu" :
            client = genai.Client(api_key=GEMINI_KEY)

            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=f"""
                    다음 문단을 한 문장으로 간단하게 요약해줘.

                    요약할 문단 : 
                    {section}
                """
            )

            essence = response.text

        else :
            raise ValueError("확인할 수 없는 device 타입")

        return essence

    # 색인 생성용 코사인 유사도 계산
    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        vec1 = vec1 / np.linalg.norm(vec1)
        vec2 = vec2 / np.linalg.norm(vec2)
        return float(np.dot(vec1, vec2))
    
    # 색인 생성
    @staticmethod
    def create_index(essence_vector : list[int], category_list=None, model=None, tokenizer=None, device="cuda", input_test_data=False) -> str:

        """
        :param essence_vector: 요약 임베딩된 벡터 (색인을 생성하고자 하는 섹션)
        :type essence_vector: list[int]
        :param category_list: DB에서 받아온 category_list
        :param model: 색인 생성에 사용할 모델 (현재는 None)
        :param tokenizer: 색인 생성에 사용할 토크나이저 (현재는 None)
        :param device: 현재 device
        :param input_test_data: .json 파일로 저장된 카테고리 파일을 사용할지 여부 (True면 사용)
        :return: . 단위로 구분된 계층형 카테고리 문자열
        :rtype: str
        """

        if input_test_data or category_list is None:
            with open(CATEGORY_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            ordered_keys = [
                "level_1_document_content",
                "level_2_document_purpose",
                "level_3_section_role",
                "level_4_section_subject",
                "level_5_section_detail"
            ]

            category_list = [data[key] for key in ordered_keys]


        index_list = []

        for depth in range(5) :
            most_similar_category = ""
            max_simlarity = -1
            for category in category_list[depth] : 
                cosine_similarity = DocTools.cosine_similarity(np.array(category["vector"]), np.array(essence_vector))
                if cosine_similarity > max_simlarity :
                    max_simlarity = cosine_similarity
                    most_similar_category = category
            index_list.append(most_similar_category["category"])

        index = ".".join(index_list)

        return index
    
    # 요약 임베딩 벡터 생성
    @staticmethod
    def create_essence_vector(essence: str, model=None, tokenizer=None, device="cuda", embedding_dim=768) -> List[float]:
        embedding_genai.configure(api_key=GEMINI_KEY)

        result = embedding_genai.embed_content(
            model="models/gemini-embedding-001",
            content=essence,
            task_type="SEMANTIC_SIMILARITY",
            output_dimensionality=768
        )

        essence_vector = result['embedding']

        return essence_vector
    
    @staticmethod
    def merge_consecutive_same_text_seq(origin_sections: list[dict]) -> list[dict]:
        if not origin_sections:
            return []

        merged = []
        prev = origin_sections[0].copy()

        for curr in origin_sections[1:]:
            if not curr["text_seq"] :
                merged.append(prev)
                prev = curr.copy()
                continue
            
            if curr["text_seq"] == prev["text_seq"]:
                prev["original_text"] += curr["original_text"]

                if (
                    prev["merge_action_type"] == "LINK_SECTION"
                    and curr["merge_action_type"] == "LINK_SECTION"
                ):
                    prev["merge_action_type"] = "LINK_SECTION"
                else:
                    prev["merge_action_type"] = "MERGE_SECTION"
            else:
                merged.append(prev)
                prev = curr.copy()

        merged.append(prev)
        return merged


class LLMEngine:
    _instance: Optional["LLMEngine"] = None
    _summary_model = None
    _indexing_model = None
    _tokenizer = None
    _sectionizer = None
    _embedding_model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 처음 실행 시 모델 INPUT
        if CUDA_IS_AVAILABLE :
            if self._summary_model is None:
                logger.info(f"[문서 분할] 요약 모델 로딩 시작")
                
                # app/model_data 에서 파인튜닝된 요약 모델을 import
                self._tokenizer = AutoTokenizer.from_pretrained(SUMMARY_MODEL_PATH)
                self._summary_model = AutoModelForCausalLM.from_pretrained(
                    SUMMARY_MODEL_PATH,
                    device_map="auto",
                    torch_dtype=torch.float16,
                )
                logger.info(f"[문서 분할] 요약 모델 로딩 완료")

        if self._sectionizer is None:
            logger.info(f"[문서 분할] 섹션화 모델 로딩 시작")
            self._sectionizer = SentenceTransformer(SECTIONIZE_MODEL_PATH)
            logger.info(f"[문서 분할] 섹션화 모델 로딩 완료")

    # 요약 모델
    def get_summary_model(self):
        return self._summary_model

    # 색인 생성 모델 (사용하지 않음)
    def get_indexing_model(self):
        return self._indexing_model

    # 토크나이저 (gemma 호환)
    def get_tokenizer(self):
        return self._tokenizer
    
    # 섹션 분할 모델 (학습된 임베딩 모델)
    def get_sectionizer(self):
        return self._tokenizer
    
    # 임베딩 모델 (사용하지 않음)
    def get_embedding_model(self):
        return self._embedding_model
    

    def get_device(self, model=None):
        if model is None :
            return "cuda" if CUDA_IS_AVAILABLE else "cpu"
        elif model == "summary_model":
            return next(self._summary_model.parameters()).device
        elif model == "indexing_model":
            return next(self._indexing_model.parameters()).device
        elif model == "embedding_model":
            return next(self._embedding_model.parameters()).device

    # 문서 분할 로직
    async def split_document(self, before_section: list[dict], text: str) :
        """
        문서를 분할하여 반환
        """
        chunks = []
        sections = []
        updated_section = []

        if before_section:
            chunks, updated_section = DocTools.compare_section(before_section, text)
        else : 
            chunks.append(text)
        
        logger.info(f"[문서 분할] 기존 문서 비교 완료 | 존재 섹션 : {sum(1 for x in chunks if isinstance(x, dict))}")

        for chunk in chunks:
            if isinstance(chunk, dict):
                data = {
                    "merge_action_type" : "SKIP",
                    "section_seq" : chunk["section_seq"],
                    "text_seq" : chunk["text_seq"]
                }
                sections.append(data)
            elif isinstance(chunk, str):
                origin_sections = []
                section = DocTools.split_chunk_by_section(chunk, self._sectionizer)
                for sec in section:
                    origin_section = DocTools.compare_section_updated(updated_section, sec)
                    origin_sections.append(origin_section)
                
                sections.extend(DocTools.merge_consecutive_same_text_seq(origin_sections))
            else:
                raise ValueError("확인되지 않은 section 형태")

        return sections

    # 문서 색인 생성 로직
    async def index_section(self, texts: list[Any], category_list : list = None) -> list[dict[str, Any]]:
        """
        섹션 인덱싱 - 각 텍스트에 대한 메타데이터 및 벡터 준비

        input = split_document를 통해서 분할된 섹션 리스트
        output = [
            {
                "merge_action_type" : "SKIP",
                "section_seq" : original_text.section_seq,
                "text_seq" : original_text.text_seq
            },
            {
                "merge_action_type" : "UNKNOWN",                                                                                                            
                "tag" : "생성된 색인 데이터",
                "essence" : "생성된 요약 데이터",
                "essence_vector" : "생성된 요약 임베딩 데이터",
                "original_text" : "원문 텍스트"
            },
            ...
        ]
        """

        tagged_sections = []

        for text in texts :
            if text["merge_action_type"] in ["SKIP", "LINK_SECTION"] :
                tagged_sections.append(text)
            else :
                essence = DocTools.create_essence(text["original_text"],
                                                model=self.get_summary_model(),
                                                tokenizer=self.get_tokenizer(),
                                                device=self.get_device())
                
                essence_vector = DocTools.create_essence_vector(essence,
                                                model=self.get_embedding_model(),
                                                tokenizer=self.get_tokenizer(),
                                                device="cuda")
                
                tag  = DocTools.create_index(essence_vector,
                                            category_list,
                                            model=self.get_indexing_model(),
                                            tokenizer=self.get_tokenizer(),
                                            device="cuda")
                
                tagged_sections.append({
                    "merge_action_type" : text.get("merge_action_type"),
                    "section_seq" : text.get("section_seq"),
                    "text_seq" : text.get("text_seq"),
                    "tag" : tag,
                    "essence" : essence,
                    "essence_vector" : essence_vector,
                    "original_text" : text["original_text"]
                })
        return tagged_sections

    # 내용 수정 로직
    async def create_edited_text(self, texts: list[dict]) -> str:

        client = genai.Client(api_key=GEMINI_KEY)

        text_list = []

        for text in texts:
            print(f"{text} 작업 시작. {text.get('merge_action_type')}")
            if text.get("merge_action_type") != "MERGE_SECTION" :
                continue
            
            for target in text.get("related_texts") :

                response = client.models.generate_content(
                    model="gemini-2.5-flash", 
                    contents=f"""
                        너는 문서를 수정하는 전문가다.

                        두 개의 핵심 내용이 동일한 문장이 있을 때, 첫번째 문장의 내용이 수정되었다.
                        이를 통해서 두번째 문장의 내용도 수정하고자 한다.
                        다음 규칙을 따라 두번째 문장도 수정하여라.

                        # 규칙

                        문체나 표현 방식, 개행 문자 등은 변경하지 않는다.
                        수정 전·후 예시에서 확인되는 의미상의 변경 사항은 전부 적용하라.
                        연관된 문장이 있다면 같이 수정하여랴.
                        중괄호 사이의 내용은 마스킹 코드로 예시와 동일한 코드가 수정해야할 텍스트에 존재하고, 해당 코드가 직접적으로 수정된 것이 아니면 절대 수정하지 않는다.
                        반드시 해당하는 문장만 하나의 문자열로 출력한다.

                        ## 수정 전 문장 1 :

                        {text['before_text']}

                        ## 수정 후 문장 1 :

                        {text['after_text']}

                        ## 수정 전 문장 2 :

                        {target['original_text']}

                    """
                )

                text_list.append({
                    "text_seq" : target['text_seq'],
                    "section_seq" : text['section_seq'],
                    "original_text" : response.text
                })


        return text_list
