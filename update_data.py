import yfinance as yf
import json
from datetime import datetime

# 데이터 수집 대상 종목 리스트 (한국 주식은 코스피 .KS, 코스닥 .KQ 부착)
TICKERS = {
    "삼성전자": "005930.KS",
    "현대로템": "064350.KS",
    "셀트리온": "068270.KS",
    "SK바이오팜": "326030.KS",
    "유한양행": "000100.KS",
    "오스코텍": "039200.KQ",
    "리노공업": "053980.KQ",
    "HD현대마린엔진": "071970.KS"
}

def safe_get(info_dict, key, default="-"):
    """데이터 누락 방지용 안전 함수"""
    val = info_dict.get(key)
    return default if val is None else val

def fetch_stock_data():
    results = {}
    
    for name, ticker in TICKERS.items():
        try:
            print(f"[{name}] 데이터 수집 중...")
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # yfinance 특성상 영업이익이 직접 나오지 않으면 매출액*영업이익률로 추산
            rev_raw = safe_get(info, "totalRevenue", 0)
            op_margin_raw = safe_get(info, "operatingMargins", 0)
            
            if rev_raw != "-" and op_margin_raw != "-":
                op_profit_est = rev_raw * op_margin_raw
            else:
                op_profit_est = 0
            
            results[name] = {
                "name": name,
                "ticker": ticker,
                "currentPrice": safe_get(info, "currentPrice", 0),
                "targetPrice": safe_get(info, "targetMeanPrice", 0),
                "per": round(safe_get(info, "trailingPE", 0), 2) if safe_get(info, "trailingPE", 0) != "-" else "-",
                "pbr": round(safe_get(info, "priceToBook", 0), 2) if safe_get(info, "priceToBook", 0) != "-" else "-",
                "eps": safe_get(info, "trailingEps", 0),
                "roe": round(safe_get(info, "returnOnEquity", 0) * 100, 2) if safe_get(info, "returnOnEquity", 0) != "-" else "-",
                "peg": safe_get(info, "pegRatio", "-"),
                "debtRatio": round(safe_get(info, "debtToEquity", 0), 2) if safe_get(info, "debtToEquity", 0) != "-" else "-",
                "revenue": round(rev_raw / 100000000, 0) if rev_raw != "-" else "-",
                "operatingProfit": round(op_profit_est / 100000000, 0) if op_profit_est else "-",
                "operatingMargin": round(op_margin_raw * 100, 2) if op_margin_raw != "-" else "-",
                "netMargin": round(safe_get(info, "profitMargins", 0) * 100, 2) if safe_get(info, "profitMargins", 0) != "-" else "-",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            print(f"[{name}] 수집 실패: {e}")
            continue

    # JSON 파일로 저장 (한글 깨짐 방지)
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("✅ data.json 업데이트 완료!")

if __name__ == "__main__":
    fetch_stock_data()
