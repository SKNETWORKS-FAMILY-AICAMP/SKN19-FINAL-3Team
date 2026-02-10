# AI Server 테스트 및 실행 가이드

## **먼저, Miro에 그려진 AI Server 로직을 먼저 확인하는 것을 추천**

## 1. 모델 및 데이터 세팅

### 모델 세팅
1. ai_server/app 하위에 model_data 폴더 생성
2. 공유 드라이브에서 gemma-2b-summary-model, paragraph_boundaryminilm 을 다운로드 
3. ai_server/app/model_data 폴더 하위에 해당 두 모델을 import
4. 폴더나 경로를 변경하고 싶다면, engine.py 에서 SECTIONZE_MODEL_PATH와 SUMMARY_MODEL_PATH를 수정

### 테스트 데이터 세팅

현재는 category_list가 없어서 제대로 불러오지 못하고 있는 상황
1. 현재는 ai_server/app/data/categories_with_vectors.json에 들어있는 데이터를 사용
    - 위 데이터를 사용하고 싶지 않다면, category_list를 추가하고, engine.DocTools.create_index 함수의 input_test_data 인자를 False로 설정

현재 DB에 들어간 데이터가 없어 임시 데이터를 직접 변수에 할당
1. worker.py의 before_section 변수에 내부용_기획서.md의 데이터가 들어있음
    - 해당 데이터를 기반으로 테스트 가능
2. get_before_section 가 정상적으로 동작하게 되면, 해당 변수는 빈 리스트로 선언

### 환경
1. create_essence는 환경에 따라 사용하는 모델이 다름
    - cpu 환경인 경우, 모델을 돌리기 어렵기 때문에 gemini-2-flash를 사용해서 같은 작업을 수행
    - cuda 환경인 경우, model_data 폴더에서 파인튜닝된 모델을 가져와서 해당 모델을 사용

