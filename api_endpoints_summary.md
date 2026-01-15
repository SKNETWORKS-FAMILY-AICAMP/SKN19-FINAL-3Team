### 1. 문서 저장 (클라우드)

문서를 시스템에 저장(등록)하는 첫 단계는 '문서 분할' 작업을 요청하는 것입니다. 이 요청이 성공하면 백그라운드에서 문서 처리 작업이 시작됩니다.

- **API Endpoint:** `POST /tasks/doc-reg`
- **설명:** 텍스트를 전달하여 문서 처리(분할, 인덱싱 등) 작업을 시작합니다. `task_type`으로 `doc-reg`를 사용합니다.
- **Input Format (`LlmTaskRequest`)**
  ```json
  {
    "text": "여기에 저장할 문서의 전체 원본 텍스트를 입력합니다."
  }
  ```
- **Output Format (`LlmTaskResponse`)**
  성공적으로 작업을 요청하면, 추적에 필요한 `task_id`와 현재 작업 상태를 받게 됩니다.
  ```json
  {
    "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "task_type": "DOC_REG",
    "task_status": "PENDING"
  }
  ```

### 2. 문서 리스트 조회

저장된 문서들의 목록은 '섹션(Section)' 목록을 조회하여 얻을 수 있습니다. 여기서 `index_seq`는 문서들을 묶는 그룹 ID라고 생각할 수 있습니다.

- **API Endpoint:** `GET /sections?index_seq={index_seq}`
- **설명:** 특정 인덱스(`index_seq`)에 속한 문서(섹션) 목록을 조회합니다.
- **Input Format**
  - `index_seq` (Query Parameter, integer): 조회하려는 문서 그룹의 ID.
  - 예시: `/sections?index_seq=1`
- **Output Format (List of `SectionResponse`)**
  ```json
  [
    {
      "section_seq": 1,
      "index_seq": 1,
      "origin_type_code": "USER_INPUT",
      "essence": "첫 번째 문서의 핵심 내용 요약입니다.",
      "updated_at": "2024-05-21T10:00:00"
    },
    {
      "section_seq": 2,
      "index_seq": 1,
      "origin_type_code": "USER_INPUT",
      "essence": "두 번째 문서의 핵심 내용 요약입니다.",
      "updated_at": "2024-05-21T10:05:00"
    }
  ]
  ```

### 3. 문서 내용 조회

최종적으로 조합된 버전의 문서 내용을 조회합니다. 특정 버전을 지정하거나 최신 버전을 조회할 수 있습니다.

- **API Endpoint:** `POST /view`
- **설명:** '레시피(recipe)'를 기반으로 최종 문서를 조립하여 그 내용을 반환합니다. `recipe_seq`를 지정하지 않으면 가장 최신 버전의 문서를 조회합니다.
- **Input Format (`DocumentViewRequest`)**
  - 최신 문서 조회 시:
    ```json
    {}
    ```
  - 특정 버전 문서 조회 시:
    ```json
    {
      "recipe_seq": 123
    }
  ```
- **Output Format (`DocumentViewResponse`)**
  ```json
  {
    "recipe_seq": 123,
    "content": "레시피에 따라 여러 텍스트 조각들이 합쳐진 최종 문서의 전체 내용입니다..."
  }
  ```

### 4. 작업 상태 체크

'문서 저장' 요청 후, 해당 작업이 어떻게 진행되고 있는지 상태를 확인할 수 있습니다.

- **API Endpoint:** `GET /tasks/{task_type}/{task_id}/status`
- **설명:** `task_type`과 `task_id`를 이용해 백그라운드 작업의 현재 상태(대기, 진행 중, 완료, 실패 등)를 확인합니다.
- **Input Format**
  - `task_type` (Path Parameter, string): 확인하려는 작업의 종류 (예: `DOC_REG`).
  - `task_id` (Path Parameter, UUID): '문서 저장' 시 발급받은 작업 ID.
  - 예시: `/tasks/DOC_REG/a1b2c3d4-e5f6-7890-1234-567890abcdef/status`
- **Output Format (`LlmTaskResponse`)**
  - 작업이 완료되었을 경우:
    ```json
    {
      "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "task_type": "DOC_REG",
      "task_status": "COMPLETE"
    }
    ```
  - `task_status`의 종류: `PENDING`, `IN_PROGRESS`, `COMPLETE`, `FAILURE` 등이 있습니다.