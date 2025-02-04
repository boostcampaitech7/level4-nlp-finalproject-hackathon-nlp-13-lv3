from typing import Dict, List, Any
from langchain.agents import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool
from langchain_community.chat_models import ChatOpenAI
import requests

class FinancialReportsAnalysisTool(BaseTool):
    name = "financial_analysis"
    description = """
    주식 투자와 기업 재무제표 분석에 유용한 도구입니다. 
    기업의 재무상태, 실적, 전망, 투자의견 등을 분석할 수 있습니다.
    입력은 자연어 질문 형태여야 합니다.
    """
    api_url: str
    
    def _call(self, query: str) -> Dict[str, Any]:
        try:
            response = requests.post(
                self.api_url,
                json={"query": query},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}

    def _arun(self, query: str) -> Dict[str, Any]:
        # 비동기 실행이 필요한 경우 구현
        raise NotImplementedError("비동기 실행은 지원되지 않습니다.")

class FinancialReportsAnalysisAgent:
    def __init__(
        self, 
        api_url: str = "http://localhost:8000/api/query",
        model: str = "gpt-4o-mini",
        temperature: float = 0.3
    ):
        # Tool 초기화
        self.financial_tool = FinancialReportsAnalysisTool(
            api_url=api_url
        )
        
        # Agent 프롬프트 템플릿
        template = """
        당신은 금융 분석 전문가입니다. 
        주어진 도구를 사용하여 기업 분석과 투자 관련 질문에 답변해야 합니다.

        다음 규칙을 반드시 따르세요:
        1. 모든 수치 데이터는 원본 단위를 그대로 유지할 것
        2. 분석은 객관적 사실에 기반할 것
        3. 불확실한 내용은 명확히 표현할 것
        4. 중요한 리스크 요인을 항상 포함할 것
        5. 최종적으로 주식 투자 관점에서 인사이트를 포함시킬 것

        {chat_history}

        Question: {input}
        {agent_scratchpad}
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["chat_history", "input", "agent_scratchpad"]
        )
        
        # LLM 초기화
        llm = ChatOpenAI(
            model=model,
            temperature=temperature
        )
        
        # Tools 리스트 구성
        tools = [self.financial_tool]
        
        # Agent 생성
        self.agent = create_react_agent(
            llm=llm,
            tools=tools,
            prompt=prompt
        )
        
        # Agent Executor 생성
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True
        )

    async def analyze(self, query: str) -> Dict[str, Any]:
        """
        주어진 쿼리에 대한 금융 분석을 수행합니다.
        
        Args:
            query (str): 분석하고자 하는 질문
            
        Returns:
            Dict[str, Any]: 분석 결과
        """
        try:
            result = await self.agent_executor.ainvoke(
                {"input": query}
            )
            return result
        except Exception as e:
            return {
                "error": f"Analysis failed: {str(e)}",
                "output": None
            }

# 사용 예시
async def main():
    # Agent 초기화
    agent = FinancialReportsAnalysisAgent(
        api_url="http://localhost:8000/api/query"
    )
    
    # 테스트 쿼리
    query = "SK하이닉스의 2024년 분기별 예상 세전 계속사업이익은?"
    
    # 분석 실행
    result = await agent.analyze(query)
    print("Analysis Result:", result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())