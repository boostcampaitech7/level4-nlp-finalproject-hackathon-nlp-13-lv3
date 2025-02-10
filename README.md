<div align='center'>

  # 🏆 NLP 프로젝트 : 멀티 AI 에이전트 기반 주식 매매 관리 서비스

</div>

## 프로젝트 개요

이 프로젝트는 AI 멀티 에이전트를 활용하여 주식 자동 매매 서비스를 개발하는 것을 목표로 합니다.   
사람이 직접 정보를 모으고 투자 전략을 세우는 과정을 단축시켜 주식 투자자들에게 고도의 품질과 빠른 분석 결과를 제공하는 시스템을 구축하였습니다.

이 시스템을 구축하기 위해 AI Multi-Agent 기반으로 인프라를 구성하고 기획했습니다.
각 에이전트는 특정한 전략을 기반으로 각 분야에 적합한 전략을 통해 주식에 대해 다양한 각도로 분석하여 분석가가 통합하는 과정을 거쳐 리포트가 투자자에게 제공됩니다.

각 에이전트는 약점인 최신 정보에 대한 정확성과 할루시네이션을 방지하기 위해 RAG 시스템을 활용했습니다.
증권사에서 작성한 기업 분석 보고서와 웹 검색을 기반으로 보다 정확한 답변을 구현했습니다.


<br><br>




## Requirements
- Python 3.11.9

그 외의 요구 사항은 각 구성 요소마다 다릅니다. 각 요구사항은 하위 폴더에서 확인하실 수 있습니다.

## System Architecture




## 📁 프로젝트 구조

### 폴더 구조 설명
```sh
project-name/
│
├── notebooks/                # 다양한 실험 및 프로토타입(RAG 파이프라인, 앱 템플릿) 구현현
│
├── embeddingserver/          # 임베딩을 수행 후 중개하는 서버입니다.
│   └── app/                  # 서버 어플리케이션 스크립트
│
├── manageserver/             # 주식 매매 관리, 보고서 전송 등을 담당합니다.
│   └── app/                  # 서버 어플리케이션 스크립트
│
├── agentserver/              # multi-agent를 활용한 보고서 산출을 담당합니다.
│   ├── app                   # 서버 어플리케이션 스크립트
│   ├── LangGraph.py          # langraph를 활용한 에이전트 파이프라인 스크립트트
│   └── worker                # 스케줄링 워커 스크립트 폴더
│     
├── webapplication            # 웹 서버 어플리에키션
|   ├── frontend              # 웹 프론트엔드 어플리케이션(streamlit 기반반)
│   └── backend               # 웹 백엔드 어플리케이션(fastapi, nginx 구성 파일도 존재)

```


## Contributing
프로젝트에 기여하고 싶으시면 jilp1598.git@gmail.com 에 연락을 주세요.  
이슈를 발견하셨으면 [issue tracker](https://github.com/boostcampaitech7/level2-nlp-generationfornlp-nlp-13-lv3/issues/new)에 리포트해주세요.


If you'd like to contribute to this project, please contact us at jilp1598.git@gmail.com.  
If you find any issues, please report them in the [issue tracker](https://github.com/boostcampaitech7/level2-nlp-generationfornlp-nlp-13-lv3/issues/new).

## Contact

기타 질문 및 토론 사항은 Github Discussion에 남겨주시면 됩니다.  

For any other questions or discussion topics, please leave them in the GitHub Discussion.


- **Github Discussion** : [Gihub Discussion](https://github.com/boostcampaitech7/level2-nlp-generationfornlp-nlp-13-lv3/discussions)

## Credit

### 👨‍💻 Contributors

 
| 김현서 [<img src="./docs/github_official_logo.png" width=18 style="vertical-align:middle;" />](https://github.com/kimhyeonseo0830) | 이재룡 [<img src="./docs/github_official_logo.png" width=18 style="vertical-align:middle;" />](https://github.com/So1pi) | 이정인 [<img src="./docs/github_official_logo.png" width=18 style="vertical-align:middle;" />](https://github.com/unsolomon) | 이현풍 [<img src="./docs/github_official_logo.png" width=18 style="vertical-align:middle;" />](https://github.com/P-oong) | 임한택 [<img src="./docs/github_official_logo.png" width=18 style="vertical-align:middle;" />](https://github.com/LHANTAEK) | 최현우 [<img src="./docs/github_official_logo.png" width=18 style="vertical-align:middle;" />](https://github.com/pica-git0) |
|:-:|:-:|:-:|:-:|:-:|:-:|
| ![김현서](https://avatars.githubusercontent.com/u/176917012?v=4) | ![이재룡](https://avatars.githubusercontent.com/u/173986541?v=4) | ![이정인](https://avatars.githubusercontent.com/u/180611698?v=4) | ![이현풍](https://avatars.githubusercontent.com/u/115058644?v=4) | ![임한택](https://avatars.githubusercontent.com/u/143519383) | ![최현우](https://avatars.githubusercontent.com/u/176974888?v=4) |


### 👼 role


|팀원   | 역할 |
|------| --- |
| 김현서 | 파인튜닝 라이브러리 탐색, 모델 탐색, 하이퍼파라미터 실험, 어댑터 병합 실험, 외부 데이터셋 전처리 |
| 이재룡 | 모델 탐색, 모델 경량화, 하드웨어 최적화, 메모리 분석 |
| 이정인 | EDA, 데이터 필터링 및 전처리, 데이터 증강 및 주제 분류, 하이퍼파라미터 실험 |
| 이현풍 | EDA, PDF QA pair 생성, 프롬프트 조합, 힌트 생성 LLM 파인튜닝 시도 |
| 임한택 | EDA, 데이터 필터링 및 전처리, 데이터 증강, 모델 탐색 및 실험, LoRA 및 모델 하이퍼파라미터 최적화, 파인튜닝 실험, 앙상블 실험    |
| 최현우 | EDA, 데이터 필터링 및 전처리, 모델 실험 환경 구성, 코드베이스 개선 및 사용성 향상, 실험 수행 및 보고 |




### Sponsors
<a href="https://boostcamp.connect.or.kr/program_ai.html"><img src="docs/boostai_logo.png" alt="boostai_logo" width="250px"></a>
