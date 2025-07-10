1. **개요**
---
비즈니스 사용자나 SQL에 익숙하지 않은 현업 담당자가 자연어로 데이터를 요청하면
Azure OpenAI를 활용해 SQL 쿼리를 자동 생성하고, Azure SQL Database에서 데이터를 조회하여 보고서 형태로 시각화 및 다운로드할 수 있도록 도움을 줌
* CSV 파일 업로드 및 Azure Blob Storage 저장
* 업로드된 데이터를 Azure SQL Database에 테이블로 저장
* 자연어로 질의 → GPT를 통해 SQL 쿼리 생성
* 생성된 쿼리 실행 및 결과 시각화
* 결과 CSV 다운로드
* 세션 초기화 및 업로드된 파일 삭제 기능

2. **사용한 Azure 서비스**
---
* Azure Blob Storage	업로드된 CSV 파일을 저장
* Azure SQL Database	CSV 데이터를 테이블로 저장하고 쿼리 실행
* Azure OpenAI	자연어 질의를 SQL 쿼리로 변환


3. **전체적인 AI 흐름도**
---
![Mermaid-preview](https://github.com/user-attachments/assets/f625a6ee-f0f8-4457-be7f-9ebcbd437f66)


4. **해당 AI 사용의 기대 효과**
---
|항목|기대 효과|
|---|---|
|비즈니스 사용자 접근성 향상|SQL을 몰라도 자연어로 원하는 데이터를 조회 가능|
|업무 효율성 증가|IT 부서에 쿼리 요청 없이 실시간으로 데이터 확인 가능|
|데이터 기반 의사결정 강화|빠른 데이터 접근으로 인사이트 도출 시간 단축|
|운영 자동화	반복적인 보고서|생성 업무 자동화 가능|
|보안 및 통제 유지|Azure 기반으로 보안 및 접근 제어 용이|


https://user09-web-001.azurewebsites.net/

tc
1) 학생별로 과목별 평균 점수를 보여줘.
2) 학년별로 평균 점수가 가장 높은 과목은 뭐야?
3) 각 반(Class)별 평균 점수를 계산해서 높은 순으로 정렬해서 보여줘.
