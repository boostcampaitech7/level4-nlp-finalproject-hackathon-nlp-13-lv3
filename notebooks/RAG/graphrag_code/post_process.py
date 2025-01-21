# post_process.py
import re
import pandas as pd

def extract_sources_numbers(text: str):
    """
    'Sources (2)', 'sources(2)', 'Sources (2,3)' 같은 패턴에서
    숫자 목록을 뽑아서 중복 없이 set으로 반환합니다.
    """
    pattern = r"Sources\s*\(([\d,]+)\)"
    matches = re.findall(pattern, text, re.IGNORECASE)  # 모든 매치를 찾음

    source_ids = set()
    for match_str in matches:
        # '2,3' 형태를 쉼표로 분리해 각각 int 변환 후 추가
        numbers = [int(x) for x in match_str.split(",")]
        source_ids.update(numbers)  # set에 추가
    
    return source_ids

def filter_text_by_ids(dataframe: pd.DataFrame, ids: list):
    """
    DataFrame에서 'id' 열이 주어진 ids 목록에 포함된 행만 필터링하여
    해당 행들의 'text' 열값을 리스트로 반환합니다.
    """
    """
    DataFrame에서 'id' 열이 주어진 ids 목록에 포함된 행만 필터링하여
    해당 행들의 'text' 열값을 리스트로 반환합니다.
    """
    # 1) 필요하다면, df['id']를 int로 변환
    dataframe['id'] = dataframe['id'].astype(int)
    
    # 2) ids도 int 리스트로 변환 (이미 int라면 생략 가능)
    ids = [int(x) for x in ids]

    # 3) 필터링
    filtered_texts = dataframe[dataframe['id'].isin(ids)]['text']
    
    return filtered_texts.tolist()
