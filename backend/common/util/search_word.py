import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from common.repositories.section_repo import SectionRepository
from common.repositories.mixed_repo import MixedRepository
from common.repositories.tag_repo import TagRepository
from common.repositories.doc_recipes_repo import DocRecipesRepository
from common.repositories.section_recipes_repo import SectionRecipesRepository
from common.repositories.original_texts_repo import OriginalTextsRepository

from common.util.AI_API import GeminiApi

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("Search Engine")


class DocSearch () :
    def __init__(self, db) :
        self.db = db
        self.section_repo = SectionRepository(db)
        self.mixed_repo = MixedRepository(db)
        self.tag_repo = TagRepository(db)
        self.recipe_repo = DocRecipesRepository(db)
        self.section_recipes_repo = SectionRecipesRepository(db)
        self.original_texts_repo = OriginalTextsRepository(db)
        self.gemini_api = GeminiApi()

    async def _create_search_vector(self, search_word: str) -> list[int] :
        vector = await self.gemini_api.create_sentence_vector(search_word)
        return vector
        
    # 검색어가 들어왔을 때, 해당 검색어가 요약에 포함된 레시피들의 리스트를 반환
    async def summary_keyword_search(self, search_word: str, limit: int = 100) -> list[dict] :
        sections = await self.section_repo.get_section_seq_by_keyword(search_word)

        logger.info(f"[keyword search] 키워드 존재 섹션 검색 완료 | 결과 섹션 수 : {len(sections)}")
        
        section_seq_list = [item["section_seq"] for item in sections]

        recipe_list = await self.mixed_repo.get_recipes_with_section_seq_list(section_seq_list)

        return recipe_list

    # 검색어가 들어왔을 때, 해당 검색어가 본문에 포함된 레시피들의 리스트를 반환
    async def text_keyword_search(self, search_word: str, limit: int = 100) -> list[dict] :
        texts = self.original_texts_repo.get_text_seq_by_keyword(search_word)

        logger.info(f"[keyword search] 키워드 존재 텍스트 검색 완료 | 결과 텍스트 수 : {len(texts)}")
        
        text_seq_list = [item["text_seq"] for item in texts]

        recipe_list = await self.mixed_repo.get_recipes_with_text_seq_list(text_seq_list)

        return recipe_list

    # 검색어가 들어왔을 때, 해당 검색어가 요약과 유사도가 높은 레시피들의 리스트를 반환
    async def semantic_search(self, search_word: str, limit: int = 100, user_seq: int=None) -> list[dict] :

        search_vector = await self._create_search_vector(search_word)

        search_list = await self.section_repo.find_similar_sections_with_score(
            query=search_word,
            query_vector=search_vector,
            k=limit
        )

        section_seq_list = [
            section.section_seq
            for section, score in search_list
            if score >= 0.55
        ]

        recipe_list = await self.mixed_repo.get_recipes_with_section_seq_list(section_seq_list)
        if user_seq is not None:
            user_recipe_list = await self.mixed_repo.get_user_recipes(user_seq)

        # user_recipe_list 에 있는 recipe_seq 들을 set 으로
        user_recipe_seq_set = {
            recipe.recipe_seq for recipe in user_recipe_list
        }

        # recipe_list 순서를 유지하면서 필터링
        filtered_recipes = [
            recipe
            for recipe in recipe_list
            if recipe.recipe_seq in user_recipe_seq_set
        ]

        return filtered_recipes

    # 검색어를 통해서 해당 레시피에서 가장 연관성 높은 섹션을 반환
    async def select_preview(self, search_word: str, target_recipe_seq) :

        search_vector = await self._create_search_vector(search_word=search_word)

        section_seq_list = await self.section_recipes_repo.get_section_seqs_by_recipe_seq(target_recipe_seq)

        most_similar_section = await self.section_repo.find_similar_sections_with_score(query=search_word, query_vector=search_vector, k=1, section_seq_list=section_seq_list)

        original_texts_list = await self.original_texts_repo.get_original_texts(section_seqs=[most_similar_section[0][0].section_seq])

        return original_texts_list[0].original_text
