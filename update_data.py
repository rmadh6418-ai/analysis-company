import requests
import json
import time

# 대시보드 UI에 있는 KOSPI 200, KOSDAQ 150 관심 종목 리스트
TARGET_STOCKS = {
    "LG화학":"051910", "S-Oil":"010950", "SK이노베이션":"096770", "롯데케미칼":"011170", "SK가스":"018670", "한국가스공사":"036460", "한화솔루션":"009830",
    "LG에너지솔루션":"373220", "POSCO홀딩스":"005490", "포스코퓨처엠":"003670", "삼성SDI":"006400", "엘앤에프":"066970", "코스모신소재":"005070",
    "HD현대중공업":"329180", "한화오션":"042660", "삼성중공업":"010140", "HD한국조선해양":"009540", "HD현대마린엔진":"071970", "HMM":"011200",
    "삼성전자":"005930", "SK하이닉스":"000660", "삼성전기":"009150", "LG이노텍":"011070", "한미반도체":"042700", "LG전자":"066570",
    "현대차":"005380", "기아":"000270", "현대모비스":"012330", "현대글로비스":"086280", "현대위아":"011210",
    "한화에어로스페이스":"012450", "현대로템":"064350", "한국항공우주":"047810", "한화시스템":"272210", "LIG넥스원":"079550",
    "삼성바이오로직스":"207940", "셀트리온":"068270", "유한양행":"000100", "한미약품":"128940", "SK바이오팜":"326030",
    "KB금융":"105560", "신한지주":"055550", "하나금융지주":"086790", "카카오뱅크":"323410", "삼성물산":"028260",
    "알테오젠":"196170", "HLB":"028300", "삼천당제약":"000250", "리가켐바이오":"141080", "에스티팜":"237690", "오스코텍":"039200",
    "휴젤":"145020", "클래시스":"214150", "실리콘투":"257720", "파마리서치":"214450", "제이시스메디칼":"287410",
    "HPSP":"403870", "리노공업":"058470", "주성엔지니어링":"036930", "이오테크닉스":"039030", "동진쎄미켐":"005290",
    "레인보우로보틱스":"277810", "로보티즈":"108490", "에스에프에이":"056190", "휴림로봇":"090710"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

quant_data = {}
print("🚀 주식 데이터 수집 시작...")

for name, ticker in TARGET_STOCKS.items():
    print(f"[{name}] 수집 중...")
    stock_info = {
        "name": name, "price": "N/A", "changeRate": "0.00%", "direction": "FLAT",
        "marketCap": "-", "foreignRate": "-", "per": "-", "fwdPer": "-", "pbr": "-", "roe": "-",
        "finance": {}
    }
    
    try:
        # 1. 실시간 현재가
        res_basic = requests.get(f"https://m.stock.naver.com/api/stock/{ticker}/basic", headers=headers).json()
        stock_info["price"] = res_basic.get("closePrice", "N/A")
        fluctuation = float(res_basic.get("fluctuationsRatio", 0))
        if fluctuation > 0:
            stock_info["direction"] = "UP"
            stock_info["changeRate"] = f"▲ +{fluctuation}%"
        elif fluctuation < 0:
            stock_info["direction"] = "DOWN"
            stock_info["changeRate"] = f"▼ {abs(fluctuation)}%"

        # 2. 투자지표 (PER, PBR 등)
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
            
        # 3. 연간 재무제표
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
        print(f"❌ 오류 발생 ({name}): {e}")
        
    quant_data[ticker] = stock_info
    time.sleep(0.5) # IP 차단 방지를 위한 딜레이

with open("quant_data.json", "w", encoding="utf-8") as f:
    json.dump(quant_data, f, ensure_ascii=False, indent=2)

print("✅ 데이터 수집 완료! quant_data.json 저장됨.")
