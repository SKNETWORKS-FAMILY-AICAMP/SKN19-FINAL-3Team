from common.core.config import settings
from common.core.crypto import CryptoService
from common.models import SecureToken, User
from common.repositories.doc_recipes_repo import DocRecipesRepository
from common.repositories.mixed_repo import MixedRepository
from common.repositories.model_logs_repo import ModelLogsRepository
from common.repositories.original_texts_repo import OriginalTextsRepository
from common.repositories.redis_repo import RedisRepository
from common.repositories.section_recipes_repo import SectionRecipesRepository
from common.repositories.section_repo import SectionRepository
from common.repositories.secure_token_repo import SecureTokenRepository
from common.repositories.local_repo import DocLocalRepository
from common.util.crypto_masking import InfoMask
from common.util.search_word import DocSearch
import re

from uuid import UUID
from typing import Optional, List, Any, Dict
from pydantic import TypeAdapter

from common.schemas import (
    LlmTaskRequest,
    LlmTaskResponse,
    LlmTaskDetailResponse,
    DocResponse,
    DocProposalResponse,
    DocUpdateRequest,
    PrivacyPatternCreate,
    PrivacyPatternResponse,
    TokenizeResponse,
    MergeProposalInputData,
    MergeProposalInputDataV2,
    MergeSectionItem,
    IndexingAiOutput,
    MergeSelectionResponse,
    MergeRecipe,
    MergeText,
    GeneratedTextItem,
    DocApplyRequest,
)
from common.core.codes import LlmTaskType, LlmTaskStatus, MergeProposalType, MergeActionType, DocRecipeRole
from common.models import OriginalText, DocRecipe
import uuid, json
from datetime import datetime


class DocumentAdaptionService:
    """
    [AJC Core Service]
    외부 문서를 시스템의 지식 체계(Context)에 맞게 '적응(Adapt)'시키는 워크플로우
    """

    def __init__(
        self,
        redis_repo: RedisRepository,
        logs_repo: Optional[ModelLogsRepository] = None,
        sct_repo: Optional[SectionRepository] = None,
        recipe_repo: Optional[DocRecipesRepository] = None,
        text_repo: Optional[OriginalTextsRepository] = None,
        token_repo: Optional[SecureTokenRepository] = None,
        # mixed_repo: MixedRepository (Optional, but recommended for asset creation)
        mixed_repo: Optional[MixedRepository] = None,
        section_recipe_repo: Optional[SectionRecipesRepository] = None,
        user: Optional[User] = None,
        local_repo : Optional[DocLocalRepository] = None,
        search_engine: Optional[DocSearch] = None,
        pattern_repo = None  # PatternRepository for InfoMask
    ):
        self.redis_repo = redis_repo
        self.logs_repo = logs_repo
        self.sct_repo = sct_repo
        self.recipe_repo = recipe_repo
        self.text_repo = text_repo
        self.token_repo = token_repo
        self.mixed_repo = mixed_repo
        self.section_recipe_repo = section_recipe_repo
        self.user = user
        self.local_repo = local_repo
        self.search_engine = search_engine
        self.pattern_repo = pattern_repo

    def _check_dependencies(self):
        """
        [의존성 주입 확인]
        필요한 모든 리포지토리가 주입되었는지 확인하고, 없으면 에러를 발생시킵니다.
        """
        required = [
            "logs_repo", "sct_repo", "recipe_repo", 
            "text_repo", "token_repo", "mixed_repo", 
            "section_recipe_repo"
        ]
        
        for name in required:
            if not getattr(self, name, None):
                raise ValueError(f"{name}가 주입되지 않았습니다")

    # [Privacy] Pattern Management
    # async def create_privacy_pattern  <- Deprecated (Config based)

    async def get_privacy_patterns(self) -> List[PrivacyPatternResponse]:
        """
        [설정 기반 패턴 조회]
        Config(settings)에 정의된 민감 정보 패턴(Regex) 로드.
        DB 대신 Config 사용: 패턴 변경이 배포 주기를 따르도록 관리하기 위함.
        """
        patterns = []
        try:
            raw_json = settings.PRIVACY_PATTERNS_JSON
            items = json.loads(raw_json)
            for idx, item in enumerate(items):
                patterns.append(
                    PrivacyPatternResponse(
                        pattern_seq=idx,
                        pattern_name=item["name"],
                        regex_pattern=item["pattern"],
                        is_active=True,
                        created_at=datetime.now(),
                    )
                )
        except Exception as e:
            print(f"Error parsing PRIVACY_PATTERNS_JSON: {e}")

        return patterns

    # [Privacy] Tokenization
    async def tokenize_text(self, text: str) -> str:
        self._check_dependencies()

        # Load from Config instead of DB
        patterns = await self.get_privacy_patterns()

        result_text = text

        # 설정된 모든 개인정보 패턴에 대해 순차적으로 검사 및 치환 수행
        for pattern in patterns:
            try:
                # 1. 매칭되는 모든 문자열 추출
                # 중복된 문자열에 대해 불필요한 연산을 줄이기 위해 집합(set)으로 유니크 값만 추출
                regex = re.compile(pattern.regex_pattern)
                found_strings = set(regex.findall(result_text))

                for origin_str in found_strings:
                    if not origin_str:
                        continue

                    # 1. Check Hash
                    data_hash = CryptoService.encrypt_data_hmac(origin_str)

                    # 2. 기존 토큰 존재 여부 확인 (재사용성 보장)
                    # 동일한 데이터에 대해서는 항상 같은 토큰 식별자를 유지하여 정합성 확보
                    existing_token = await self.token_repo.get_by_hash(data_hash)

                    if existing_token:
                        token_str = existing_token.token_text
                    else:
                        # 3. 신규 토큰 생성
                        # 원본 데이터는 AES로 암호화하여 저장하고, 해시값으로 매핑 관리
                        ciphertext = CryptoService.encrypt_data_aes(origin_str)

                        # [트랜잭션 전략]
                        # 식별자(seq) 생성을 위해 먼저 '임시 값'으로 레코드를 생성한 후,
                        # 생성된 seq를 포함한 최종 토큰 포맷({{TYPE_SEQ}})으로 업데이트

                        new_token = SecureToken(
                            token_text="TEMP",  # 임시 값 (업데이트 예정)
                            data_type=pattern.pattern_name,
                            ciphertext=ciphertext,
                            data_hash=data_hash,
                        )
                        saved_token = await self.token_repo.create_token(new_token)

                        # 생성된 Seq를 이용해 실제 토큰 값 생성 및 저장
                        real_token_value = (
                            f"{{{{{pattern.pattern_name}_{saved_token.token_seq}}}}}"
                        )
                        saved_token.token_text = real_token_value  # type: ignore
                        await self.token_repo.create_token(saved_token)  # 업데이트 반영

                        token_str = real_token_value

                    # 4. 원본 문자열 치환
                    # 추출한 유니크 문자열에 해당하는 모든 부분을 토큰으로 일괄 변경
                    # re.escape를 사용하여 특수문자가 포함된 원본 문자열도 안전하게 처리
                    result_text = re.sub(re.escape(origin_str), token_str, result_text)  # type: ignore

            except re.error:
                # Invalid regex, skip
                continue

        return result_text

    async def request_document_indexing(self, recipe_seq, text) -> LlmTaskResponse:
        """
        [문서 색인 요청]
        긴 문서 처리 시간 소요로 인해 비동기 작업 위임.
        DB에 로그 선기록하여 상태 추적, Redis 큐를 통해 워커(Worker)에 작업 전달.
        """
        self._check_dependencies()

        masking_tool = InfoMask(self.token_repo, self.pattern_repo)

        text = await masking_tool.encrypt_text(text)

        task_id = uuid.uuid4()
        task_type = LlmTaskType.DOC_INDEX
        task_status = LlmTaskStatus.PENDING

        payload = {
            "task_id": str(task_id),
            "task_type": task_type.value,
            "task_status": task_status.value,
            # "text": text, # 페이로드 크기 최적화를 위해 제외 (워커가 DB/Storage에서 조회 권장)
        }

        input_data = {"recipe_seq": recipe_seq, "text": text}

        operator_seq = self.user.user_seq if self.user else None

        # [추적성 보장] DB에 초기 상태(PENDING) 기록
        await self.logs_repo.create(
            operator_seq=operator_seq,
            team_seq=None,
            task_type_code=task_type,
            task_id=task_id,
            start_task_id=task_id,
            input_data=input_data,  # 재현 가능성을 위해 원본 입력 저장
            ai_output=None,
            user_decision=None,
        )
        # [비동기 처리] Redis 큐에 작업 ID 전송
        await self.redis_repo.enqueue(key_name="task_id", payload=payload)

        return LlmTaskResponse(
            task_id=task_id, task_type=task_type, task_status=task_status
        )

    async def request_document_local_save(self, recipe_seq, text) :
        await self.local_repo.upsert(
            recipe_seq=recipe_seq,
            user_seq=self.user.user_seq,
            text=text,
            auto_commit=True,
        )

    async def _fetch_task_state_from_redis(self, task_id: str):
        """
        [상태 조회 공통 로직]
        실시간 작업 상태 파악을 위해 Redis에서 작업 메타데이터 조회.
        """
        meta = await self.redis_repo.get_task_metadata(task_id)

        if not meta:
            raise KeyError("작업을 찾을 수 없습니다.")

        task_status = None
        task_type = None

        if "task_status" in meta:
            try:
                task_status = LlmTaskStatus(meta["task_status"])
            except ValueError:
                raise KeyError("작업 상태를 찾을 수 없습니다.")

        if "task_type" in meta:
            try:
                task_type = LlmTaskType(meta["task_type"])
            except ValueError:
                raise ValueError("알 수 없는 작업 상태입니다.")

        return task_status, task_type

    async def get_task_status(self, task_id: str) -> LlmTaskDetailResponse:
        task_status, task_type = await self._fetch_task_state_from_redis(task_id)

        return LlmTaskDetailResponse(
            task_id=uuid.UUID(task_id),
            task_type=task_type,  # type: ignore
            task_status=task_status,  # type: ignore
            results=None,
        )

    async def get_task_detail(self, task_id: str) -> LlmTaskDetailResponse:
        # 1. Redis 우선 조회 (진행 중인 작업 상태 확인)
        task_status, task_type = await self._fetch_task_state_from_redis(task_id)

        # 2. DB 조회 (작업 완료 여부 및 결과 데이터 확인)
        # Redis 키 만료 이후에도 영구적인 기록 확인 목적.
        log = None
        if self.logs_repo:
            try:
                uuid_obj = uuid.UUID(task_id)
                log = await self.logs_repo.get_by_task_id(uuid_obj)
            except (ValueError, TypeError):
                # 로그가 없으면 아직 Redis 상에만 존재하거나 잘못된 ID임
                raise KeyError("작업 상태를 찾을 수 없습니다.")

        if log:
            return LlmTaskDetailResponse(
                task_id=uuid.UUID(task_id),
                task_type=LlmTaskType(log.task_type_code),
                task_status=LlmTaskStatus.COMPLETED,
                results={"input_data": log.input_data, "ai_output": log.ai_output},
            )

        if task_status and task_type:
            return LlmTaskDetailResponse(
                task_id=uuid.UUID(task_id),
                task_type=task_type,
                task_status=task_status,
                results=None,
            )

        raise ValueError("작업을 찾을 수 없습니다")

    async def get_all_documents(self) -> Optional[List[DocResponse]]:
        """[문서 목록 조회] 등록된 모든 문서 레시피 반환."""
        return await self.mixed_repo.get_user_recipes(self.user.user_seq)  # type: ignore

    async def get_document(self, recipe_seq: int) -> Optional[DocResponse]:
        """
        [특정 문서 상세 조회]
        Recipe(조립 규칙) 기반, 흩어진 Original Text들을 조합해
        하나의 완성된 문서 텍스트로 재구성.
        """
        recipe = await self.recipe_repo.get_by_seq(recipe_seq)  # type: ignore
        if not recipe:
            return None

        masking_tool = InfoMask(self.token_repo, self.pattern_repo)

        # 기본 값 설정
        final_recipe_value = recipe.recipe_value
        final_title = None
        final_text = None
        decrypt_text = None

        if recipe.recipe_value and isinstance(recipe.recipe_value, list):  # type: ignore
            try:
                # 1. 레시피 파싱 (JSON)
                # 문서가 어떤 텍스트 조각(Sequences)들로 구성되어 있는지 확인
                parsed_value = recipe.recipe_value
                final_recipe_value = parsed_value

                # 2. 원본 텍스트 조회 및 조립
                # 레시피에 명시된 순서대로 텍스트 조각들을 DB에서 가져와 결합
                if isinstance(parsed_value, list):
                    texts = []
                    for idx, item in enumerate(parsed_value):
                        if isinstance(item, int):
                            text_obj = await self.text_repo.get_by_text_seq(item)  # type: ignore

                            if not text_obj:
                                raise ValueError("텍스트를 찾을 수 없습니다.")
                            texts.append(text_obj.original_text)
                            # if text_obj:
                            #     # 첫 번째가 아니면 앞에 개행 2개 추가
                            #     if idx > 0:
                            #         texts.append("\n\n" + text_obj.original_text)
                            #     else:
                            #         texts.append(text_obj.original_text)

                    # 3. 최종 텍스트 생성
                    if texts:
                        final_text = "".join(texts)
                        first_line = texts[0].split("\n")[0]
                        final_title = first_line.replace("#", "").strip()

                    local_recipe = await self.local_repo.get_full(recipe_seq, self.user.user_seq)
                    if local_recipe :
                        if recipe.updated_at < local_recipe.updated_at :
                            final_text = local_recipe.text
                    
                    decrypt_text = await masking_tool.decrypt_text(final_text)


            except ValueError:
                pass

        # 새로운 객체(DTO) 생성 반환
        return DocResponse(
            recipe_seq=recipe.recipe_seq,  # type: ignore
            doc_type_code=recipe.doc_type_code,  # type: ignore
            recipe_value=final_recipe_value,  # type: ignore
            created_at=recipe.created_at,  # type: ignore
            updated_at=recipe.updated_at,  # type: ignore
            title=final_title,
            text=decrypt_text,
        )

    async def get_merge_proposal(self, task_id: str) -> Optional[LlmTaskResponse]:
        """
        [병합 제안 생성]
        """
        try:
            
            # region 유효성 체크 & 초기화

            self._check_dependencies()
            
            if not task_id:
                raise ValueError("Task ID가 필요합니다")
            
            log = await self.logs_repo.get_by_task_id(task_id)  # type: ignore
            if not log:
                raise ValueError("model_log 없음")
            
            if not log.ai_output:
                raise ValueError("log.ai_output이 없습니다. AI 작업이 완료되지 않았거나 실패했을 수 있습니다.")
            
            # 지역변수
            masking_tool = InfoMask(self.token_repo, self.pattern_repo)
            new_task_uuid = uuid.uuid4()
            task_type = LlmTaskType.MERGE_PROP
            task_status = LlmTaskStatus.PENDING
            start_task_uuid = log.start_task_id
            
            current_recipe_seq = log.input_data.get("recipe_seq", 0)
            ai_analyzed_sections = TypeAdapter(List[IndexingAiOutput]).validate_python(log.ai_output)

            if not ai_analyzed_sections:
                raise ValueError("ai_analyzed_sections가 비어 있습니다. AI 작업이 완료되지 않았거나 실패했을 수 있습니다.")


            # endregion

            is_all_skip = all(item.merge_action_type == MergeActionType.SKIP for item in ai_analyzed_sections)
            
            
            # region 유사도 조회

            if not is_all_skip:
                for this_section in ai_analyzed_sections:

                    if not this_section.merge_action_type in (MergeActionType.UNKNOWN):
                        continue

                    if not this_section.essence_vector:
                        raise ValueError("essence_vector 없음")

                    
                    this_section.merge_action_type = MergeActionType.CREATE_NEW

                
                    # 텍스트 기반 조회
                    original_text_obj = await self.text_repo.get_by_stripped_text(this_section.original_text)

                    # 동일한 텍스트가 존재하면 CREATE_NEW이나 section_seq를 가져간다
                    if original_text_obj:
                        this_section.section_seq = original_text_obj.section_seq                        
                        this_section.score = 1.0
                        continue


                    # 벡터 기반 조회
                    similar_sections = await self.sct_repo.find_similar_sections_with_score(
                        query=this_section.essence, 
                        query_vector=this_section.essence_vector, 
                        k=1
                    )

                    
                    if similar_sections:
                        similar_section, score = similar_sections[0]
                        
                        # 0.95 이상이면 단순 링크 (내용 동일)
                        if settings.THRESHOLD_LEVEL1 <= score:
                            this_section.section_seq = similar_section.section_seq
                            this_section.score = score
            # endregion

            # region 연관 레시피 조회

            # 레시피와 연결된 섹션 매핑
            target_recipe_text_map = {}
            
            if not is_all_skip:
                for this_section in ai_analyzed_sections:

                    # MergeActionType.MERGE_SECTION만 허용
                    if not this_section.merge_action_type in (MergeActionType.MERGE_SECTION):
                        continue
                    
                    # 유효성 체크 - section_seq
                    if not this_section.section_seq:
                        raise ValueError("section_seq 없음")
                    
                    # 해당 섹션을 사용하는 모든 레시피 조회
                    section_recipes = await self.section_recipe_repo.get_by_section_seq_list([this_section.section_seq])
                    
                    # MergeActionType.MERGE_SECTION 이면 무조건 1개라도 존재해야함
                    if not section_recipes:
                        raise ValueError("section_recipes 없음")
                    
                    # 사용자에게 권한이 있는 레시피만 조회
                    user_recipes = await self.mixed_repo.get_user_recipes(self.user.user_seq)

                    # 현재 수정 중인 레시피 제외
                    target_recipe_seqs = {
                        recipe.recipe_seq
                        for recipe in user_recipes
                        if recipe.recipe_seq != current_recipe_seq
                    }
                    
                    # 섹션에서 사용자에게 권한이 있는, 현재 수정중이지 않은 레시피만 필터링
                    section_recipes_filtered = [
                        sr for sr in section_recipes
                        if sr.recipe_seq in target_recipe_seqs
                    ]

                    # 섹션과 연결된 레시피: 결과를 매핑 테이블에 정리
                    temp_recipe_seqs = set()

                    for sr in section_recipes_filtered:
                        # 1. 섹션 -> 레시피 매핑 (현재 루프 내 사용)
                        temp_recipe_seqs.add(sr.recipe_seq)

                        # 2. 레시피 -> 텍스트 매핑
                        if sr.recipe_seq not in target_recipe_text_map:
                            target_recipe_text_map[sr.recipe_seq] = set()
                        target_recipe_text_map[sr.recipe_seq].add(sr.text_seq)
                    
                    # [Input Data 업데이트] analyzed_section에 연관 레시피 정보 저장
                    this_section.related_recipe_seq = list(temp_recipe_seqs)
                
            # endregion

            # region 저장 내용 구성

            final_update_data = []

            for this_section in ai_analyzed_sections:
                # SKIP
                if this_section.merge_action_type in (MergeActionType.SKIP):                    
                    final_update_data.append({
                        "merge_action_type": this_section.merge_action_type,
                        "text_seq": this_section.text_seq,
                        "section_seq": this_section.section_seq
                    })
                # LINK_SECTION
                elif this_section.merge_action_type in (MergeActionType.LINK_SECTION):
                    final_update_data.append({
                        "merge_action_type": this_section.merge_action_type,
                        "text_seq": this_section.text_seq,
                        "section_seq": this_section.section_seq,
                        "original_text": this_section.original_text
                    })
                # CREATE_NEW
                elif this_section.merge_action_type in (MergeActionType.CREATE_NEW):
                    final_update_data.append({
                        "merge_action_type": this_section.merge_action_type,
                        "original_text": this_section.original_text,
                        "section_seq": this_section.section_seq,
                        "essence": this_section.essence,
                        "essence_vector": this_section.essence_vector,
                        "tag": this_section.tag
                    })
                # MERGE_SECTION
                elif this_section.merge_action_type in (MergeActionType.MERGE_SECTION):

                    original_texts = await self.text_repo.get_by_section(this_section.section_seq)
                    related_texts_content = [
                        {"text_seq": t.text_seq, "original_text": t.original_text}
                        for t in original_texts
                        if t.original_text and t.text_seq != this_section.text_seq
                    ]

                    # 대표 before_text (text_seq가 section.text_seq인것)
                    before_text = next((t.original_text for t in original_texts if t.text_seq == this_section.text_seq), None)

                    final_update_data.append({
                        "merge_action_type": MergeActionType.MERGE_SECTION,
                        "section_seq": this_section.section_seq,
                        "text_seq": this_section.text_seq,
                        "before_text": before_text,
                        "after_text": this_section.original_text, # 제안된 텍스트
                        "tag": this_section.tag,
                        "essence": this_section.essence,
                        "essence_vector": this_section.essence_vector,
                        "related_texts": related_texts_content, # AI 제안용
                        "target_recipes": this_section.related_recipe_seq
                    })

                else:
                    raise ValueError("merge_action_type 없음")
            # endregion

            # region 최종 처리

            # target_recipe_text_map -> merge_proposal_target_recipe_list
            merge_proposal_target_recipe_list = [
                {"recipe_seq": recipe_seq, "text_seq_list": list(text_seq_set)}
                for recipe_seq, text_seq_set in target_recipe_text_map.items()
            ]

            # 로그 생성 (신규 model_logs - DOC_UPDATE)
            await self.logs_repo.create(
                operator_seq=None,
                team_seq=None,
                task_type_code=task_type.value,
                task_id=new_task_uuid,
                start_task_id=start_task_uuid,
                input_data={
                    "is_all_skip": is_all_skip,
                    "updates": final_update_data,
                    "recipe_seq": current_recipe_seq,
                    "merge_proposal_target_recipe_list": merge_proposal_target_recipe_list
                }, 
                ai_output=None,
                user_decision={"approver": "SYSTEM_AUTO"}, # 자동 승인 표시
            )


            # 비동기 처리 여부 확인 위함
            merge_section_data = [
                section for section in final_update_data
                if section.get("merge_action_type") == MergeActionType.MERGE_SECTION
                and section.get("related_texts")
            ]

            # merge_section_data가 있으면 [⛓️💥 비동기 처리], 없으면 바로 [✅ 완료 처리]
            if merge_section_data:
                # [⛓️💥 비동기 처리] Redis 큐에 작업 ID 전송
                payload = {
                    "task_id": str(new_task_uuid),
                    "task_type": task_type.value,
                    "task_status": task_status.value,
                }
                await self.redis_repo.enqueue(key_name="task_id", payload=payload)
            else:
                # [✅ 완료 처리]
                task_status = LlmTaskStatus.COMPLETED
            
            return LlmTaskResponse(
                task_id=new_task_uuid, task_type=task_type, task_status=task_status
            )
        
            # endregion

        except ValueError as e:
            print(f"유효하지 않은 값이 있습니다: {e}")
            raise e
        except Exception as e:
            print(f"알 수 없는 에러가 발생했습니다: {e}")
            raise e
    
    async def get_merge_selection(self, task_id: str) -> Optional[MergeSelectionResponse]:
        """
        선택지 생성
        """
        try:
            # region 유효성 체크 & 초기화

            self._check_dependencies()
            
            # 유효성 체크 - task_id가 없는 경우
            if not task_id:
                raise ValueError("Task ID가 필요합니다")
            
            log = await self.logs_repo.get_by_task_id(task_id)  # type: ignore
            # 유효성 체크 - log가 없는 경우
            if not log:
                raise ValueError("model_log 없음")
            
            # 유효성 체크 - log.input_data가 없는 경우
            if not log.input_data:
                raise ValueError("log.input_data가 없습니다.")

            # 유효성 체크 - log.ai_output이 없는 경우
            if not log.ai_output:
                raise ValueError("log.ai_output이 없습니다.")

            # input_data 객체화
            _parse_target = ""
            try:
                _parse_target = "input_data"
                # [변경점] V2 스키마 사용
                input_data = TypeAdapter(MergeProposalInputDataV2).validate_python(log.input_data)
                _parse_target = "ai_output_list"
                ai_output_list = TypeAdapter(List[GeneratedTextItem]).validate_python(log.ai_output)
            except Exception as e:
                raise ValueError(f"{_parse_target} 파싱 실패: {e}")

            text_list_before = []
            masking_tool = InfoMask(self.token_repo, self.pattern_repo)
            recipes = []

            generated_text_map = {item.text_seq: {"original_text": item.original_text, "section_seq": item.section_seq} for item in ai_output_list}

            # endregion

            # region 레시피별로 텍스트 취합

            for this_recipe in input_data.merge_proposal_target_recipe_list:
                """
                1. recipe_seq로 recipe 조회
                2. recipe_data.recipe_value로 text_list_before 조회
                3. merge_recipe에 text_list_before 추가
                4. merge_recipe를 recipes에 추가
                """
                
                # recipe_seq로 recipe 조회
                recipe_data = await self.recipe_repo.get_by_seq(this_recipe.recipe_seq)
                if not recipe_data:
                    raise ValueError(f"recipe_seq: {this_recipe.recipe_seq} 없음")

                merge_recipe = MergeRecipe(
                    recipe_seq=this_recipe.recipe_seq,
                    is_merge=True,
                    title=recipe_data.title,
                    doc_type_code=recipe_data.doc_type_code,
                    texts=[]
                )

                # 유효성 체크 - 레시피 value가 비어있는 경우
                if not recipe_data.recipe_value:
                    raise ValueError(f"레시피 {this_recipe.recipe_seq}에 value가 없습니다.")

                text_list_before = await self.text_repo.get_original_texts(text_seqs = recipe_data.recipe_value)

                # 유효성 체크 - text_list_before가 없는 경우
                if not text_list_before:
                    raise ValueError(f"text_list_before가 없습니다.")

                # 유효성 체크 - text_list_before와 recipe_value의 길이가 다른 경우
                if len(text_list_before) != len(recipe_data.recipe_value):
                    raise ValueError(f"text_list_before와 recipe_value의 길이가 다릅니다.")

                for this_text_seq in recipe_data.recipe_value:

                    text_before_item = next((item for item in text_list_before if item.text_seq == this_text_seq), None)

                    # 유효성 체크 - text_before_item이 없는 경우
                    if not text_before_item:
                        raise ValueError(f"text_before_item이 없습니다.")

                    is_changed = False
                    text_after = None
                    
                    if this_text_seq in generated_text_map.keys():
                        is_changed = True
                        text_after = await masking_tool.decrypt_text(generated_text_map[this_text_seq].get("original_text"))

                    merge_recipe.texts.append(
                        MergeText(
                            is_changed=is_changed,
                            text_seq=this_text_seq,
                            section_seq=text_before_item.section_seq,
                            text_before=await masking_tool.decrypt_text(text_before_item.original_text),
                            text_after=text_after,
                        )
                    )

                recipes.append(merge_recipe)

            # endregion

            return MergeSelectionResponse(
                task_id=uuid.UUID(task_id),
                recipes=recipes
            )

        except ValueError as e:
            print(f"유효하지 않은 값이 있습니다: {e}")
            raise e
        except Exception as e:
            print(f"알 수 없는 에러가 발생했습니다: {e}")
            raise e


    async def apply_document_update_final(self, request: DocApplyRequest):
        """
        문서 업데이트 최종 적용
        """

        try:

            self._check_dependencies()

            task_id = str(request.task_id)  # ensure string


            # task_id로 model_logs 조회
            log = await self.logs_repo.get_by_task_id(task_id)  # type: ignore
            if not log:
                raise ValueError("model_log 없음")
                        
            # model_logs의 input_data에서 updates를 가져옴
            section_list = log.input_data.get("updates")
            if not section_list:
                raise ValueError("updates 없음")

            is_all_skip = log.input_data.get("is_all_skip")
            recipe_seq_currented = log.input_data.get("recipe_seq")

            # 순서만 변경한 경우
            if recipe_seq_currented and is_all_skip:

                # 순서만 변경하여 저장
                await self.mixed_repo.save_recipe_with_new_sort(
                    recipe_seq=recipe_seq_currented, text_section_list=section_list
                )

                return LlmTaskResponse(
                    task_id=task_id,
                    task_type=LlmTaskType.DOC_UPDATE,
                    task_status=LlmTaskStatus.COMPLETED
                )

            
            has_merge_section = request.has_merge_section
            
            text_update_list = []
            # merge_section 있으면 병합 여부를 체크함
            if has_merge_section:
                
                # LLM이 생성한 대체 텍스트 리스트
                generated_text_list = TypeAdapter(List[GeneratedTextItem]).validate_python(log.ai_output)
                # 사용자가 선택한 문서 리스트
                recipe_seq_list_selected = request.recipe_seq_list_selected

                merge_proposal_target_recipe_list = log.input_data.get("merge_proposal_target_recipe_list")

                for recipe_seq_selected in recipe_seq_list_selected:

                    merge_recipe = next((item for item in merge_proposal_target_recipe_list if item.get("recipe_seq") == recipe_seq_selected), None)

                    if not merge_recipe:
                        raise ValueError(f"merge_recipe 없음")

                    for text_seq in merge_recipe.get("text_seq_list"):

                        generated_text = next((item for item in generated_text_list if item.text_seq == text_seq), None)
                        if not generated_text:
                            raise ValueError(f"generated_text 없음")
                        
                        text_update_list.append(
                            GeneratedTextItem(
                                text_seq=text_seq,
                                section_seq=generated_text.section_seq,
                                original_text=generated_text.original_text,
                            )
                        )

            # 업데이트 저장
            final_recipe_seq = await self.mixed_repo.save_document_update(
                recipe_seq_currented, 
                section_list, 
                text_update_list, 
                self.user.user_seq,
                title=request.title
            )
            
            return LlmTaskResponse(
                task_id=task_id,
                task_type=LlmTaskType.DOC_UPDATE,
                task_status=LlmTaskStatus.COMPLETED,
                recipe_seq=final_recipe_seq  # 생성/업데이트된 recipe_seq 반환
            )
        except ValueError as e:
            print(f"유효하지 않은 값이 있습니다: {e}")
            raise e
        except Exception as e:
            print(f"알 수 없는 에러가 발생했습니다: {e}")
            raise e
            
    async def rename_document(self, recipe_seq: int, title: str):
        """
        [문서 이름 변경]
        중복된 이름이 있는지 확인 후 변경
        """
        self._check_dependencies()
        
        # 1. 중복 체크
        existing_doc = await self.recipe_repo.get_by_title(title)
        if existing_doc:
            # 자기 자신의 이름이면 무시 (변경 사항 없음)
            if existing_doc.recipe_seq == recipe_seq:
                return
            raise ValueError(f"'{title}'은(는) 이미 존재하는 문서 이름입니다.")
            
        # 2. 이름 변경
        updated = await self.recipe_repo.update_title(recipe_seq, title)
        if not updated:
            raise ValueError("문서를 찾을 수 없거나 변경에 실패했습니다.")

    async def delete_document(self, recipe_seq: int) -> bool:
        """
        문서 삭제
        
        Args:
            recipe_seq: 삭제할 문서의 recipe_seq
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            ValueError: recipe_seq가 존재하지 않는 경우
            PermissionError: 사용자에게 삭제 권한이 없는 경우
        """
        self._check_dependencies()
        
        # 1. recipe_seq 존재 확인
        doc_recipe = await self.recipe_repo.get_by_seq(recipe_seq)
        if not doc_recipe:
            raise ValueError(f"Recipe {recipe_seq} not found")
        
        # 2. 권한 확인 - R_ADMIN 또는 R_EDITOR만 삭제 가능
        has_permission = await self.mixed_repo.check_user_recipe_permission(
            user_seq=self.user.user_seq,
            recipe_seq=recipe_seq,
            required_roles=[DocRecipeRole.R_ADMIN, DocRecipeRole.R_EDITOR]
        )
        
        if not has_permission:
            raise PermissionError(
                f"User {self.user.user_seq} does not have permission to delete recipe {recipe_seq}"
            )
        
        # 3. 트랜잭션 기반 삭제 실행
        await self.mixed_repo.delete_document_transaction(recipe_seq)
        
        return True


    async def document_search(self, search_word, limit: int=100, type="cloud") :

        masking_tool = InfoMask(self.token_repo, self.pattern_repo)

        recipe_list = await self.search_engine.semantic_search(search_word, limit, self.user.user_seq)
        recipe_responses = []
        for recipe in recipe_list :
            response_detail = {}
            response_detail["id"] = recipe.recipe_seq
            response_detail["title"] = recipe.title
            response_detail["type"] = type
            preview_text = await self.search_engine.select_preview(search_word, recipe.recipe_seq)
            response_detail["preview"] = await masking_tool.decrypt_text(preview_text)
            recipe_responses.append(response_detail)

        return recipe_responses