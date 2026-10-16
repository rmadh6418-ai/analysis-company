import requests
import json
import time

# 1. 수집할 관심 종목 리스트 (HTML에 있던 종목들)
TARGET_STOCKS = {
    "삼성전자": "005930", "SK하이닉스": "000660", "현대로템": "064350", 
    "HD현대마린엔진": "071970", "셀트리온": "068270", "SK바이오팜": "326030",
    "유한양행": "000100", "오스코텍": "039200", "리노공업": "058470"
    # 필요하신 KOSPI/KOSDAQ 종목들을 여기에 계속 추가하시면 됩니다.
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

quant_data = {}

print("🚀 주식 데이터 수집 시작...")

for name, ticker in TARGET_STOCKS.items():
    print(f"[{name}] 수집 중...")
    stock_info = {
        "name": name,
        "price": "N/A", "changeRate": "0.00%", "direction": "FLAT",
        "marketCap": "-", "foreignRate": "-", "per": "-", "fwdPer": "-", "pbr": "-", "roe": "-",
        "finance": {}
    }
    
    try:
        # 1. 실시간 현재가 (Basic)
        res_basic = requests.get(f"https://m.stock.naver.com/api/stock/{ticker}/basic", headers=headers).json()
        stock_info["price"] = res_basic.get("closePrice", "N/A")
        fluctuation = float(res_basic.get("fluctuationsRatio", 0))
        if fluctuation > 0:
            stock_info["direction"] = "UP"
            stock_info["changeRate"] = f"▲ +{fluctuation}%"
        elif fluctuation < 0:
            stock_info["direction"] = "DOWN"
            stock_info["changeRate"] = f"▼ {fluctuation}%"

        # 2. 투자지표 (Integration)
        res_integ = requests.get(f"https://m.stock.naver.com/api/stock/{ticker}/integration", headers=headers).json()
        for info in res_integ.get("totalInfos", []):
            key = info.get("key", "")
            val = info.get("value", "-")
            if "시총" in key or key == "marketValue": stock_info["marketCap"] = val
            elif "외인소진율" in key or key == "foreignRate": stock_info["foreignRate"] = val
            elif key in ["PER", "per"]: stock_info["per"] = val.replace("배", "")
            elif key in ["추정PER", "cnsPer"]: stock_info["fwdPer"] = val.replace("배", "")
            elif key in ["PBR", "pbr"]: stock_info["pbr"] = val.replace("배", "")
            elif key in ["ROE", "roe"]: stock_info["roe"] = val
            
        # 3. 재무제표 (Annual)
        res_finance = requests.get(f"https://m.stock.naver.com/api/stock/{ticker}/finance/annual", headers=headers).json()
        fin_info = res_finance.get("financeInfo", {})
        
        years = fin_info.get("dateList", ["-", "-", "-", "-"])
        stock_info["finance"]["years"] = years[-4:] # 최근 4년
        
        def get_fin_data(title):
            for item in fin_info.get("itemLists", []):
                if title in item.get("title", ""):
                    return item.get("columns", [])[-4:]
            return ["-", "-", "-", "-"]
            
        stock_info["finance"]["revs"] = get_fin_data("매출액")
        stock_info["finance"]["ops"] = get_fin_data("영업이익")
        stock_info["finance"]["opMs"] = get_fin_data("영업이익률")
        stock_info["finance"]["npMs"] = get_fin_data("순이익률")
        stock_info["finance"]["debts"] = get_fin_data("부채비율")
        stock_info["finance"]["epss"] = get_fin_data("EPS")
        
    except Exception as e:
        print(f"오류 발생 ({name}): {e}")
        
    quant_data[ticker] = stock_info
    time.sleep(0.5) # 네이버 서버 과부하 방지 (매우 중요)

# JSON 파일로 저장
with open("quant_data.json", "w", encoding="utf-8") as f:
    json.dump(quant_data, f, ensure_ascii=False, indent=2)

print("✅ 데이터 수집 완료! quant_data.json 저장됨.")
