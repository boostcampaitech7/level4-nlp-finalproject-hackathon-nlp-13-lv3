import uvicorn
import mojito
import os
import pandas as pd
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException


app = FastAPI()

# 환경변수에서 인증 정보 로드
load_dotenv()
broker = mojito.KoreaInvestment(
    api_key=os.getenv('KOREAINVESTMENT_KEY'),
    api_secret=os.getenv('KOREAINVESTMENT_SECRET'),
    acc_no=os.getenv('KOREAINVESTMENT_ACC_NO')
)

target_stocks = {
    "네이버": "035420",
    "크래프톤": "259960",
    "CJ제일제당": "097950",
    "LG화학": "051910",
    "SK케미칼": "285130",
    "SK하이닉스": "000660",
    "롯데렌탈": "089860",
    "엘앤에프": "066970",
    "카카오뱅크": "323410",
    "한화솔루션": "009830"
}

def resolve_stock_code(identifier: str) -> tuple:
    """입력값을 종목코드로 변환 (회사명/코드 모두 허용)"""
    if identifier in target_stocks:
        return identifier, target_stocks[identifier]
    
    for name, code in target_stocks.items():
        if code == identifier:
            return name, code
            
    raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다")

@app.get("/hoga/{identifier}")
async def get_realtime_hoga(identifier: str):
    company, stock_code = resolve_stock_code(identifier)
    
    # 호가 데이터 요청
    resp = requests.get(
        url=f"{broker.base_url}/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
        headers={
            "authorization": broker.access_token,
            "appkey": broker.api_key,
            "appsecret": broker.api_secret,
            "tr_id": "FHKST01010200"
        },
        params={
            "FID_COND_MRKT_DIV_CODE": 'J',
            "FID_INPUT_ISCD": stock_code
        }
    )
    
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="호가 데이터 조회 실패")

    raw_data = resp.json().get('output1', {})
    
    # 데이터 구조화
    return {
        "company": company,
        "code": stock_code,
        "timestamp": raw_data.get('aspr_acpt_hour'),
        "asks": [{"price": raw_data[f'askp{i}'], "volume": raw_data[f'askp_rsqn{i}']} for i in range(1,11)],
        "bids": [{"price": raw_data[f'bidp{i}'], "volume": raw_data[f'bidp_rsqn{i}']} for i in range(1,11)],
        "total_ask": raw_data.get('total_askp_rsqn'),
        "total_bid": raw_data.get('total_bidp_rsqn')
    }

if __name__ == "__main__":
    uvicorn.run("utils:app", port=7840, reload=True)