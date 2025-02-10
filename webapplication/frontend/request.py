import os

import requests
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.environ['BACKEND_URL']


def create_report_task(user_id: str, stock_code: str, investor_type: str):
    url = BACKEND_URL + "/api/v1/invest/"

    data = {
        "user_id": user_id,
        "stock_code": stock_code,
        "investor_type": investor_type
    }

    response = requests.put(url, json=data)
    return response.json()


def get_report(task_id: str, user_id: str):
    url = BACKEND_URL + f"/api/v1/invest/report"

    params = {
        "task_id": str(task_id),
        "user_id": str(user_id)
    }

    response = requests.get(url, params=params)
    return response.json()
