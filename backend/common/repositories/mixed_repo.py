from typing import List, Dict, Any, Optional
import json
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct, case, desc, func

from common.repositories.original_texts_repo import OriginalTextsRepository
from common.repositories.doc_recipes_repo import DocRecipesRepository
from common.repositories.section_repo import SectionRepository
from common.repositories.section_recipes_repo import SectionRecipesRepository
from common.repositories.tag_repo import TagRepository
from common.repositories.doc_recipes_repo import DocRecipesRepository

from common.models import DocRecipe, SectionRecipe, OriginalText, Section, DocRecipeMember
from common.core.codes import MergeActionType, DocRecipeRole
# from common.util.text_helper import clean_original_text
# [DEBUG] 쿼리 확인
# from sqlalchemy.dialects import postgresql

# from dotenv import load_dotenv
# import os
# from google import genai


class MixedRepository:
    """
    여러 리포지토리를 조합하여 복합적인 데이터 조회를 담당하는 저장소.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.text_repo = OriginalTextsRepository(db)
        self.doc_recipe_repo = DocRecipesRepository(db)
        self.section_repo = SectionRepository(db)
        self.section_recipe_repo = SectionRecipesRepository(db)
        self.tag_repo = TagRepository(db)

    # ------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------
    async def save_ai_proposal_assets(
        self, 
        task_id: UUID,
        ai_output: dict, 
        team_seq: Optional[int]
    ) -> Optional[DocRecipe]:
        """AI 제안(ai_output)을 기반으로 지식 자산 일괄 생성"""
        
        if "sections" not in ai_output:
            return None
            
        sections = ai_output["sections"]
        if not sections or any(item.get("is_exist") for item in sections):
            # 내용이 없거나 기존 내용이 섞여있어 처리가 애매한 경우 (현재 로직상 전체 신규만 처리 중이나, 확장 가능)
            # 여기서는 호출 측 로직 준수: is_exist가 false인 것들만 처리하거나,
            # 아니면 전체 신규일 때만 처리하는 조건은 호출 측에서 이미 검사했다고 가정.
            pass

        # 1) Indices 데이터 생성
        # [최적화] 단일 반복문으로 통합 처리
        
        # 0. 후보 레시피(DocRecipe) 선 생성
        new_recipe = DocRecipe(
            doc_type_code="GENERATED_CANDIDATE",
            recipe_value=json.dumps(ai_output),
            title=f"AI Merge Proposal for Task {task_id}",
        )
        saved_recipe = await self.doc_recipe_repo.create(new_recipe)
        new_recipe_seq = saved_recipe.recipe_seq
        
        # 상태 관리 변수
        created_indices = {} # Name -> Index Object Cache
        new_section_recipes = [] # Batch Insert 대상
        current_coord = 0
        
        for item in sections:
            current_coord += 1
            
            target_section_seq = None
            target_text_seq = None
            
            # Case A: 신규 생성 (is_exist: False)
            if item.get("is_exist") is False:
                
                # A-1. Index 처리 (On-demand Check & Create)
                index_val = item.get("index")
                target_index_seq = None
                
                if index_val and isinstance(index_val, str):
                    # 캐시에 없으면 DB 조회/생성 시도
                    if index_val not in created_indices:
                        # existing_idx = await self.index_repo.get_by_name_and_parent(index_val, None)
                        # TODO: index_repo가 필요하다면 추가 주입하거나 로직 보완 필요
                        # 현재 knowledge_asset_repo.py 원본에도 index_repo는 init에 없음
                        # 주석 처리된 상태 그대로 유지
                        existing_idx = None 
                        if existing_idx:
                            created_indices[index_val] = existing_idx
                        else:
                            # new_index = Index(
                            #     team_seq=team_seq,
                            #     index_name=index_val,
                            #     parent_seq=None,
                            #     depth=1,
                            #     index_path=f"/{index_val}"
                            # )
                            # saved_index = await self.index_repo.create(new_index)
                            # created_indices[index_val] = saved_index
                            pass
                    
                    # target_index_seq = created_indices[index_val].index_seq
                    pass
                
                # A-2. Section 생성
                essence_val = item.get("essence", "")
                vector_val = item.get("essence_vector")
                if isinstance(vector_val, str):
                    try:
                        vector_val = json.loads(vector_val)
                    except (ValueError, TypeError):
                        vector_val = None
                
                new_section = await self.section_repo.create_section(
                    index_seq=None, # target_index_seq,
                    origin_type_code="TEXT",
                    essence=essence_val,
                    essence_vector=vector_val
                )
                target_section_seq = new_section.section_seq
                
                # A-3. Original Text 생성
                origin_text_val = item.get("original_text", "")
                saved_texts = await self.text_repo.create_batch(
                    section_seq=target_section_seq,
                    texts=[origin_text_val]
                )
                if saved_texts:
                    target_text_seq = saved_texts[0].text_seq
                    
            # Case B: 기존 존재 (is_exist: True)
            else:
                target_text_seq = item.get("text_seq")
                # 기존 텍스트 시퀀스로 섹션 정보 역추적
                if target_text_seq:
                    original_text_obj = await self.text_repo.get_by_text_seq(target_text_seq)
                    if original_text_obj:
                        target_section_seq = original_text_obj.section_seq
            
            # Common: Recipe Mapping 객체 생성
            if target_section_seq or target_text_seq:
                sr_record = SectionRecipe(
                    section_seq=target_section_seq,
                    text_seq=target_text_seq,
                    recipe_seq=new_recipe_seq,
                    coord=current_coord
                )
                new_section_recipes.append(sr_record)
        
        # 일괄 저장 (Batch Insert)
        if new_section_recipes:
            await self.section_recipe_repo.create_batch(new_section_recipes)
            
        return saved_recipe

    # ------------------------------------------------------------
    # READ
    # ------------------------------------------------------------
    async def get_before_section(self, recipe_seq: int) -> List[Dict[str, Any]]:
        """
        recipe_seq로 해당 recipe에 맞는 original_text 목록을 조회
        """
        recipe_detail = await self.doc_recipe_repo.get_by_seq(recipe_seq)
        original_texts = []

        if recipe_detail and recipe_detail.recipe_value:
            recipe_value = recipe_detail.recipe_value
            try:
                if isinstance(recipe_value, list):
                    value_list = recipe_value
                elif isinstance(recipe_value, str):
                    value_list = json.loads(recipe_value)
                else:
                    raise ValueError(f"Unsupported type for recipe_value: {type(recipe_value)}")

                # Ensure list of ints
                value_list = [int(x) for x in value_list]
            except Exception as e:
                # print(f"Error parsing recipe_value: {e}")
                raise ValueError(f"recipe_value 처리 과정에서 오류가 발생했습니다: {e}")
            
            for value in value_list:
                text_obj = await self.text_repo.get_by_text_seq(value)
                if text_obj:
                    # 필요한 필드만 dict로 구성 (engine 호환성)
                    # 반환 타입이 단순 객체 리스트인지, dict 리스트인지 기존 로직을 고려
                    # 기존 mixed_repo는 text_obj (객체 or dict)를 반환했음
                    # WorkerService에서 사용하는 형태인 Dict로 반환하도록 조정
                    original_texts.append({
                        "text_seq": text_obj.text_seq,
                        "section_seq": text_obj.section_seq,
                        "original_text": text_obj.original_text
                    })
        else:
            raise ValueError("recipe를 불러올 수 없습니다.")      

        return original_texts
    
    
    async def get_search_sections(self, search_word, search_vector, num_of_sections=1) :
        """
        검색어를 입력하면 해당 검색어와 가장 유사한 섹션 {num_of_sections}개를 반환
        """
        # load_dotenv()
        # GEMINI_KEY=os.environ.get("GEMINI_API_KEY")

        # section_seqs = []

        # client = genai.Client(api_key=GEMINI_KEY)

        # # Gemini 임베딩 생성 요청
        # response = client.models.embed_content(
        #     model="text-embedding-004",
        #     contents=search_word
        # )

        # search_vector = response.embeddings[0].values

        similar_sections = await self.section_repo.find_similar_sections_with_score(
            query = search_word, query_vector=search_vector, k=num_of_sections
        )

        return similar_sections

    # section_seq 들의 리스트를 가지고, recipes들의 리스트를 section이 많이 포함된 순서대로 반환
    async def get_recipes_with_section_seq_list(self, section_seq_list: List[int]):
        if not section_seq_list:
            return []

        priority_case = case(
            *[
                (SectionRecipe.section_seq == seq, idx)
                for idx, seq in enumerate(section_seq_list)
            ],
            else_=len(section_seq_list)
        )

        stmt = (
            select(DocRecipe)
            .join(SectionRecipe, DocRecipe.recipe_seq == SectionRecipe.recipe_seq)
            .where(SectionRecipe.section_seq.in_(section_seq_list))
            .group_by(DocRecipe.recipe_seq)
            .order_by(
                desc(func.count(SectionRecipe.section_seq)),
                func.min(priority_case)
            )
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # section_seq 들의 리스트를 가지고, recipes들의 리스트를 section이 많이 포함된 순서대로 반환
    async def get_recipes_with_text_seq_list(self, text_seq_list: List[int]) :
        stmt = (
            select(DocRecipe)
            .join(SectionRecipe, DocRecipe.recipe_seq == SectionRecipe.recipe_seq)
            .where(SectionRecipe.text_seq.in_(text_seq_list))
            .group_by(DocRecipe.recipe_seq)
            .order_by(desc(func.count(SectionRecipe.text_seq)))
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # 현재 유저가 권한이 있는 문서 레시피만 출력
    async def get_user_recipes(self, user_seq: int) -> List[DocRecipe]:
        query = (
            select(DocRecipe)
            .join(
                DocRecipeMember,
                DocRecipeMember.recipe_seq == DocRecipe.recipe_seq
            )
            .where(DocRecipeMember.user_seq == user_seq)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # 문서 레시피 생성
    async def create_doc_recipe(self, doc_type_code: str, title: str, recipe_value: Any, auto_commit: bool = True, user_seq: int = None) -> DocRecipe:
        recipe = await self.doc_recipe_repo.create_doc_recipe(doc_type_code, title, recipe_value, auto_commit)
        if user_seq is not None:
            member = DocRecipeMember(
                recipe_seq=recipe.recipe_seq,
                user_seq=user_seq,
                role_code=DocRecipeRole.R_ADMIN  # 문서 생성자는 관리자 권한
            )
            self.db.add(member)
            
        return recipe

    # ------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------
    async def save_recipe_with_new_sort(
        self,
        recipe_seq: int,
        text_section_list: List[dict]
    ):
        """
        기존 레시피에 대해 새로운 텍스트 순서를 적용하여 저장
        """

        # 1) 기존 레시피 조회
        existing_recipe = await self.doc_recipe_repo.get_by_seq(recipe_seq)
        if not existing_recipe:
            return None
        

        text_seq_list = [item.get('text_seq') for item in text_section_list]

        # 2) 조립 규칙 상세 정의 수정
        # existing_recipe의 recipe_value 수정
        # existing_recipe의 recipe_value 수정
        await self.doc_recipe_repo.touch_recipe_value(recipe_seq, text_seq_list)

        # 3) section_recipes 테이블 recipe_seq로 조회하여 삭제 
        await self.section_recipe_repo.delete_by_recipe_seq(recipe_seq)

        # 4) section_recipes 테이블에 text_section_list에 따라 insert
        for idx, text_section in enumerate(text_section_list):
            await self.section_recipe_repo.create_section_recipe(
                recipe_seq=recipe_seq,
                text_seq=text_section.get('text_seq'),
                section_seq=text_section.get('section_seq'),
                coord=idx
            )

    # ------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------
    async def check_user_recipe_permission(
        self, 
        user_seq: int, 
        recipe_seq: int,
        required_roles: List[str] = None
    ) -> bool:
        """
        사용자가 특정 레시피에 대한 권한을 가지고 있는지 확인
        
        Args:
            user_seq: 사용자 식별자
            recipe_seq: 레시피 식별자
            required_roles: 필요한 권한 목록 (예: ['R_ADMIN', 'R_EDITOR'])
                           None인 경우 권한 존재 여부만 확인
        
        Returns:
            bool: 권한이 있으면 True, 없으면 False
        """
        query = (
            select(DocRecipeMember.role_code)
            .where(
                DocRecipeMember.user_seq == user_seq,
                DocRecipeMember.recipe_seq == recipe_seq
            )
        )
        
        result = await self.db.execute(query)
        role = result.scalar_one_or_none()
        
        if role is None:
            return False
        
        # 기존 데이터 호환성: 빈 문자열은 R_ADMIN으로 간주
        if role == "":
            role = DocRecipeRole.R_ADMIN
        
        if required_roles is None:
            return True
        
        return role in required_roles

    async def delete_document_transaction(self, recipe_seq: int) -> bool:
        """
        [Transaction] 문서 삭제 (관련 데이터 일괄 삭제)
        """
        try:
            # 1. section_recipes 삭제
            await self.section_recipe_repo.delete_by_recipe_seq(recipe_seq, auto_commit=False)
            
            # 2. original_texts 삭제
            await self.text_repo.delete_by_recipe_seq(recipe_seq, auto_commit=False)
            
            # 3. doc_recipes 삭제 (CASCADE로 doc_recipe_members도 자동 삭제)
            await self.doc_recipe_repo.delete_by_recipe_seq(recipe_seq, auto_commit=False)

            # 4. 정리 (연결 끊어진 텍스트 삭제)
            await self.text_repo.delete_orphaned_texts(auto_commit=False)
            
            # 5. 모든 작업 커밋
            await self.db.commit()
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise e

    # ------------------------------------------------------------
    # ETC
    # ------------------------------------------------------------
    
    # save_document_update
    # 작업영역 202601281035

    async def save_document_update(self,recipe_seq: int, section_list: List[dict], text_update_list: List[dict] = None, user_seq: int = None, has_merge_section: bool = False, title: str = None) -> int:
        """
        [Transaction] 문서 업데이트 사항을 일괄 적용하고 커밋.
        apply_document_update에서 호출됨.
        
        Returns:
            int: 생성되거나 업데이트된 recipe_seq
        """
        try:

            section_recipes = []

            # 1. updates 처리
            for idx, section_item in enumerate(section_list):
                # MergeActionType은 JSON 역직렬화 시 문자열일 수 있으므로 처리
                mat = section_item.get("merge_action_type")
                
                text_seq = section_item.get("text_seq")
                section_seq = section_item.get("section_seq")

                # 작업번호 202601281627
                tag_str = section_item.get("tag", "")
                tag_seqs = []
                if isinstance(tag_str, str) and tag_str:
                    # '.' 로 스플릿
                    tag_names = tag_str.split('.')
                    # 빈 문자열 제거 (혹시 '..' 등이 있을 경우)
                    tag_names = [t.strip() for t in tag_names if t.strip()]
                    
                    if tag_names:
                        # tag_repo를 통해 seq 조회
                        tag_seqs = await self.tag_repo.get_seqs_by_names(tag_names)
                
                # Enum 비교를 위해 값 변환 (필요 시)
                # 여기서는 update["merge_action_type"]이 이미 올바른 값(Enum or Str)이라고 가정하지만
                # 안전하게 Str 비교 또는 Enum 변환
                if mat == MergeActionType.SKIP or mat == "SKIP":
                    do_nothing = True

                    # section_recipes에 추가
                    section_recipes.append({
                        "text_seq": text_seq,
                        "section_seq": section_seq,
                        "coord": idx + 1
                    })
                elif mat == MergeActionType.LINK_SECTION or mat == "LINK_SECTION":
                    # region [처리 로직]
                    # LINK_SECTION: 기존 텍스트 업데이트
                    await self.text_repo.update_text(
                        text_seq=text_seq,
                        new_text=section_item.get("original_text"),
                        auto_commit=False # Deferred Commit
                    )

                    # section_recipes에 추가
                    section_recipes.append({
                        "text_seq": text_seq,
                        "section_seq": section_seq,
                        "coord": idx + 1
                    })
                    # endregion
                elif mat == MergeActionType.MERGE_SECTION or mat == "MERGE_SECTION":
                    # region [처리 로직]
                    # ------------------------------------------------------------
                    after_text = section_item.get("after_text")

                    await self.text_repo.update_text(
                        text_seq=text_seq,
                        new_text=after_text,
                        auto_commit=False # Deferred Commit
                    )

                    essence = section_item.get("essence")
                    essence_vector = section_item.get("essence_vector")
                    
                    await self.section_repo.update_section(
                        section_seq=section_seq,
                        essence=essence,
                        essence_vector=essence_vector,
                        tag=tag_seqs,
                        auto_commit=False # Deferred Commit
                    )

                    # section_recipes에 추가
                    section_recipes.append({
                        "text_seq": text_seq,
                        "section_seq": section_seq,
                        "coord": idx + 1
                    })

                    # ------------------------------------------------------------
                    # endregion

                elif mat == MergeActionType.CREATE_NEW or mat == "CREATE_NEW":
                    # region [처리 로직]
                    # ------------------------------------------------------------
                    # CREATE_NEW: 신규 섹션 -> 신규 텍스트 -> 신규 섹션레시피 연결

                    _section_seq = 0
                    
                    if section_item.get("section_seq"):
                        _section_seq = section_item.get("section_seq")
                    else:
                        
                        # 단건 저장 update 1개 = setionc 1개
                        new_section = await self.section_repo.create_section(
                                tag=tag_seqs, # 조회된 태그 seq 리스트
                                origin_type_code="TEXT",
                                essence=section_item.get("essence", ""),
                                essence_vector=section_item.get("essence_vector"),
                                auto_commit=False
                            )
                        _section_seq = new_section.section_seq
                    
                    # 생성된 섹션 seq와 text로 original_text 생성
                    new_text = await self.text_repo.create(
                        original_text=section_item.get("original_text", ""),
                        section_seq=_section_seq,
                        auto_commit=False
                    )

                    # section_recipes에 추가
                    section_recipes.append({
                        "text_seq": new_text.text_seq,
                        "section_seq": _section_seq,
                        "coord": idx + 1
                    })


            recipe_value = [section_recipe["text_seq"] for section_recipe in section_recipes]

            # 신규 레시피 라면
            if not recipe_seq:
                
                # doc_recipe 추가
                doc_recipe = await self.create_doc_recipe(
                    doc_type_code="TEXT",
                    title=title if title else "새 문서",
                    recipe_value=recipe_value,
                    auto_commit=False,
                    user_seq = user_seq
                )
                recipe_seq = doc_recipe.recipe_seq
            else:

                # recipe_value 업데이트
                await self.doc_recipe_repo.touch_recipe_value(
                    recipe_seq=recipe_seq,
                    recipe_value=recipe_value,
                    auto_commit=False
                )

            # section_recipe 삭제
            await self.section_recipe_repo.delete_by_recipe_seq(
                recipe_seq=recipe_seq,
                auto_commit=False
            )

            # section_recipe 추가
            for section_recipe in section_recipes:
                await self.section_recipe_repo.create_section_recipe(
                    recipe_seq=recipe_seq,
                    text_seq=section_recipe["text_seq"],
                    section_seq=section_recipe["section_seq"],
                    coord=section_recipe["coord"],
                    auto_commit=False
                )

            # 2. text_update_list 처리 (필요시)
            # 현재 apply_document_update 에서는 updates만 루프 돌고 있음.
            # text_update_list 변수 사용 (함수 인자로 전달받은 값)
            text_update_list = text_update_list or []
            for text_update in text_update_list:
                await self.text_repo.update_text(
                    text_seq=text_update.text_seq,
                    new_text=text_update.original_text,
                    auto_commit=False # Deferred Commit
                )

            # 3. 정리 (연결 끊어진 텍스트 삭제)
            await self.text_repo.delete_orphaned_texts(auto_commit=False)

            # 4. 최종 커밋
            await self.db.commit()
            #await self.db.rollback()
            
            return recipe_seq
            
        except Exception as e:
            await self.db.rollback()
            raise e
