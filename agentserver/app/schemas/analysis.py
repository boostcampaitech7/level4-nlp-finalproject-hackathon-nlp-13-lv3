from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    company_name: str
    user_assets: float
    financial_query: str
    investment_persona: str

class AnalysisResponse(BaseModel):
    final_report: str
