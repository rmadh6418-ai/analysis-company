import requests
from bs4 import BeautifulSoup
import json
import time

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
        "peg": "N/A", "pegDesc": "EPS 확인 불가",
        "finance": { "years": ["-","-","-","-"], "revs": ["-","-","-","-"], "ops": ["-","-","-","-"], "opMs": ["-","-","-","-"], "npMs": ["-","-","-","-"], "debts": ["-","-","-","-"], "epss": ["-","-","-","-"] }
    }
    
    try:
        # 1. 실시간 현재가 (모바일 API)
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
            
        # 3. 재무제표 크롤링 (네이버 금융 PC버전 - 가장 안정적임)
        url = f"https://finance.naver.com/item/main.naver?code={ticker}"
        res_html = requests.get(url, headers=headers)
        soup = BeautifulSoup(res_html.text, 'html.parser')
        
        cop_analysis = soup.find('div', {'class': 'cop_analysis'})
        if cop_analysis:
            table = cop_analysis.find('table')
            thead_trs = table.find('thead').find_all('tr')
            # 연도 4개 파싱
            years = [th.text.strip() for th in thead_trs[1].find_all('th')[:4]]
            
            tbody_trs = table.find('tbody').find_all('tr')
            def get_row(title):
                for tr in tbody_trs:
                    th = tr.find('th')
                    if th and title in th.text:
                        return [td.text.strip() for td in tr.find_all('td')[:4]]
                return ["-", "-", "-", "-"]

            revs = get_row("매출액")
            ops = get_row("영업이익")
            opMs = get_row("영업이익률")
            npMs = get_row("순이익률")
            debts = get_row("부채비율")
            epss = get_row("EPS")
            
            stock_info["finance"] = {
                "years": years, "revs": revs, "ops": ops, "opMs": opMs, "npMs": npMs, "debts": debts, "epss": epss
            }

        # 4. 백엔드에서 PEG 직접 계산
        try:
            target_per = stock_info["fwdPer"] if stock_info["fwdPer"] != "-" else stock_info["per"]
            per_float = float(target_per.replace(',', ''))
            
            eps_valid = []
            for e in stock_info["finance"]["epss"]:
                try: eps_valid.append(float(e.replace(',', '')))
                except: pass
                
            if per_float > 0 and len(eps_valid) >= 2:
                eps_current = eps_valid[-1]
                eps_prev = eps_valid[-2]
                if eps_current > 0 and eps_prev > 0:
                    growth = ((eps_current - eps_prev) / eps_prev) * 100
                    if growth > 0:
                        stock_info["peg"] = f"{per_float / growth:.2f}배"
                        stock_info["pegDesc"] = f"EPS 성장률(+{growth:.1f}%) 반영"
                    else:
                        stock_info["pegDesc"] = "EPS 역성장"
                else:
                    stock_info["pegDesc"] = "적자 지속 또는 흑자 전환"
        except:
            pass # 계산 불가 시 기본값 유지

    except Exception as e:
        print(f"❌ 오류 발생 ({name}): {e}")
        
    quant_data[ticker] = stock_info
    time.sleep(0.5)

with open("quant_data.json", "w", encoding="utf-8") as f:
    json.dump(quant_data, f, ensure_ascii=False, indent=2)

print("✅ 데이터 수집 완료! quant_data.json 저장됨.")
