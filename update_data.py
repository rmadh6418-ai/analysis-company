import json
import time
from datetime import datetime
import pandas as pd

# 한국 주식 수집을 위한 라이브러리 (requirements.txt 에 추가 필요)
# pip install finance-datareader pykrx requests
import FinanceDataReader as fdr
from pykrx import stock

# 수집할 기업 리스트 (이미지 3번 참조하여 주요 종목 추가)
COMPANIES = [
    "삼성전자", "현대로템", "셀트리온", "SK바이오팜", "유한양행", "오스코텍", "리노공업", "HD현대마린엔진",
    "LG에너지솔루션", "POSCO홀딩스", "삼성SDI", "에코프로비엠", "에코프로",
    "SK하이닉스", "한미반도체", "현대차", "기아", "NAVER", "카카오", "알테오젠", "HLB"
]

def format_val(val, multiplier=1, decimals=0):
    if pd.isna(val) or val is None:
        return "-"
    try:
        res = float(val) * multiplier
        return round(res, decimals) if decimals > 0 else int(round(res))
    except:
        return "-"

def get_ticker_dict():
    """종목명으로 티커를 찾기 위한 딕셔너리 생성 (코스피 + 코스닥)"""
    df_krx = fdr.StockListing('KRX')
    # Name을 key로, Code를 value로 하는 딕셔너리
    return dict(zip(df_krx['Name'], df_krx['Code']))

def fetch_stock_data():
    ticker_dict = get_ticker_dict()
    results = {}
    today = datetime.today().strftime("%Y%m%d")

    # pykrx를 이용해 오늘(최근 영업일)의 전체 밸류에이션(PER, PBR, EPS 등) 한 번에 가져오기
    # 주말인 경우를 대비해 가장 최근 영업일 데이터를 가져오도록 합니다.
    try:
        val_df_kospi = stock.get_market_fundamental_by_ticker(date=today, market="KOSPI")
        val_df_kosdaq = stock.get_market_fundamental_by_ticker(date=today, market="KOSDAQ")
        val_df = pd.concat([val_df_kospi, val_df_kosdaq])
    except:
        # 혹시 오늘 데이터가 안 올라왔으면 어제 날짜로 시도
        yesterday = (datetime.today() - pd.Timedelta(days=1)).strftime("%Y%m%d")
        val_df_kospi = stock.get_market_fundamental_by_ticker(date=yesterday, market="KOSPI")
        val_df_kosdaq = stock.get_market_fundamental_by_ticker(date=yesterday, market="KOSDAQ")
        val_df = pd.concat([val_df_kospi, val_df_kosdaq])

    for name in COMPANIES:
        try:
            ticker = ticker_dict.get(name)
            if not ticker:
                print(f"[{name}] 티커를 찾을 수 없습니다.")
                continue
                
            print(f"[{name} - {ticker}] 데이터 수집 중...")
            
            # 1. 현재가 수집 (FinanceDataReader)
            df_price = fdr.DataReader(ticker, start=(datetime.today() - pd.Timedelta(days=7)).strftime("%Y-%m-%d"))
            current_price = df_price['Close'].iloc[-1]

            # 2. 가치 지표 수집 (pykrx 밸류에이션 데이터)
            per = "-"
            pbr = "-"
            eps = "-"
            if ticker in val_df.index:
                per = val_df.loc[ticker, "PER"]
                pbr = val_df.loc[ticker, "PBR"]
                eps = val_df.loc[ticker, "EPS"]
                # 0으로 나오면 N/A 처리
                per = "-" if per == 0 else per
                pbr = "-" if pbr == 0 else pbr
                eps = "-" if eps == 0 else eps

            # 3. 재무 데이터 (OpenDart나 네이버 크롤링이 필요하지만 정적 웹 특성상 간이 추정)
            # 완벽한 재무 데이터는 API 한계가 있으므로 모닝스타 해자 로직이 작동하도록 임의 방어 코드 적용
            # 실무에서는 이 부분을 본인의 네이버 크롤링 로직으로 교체하시는 것을 권장합니다.
            
            results[name] = {
                "name": name,
                "ticker": ticker,
                "currentPrice": int(current_price),
                "targetPrice": "-", # 증권사 컨센서스는 별도 유료 API 필요
                "per": format_val(per, 1, 2),
                "pbr": format_val(pbr, 1, 2),
                "eps": format_val(eps),
                "roe": format_val(pbr / per * 100 if per != "-" and pbr != "-" else "-", 1, 2), # ROE = PBR/PER 추산
                "peg": "-",
                "debtRatio": "-",
                "revenue": "-",
                "operatingProfit": "-",
                "operatingMargin": "-",
                "netMargin": "-",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            time.sleep(0.5) # 서버 과부하 방지
            
        except Exception as e:
            print(f"[{name}] 수집 실패: {e}")
            continue

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("✅ data.json 업데이트 완료!")

if __name__ == "__main__":
    fetch_stock_data()
