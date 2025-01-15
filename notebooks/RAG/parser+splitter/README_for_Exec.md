## 개발환경 세팅 

1. 파일들을 프로젝트 디렉토리 폴더에 두세요.

2. `cd {프로젝트 디렉토리(pyproject.toml이 있는 곳)}` 입력해서 프로젝트 디렉토리로 변경해줍니다. 

3. 파이썬 버전을 3.11.xx로 맞춰주세요.

3. Poetry 라이브러리 설치를 해줍니다.
    - `curl -sSL https://install.python-poetry.org | python3 -`
    - 설치된 Poetry 확인 `poetry --version`

3. `poetry install` 입력합니다. 
- 만약 파이썬 버전 문제가 발생하면 3.11.xx 버전으로 진행해주세요.
- 해당 버전으로 주피터 노트북에서 사용할 수 있게 kernel에 등록해주세요.
    - `python -m ipykernel install --user --name RAG-PARSER --display-name "pyenv 3.11.9"`

4. `poetry shell`로 가상환경을 활성화 시켜줍니다.

5. .env 파일을 만들고 아래의 API를 설정해줍니다.
```
OPENAI_API_KEY = "YOUR_API_KEY"
UPSTAGE_API_KEY = "YOUR_API_KEY"
LANGCHAIN_API_KEY = "YOUR_API_KEY"
LANGCHAIN_TRACING_V2 = true
LANGCHAIN_ENDPOINT = https://api.smith.langchain.com
LANGCHAIN_PROJECT = NLP13-Parser
```

6. RAG_parser+splitter.ipynb 파일을 순서대로 실행시켜줍니다.
