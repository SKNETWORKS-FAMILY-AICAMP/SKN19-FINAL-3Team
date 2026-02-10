// ============================================================================
// 공통 타입 정의
// ============================================================================

/** 로컬 문서 */
export interface Document {
    doc_name: string
    doc_type: string
    content: string
}

/** 클라우드 문서 목록 응답 */
export interface CloudDocumentResponse {
    recipe_seq: number
    doc_type_code: string
    title: string | null
    text: string | null
    recipe_value: string
    created_at: string
    updated_at: string
}

/** 클라우드 문서 상세 응답 */
export interface CloudDocumentDetail {
    recipe_seq: number
    doc_type_code: string
    title: string
    text: string
    recipe_value: Record<string, unknown>
    created_at: string
    updated_at: string
}

/** 작업 상태 응답 */
export interface TaskStatusResponse {
    task_id: string
    task_type: string
    task_status: string
}

/** 인덱싱 요청 */
export interface IndexRequest {
    recipe_seq: number
    text: string
}

/** 인덱싱 응답 */
export interface IndexResponse {
    task_id: string
    task_type: string
    task_status: string
}

/** 문서 섹션 */
export interface Section {
    is_changed: boolean
    original_text: string
    section_seq: number
    text_seq: number
}

/** 제안 문서 */
export interface ProposalDocument {
    recipe_seq: number
    title: string
    sections: Section[]
}

/** 제안 응답 */
export interface ProposalResponse {
    target_recipes: ProposalDocument[]
    task_id: string
}

// ============================================================================
// 병합(Merge) 관련 타입
// ============================================================================

/** 병합 텍스트 */
export interface MergeText {
    is_changed: boolean
    text_seq: number
    section_seq: number
    text_before: string
    text_after: string | null
}

/** 병합 레시피 */
export interface MergeRecipe {
    recipe_seq: number
    is_merge: boolean
    title: string | null
    doc_type_code: string | null
    texts: MergeText[]
}

/** 병합 선택 응답 */
export interface MergeSelectionResponse {
    task_id: string
    recipes: MergeRecipe[]
}
