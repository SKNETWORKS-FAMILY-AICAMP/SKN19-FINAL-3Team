import asyncio
from typing import Any, List, Optional

import torch
from llama_index.core import Document
from llama_index.core.node_parser import MarkdownNodeParser
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer


class LLMEngine:
    _instance: Optional["LLMEngine"] = None
    _model = None
    _tokenizer = None
    _embedding_model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            print("Gemma2 2B 모델 로딩 중")
            self._tokenizer = AutoTokenizer.from_pretrained("google/gemma-2-2b")
            self._model = AutoModelForCausalLM.from_pretrained(
                "google/gemma-2-2b",
                device_map="auto",
                torch_dtype=torch.float16,
                load_in_8bit=True,
                attn_implementation="eager",
            )
            print("Gemma2 2B 로드 완료")

        if self._embedding_model is None:
            print("임베딩 모델 로딩 중")
            self._embedding_model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2"
            )
            print("임베딩 모델 로드 완료")

    @staticmethod
    def chunk_markdown_with_llamaindex(markdown_text: str) -> list[dict[str, Any]]:
        doc = Document(text=markdown_text)
        parser = MarkdownNodeParser()
        nodes = parser.get_nodes_from_documents([doc])

        chunks = []
        for i, node in enumerate(nodes):
            chunks.append(
                {
                    "chunk_id": i,
                    "content": node.get_content(),
                    "metadata": node.metadata,
                }
            )

        return chunks

    async def split_document(self, text: str) -> list[dict[str, Any]]:
        """
        문서를 마크다운 단위로 분할하여 반환합니다.

        반환 예시:
            [
                {"seq": 0, "text": "# 문서 제목\n첫 번째 문단 내용..."},
                {"seq": 1, "text": "## 부제목\n두 번째 문단 내용..."},
                ...
            ]
        """
        chunks = type(self).chunk_markdown_with_llamaindex(text)
        texts = [
            {
                "seq": chunk.get("chunk_id"),
                "text":chunk.get("content")
            } for chunk in chunks if chunk.get("content")
        ]
        return texts

    async def index_section(self, texts: list[str]) -> list[dict[str, Any]]:
        """
        섹션 인덱싱 - 각 텍스트에 대한 메타데이터 및 벡터 준비

        input = md:str
        output =  [{"index" : str ( ex. 기술문서.개요.기술스택) , "essence" : str, "original_text" : str}, {...} , ... ]

        """
        indexed_sections = []
        for text in texts:
            # llm 프롬프트로 데이터 생성
            indexed_sections.append(
                {
                    "seq": text.get("seq"),
                    "index": "테스트.인텍스.확인용",
                    "essence": "내용 요약이 들어있습니다",
                    "original_text": text.get("text"),
                    "reasoning": "테스트 사유 입니다."
                }
            )

        return indexed_sections

    async def merge_proposals(self, texts: list[str]) -> str:
        """
        제안 병합 - 여러 텍스트를 하나로 통합
        """
        await asyncio.sleep(0.5)

        if not texts:
            return ""

        # 각 제안에 구분자 추가하여 병합
        merged = "\n\n---\n\n".join(
            f"[제안 {i + 1}]\n{text}" for i, text in enumerate(texts) if text.strip()
        )

        return merged

    async def generate_document(
        self, text: str, max_tokens: int = 512
    ) -> dict[str, Any]:
        """
        문서 생성 - Gemma2 2B를 사용한 실제 LLM 추론
        """
        prompt = f"""Convert the following text to JSON format.
**IMPORTANT**: Output ONLY valid JSON, no explanations.

Text: {text}

JSON Output:"""

        # 토큰화
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)

        # 비동기 처리를 위해 별도 스레드에서 실행
        loop = asyncio.get_event_loop()

        def _generate():
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=0.1,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self._tokenizer.eos_token_id,
                )
            return self._tokenizer.decode(outputs[0], skip_special_tokens=True)

        # CPU-bound 작업을 별도 스레드에서 실행
        full_output = await loop.run_in_executor(None, _generate)
        generated_text = full_output.replace(prompt, "").strip()

        return {
            "title": "Generated Document",
            "content": generated_text,
            "summary": generated_text[:200] + "..."
            if len(generated_text) > 200
            else generated_text,
            "metadata": {
                "source_length": len(text),
                "model": "google/gemma-2-2b",
                "generated_at": asyncio.get_event_loop().time(),
            },
        }

    async def embed_text(self, text: str) -> List[float]:
        """
        텍스트를 벡터로 임베딩

        Args:
            text: 임베딩할 텍스트

        Returns:
            1536차원 벡터 (OpenAI text-embedding-3-small 호환)
        """
        loop = asyncio.get_event_loop()

        def _embed():
            # sentence-transformers로 임베딩 생성 (384차원)
            embedding = self._embedding_model.encode(text, convert_to_numpy=True)

            # 1536차원으로 패딩 (zero-padding)
            # 실제 운영 시에는 1536차원 모델 사용 또는 DB 스키마 조정 필요
            import numpy as np

            padded = np.zeros(1536)
            padded[: len(embedding)] = embedding

            return padded.tolist()

        # CPU-bound 작업을 별도 스레드에서 실행
        vector = await loop.run_in_executor(None, _embed)
        return vector
