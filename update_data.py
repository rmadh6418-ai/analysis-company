import yfinance as yf
import json
from datetime import datetime

# 데이터 수집 대상 종목 리스트
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

def format_val(val, multiplier=1, decimals=0):
    """데이터 누락(None) 방지 및 안전한 숫자 포맷팅 (소수점 제거 등)"""
    if val is None or val == "":
        return "-"
    try:
        res = float(val) * multiplier
        if decimals > 0:
            return round(res, decimals)
        else:
            return int(round(res)) # 소수점 제거 (정수 반환)
    except (ValueError, TypeError):
        return "-"

def fetch_stock_data():
    results = {}
    
    for name, ticker in TICKERS.items():
        try:
            print(f"[{name}] 데이터 수집 중...")
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 1. 주가 정보 (yfinance 누락 대비 다중 체크)
            current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
            target_price = info.get("targetMeanPrice")
            
            # 2. PER, PBR, EPS (Yahoo API가 한국주식을 종종 누락하므로 직접 계산 보완)
            eps = info.get("trailingEps")
            per = info.get("trailingPE")
            if not per and current_price and eps and eps > 0:
                per = current_price / eps
                
            book_value = info.get("bookValue")
            pbr = info.get("priceToBook")
            if not pbr and current_price and book_value and book_value > 0:
                pbr = current_price / book_value

            # 3. 실적 및 수익성 지표
            rev = info.get("totalRevenue")
            op_margin = info.get("operatingMargins")
            
            # 영업이익이 직접 나오지 않으면 매출액 * 영업이익률로 추산
            op_profit = (rev * op_margin) if (rev and op_margin) else None

            results[name] = {
                "name": name,
                "ticker": ticker,
                "currentPrice": format_val(current_price),
                "targetPrice": format_val(target_price),  # 소수점 절사됨
                "per": format_val(per, 1, 2),
                "pbr": format_val(pbr, 1, 2),
                "eps": format_val(eps),
                "roe": format_val(info.get("returnOnEquity"), 100, 2),
                "peg": format_val(info.get("pegRatio"), 1, 2),
                "debtRatio": format_val(info.get("debtToEquity"), 1, 2),
                "revenue": format_val(rev, 1/100000000, 0), # 억 원 단위 변환
                "operatingProfit": format_val(op_profit, 1/100000000, 0),
                "operatingMargin": format_val(op_margin, 100, 2),
                "netMargin": format_val(info.get("profitMargins"), 100, 2),
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
