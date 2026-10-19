import requests
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor

KOSPI200_SECTORS = {
    "화학·에너지": {"LG화학": "051910", "S-Oil": "010950", "SK이노베이션": "096770", "롯데케미칼": "011170", "SK가스": "018670", "GS": "078930", "한국가스공사": "036460", "한화솔루션": "009830", "금호석유": "011780", "OCI홀딩스": "010060", "대한유화": "006650"},
    "이차전지·배터리": {"LG에너지솔루션": "373220", "POSCO홀딩스": "005490", "포스코퓨처엠": "003670", "삼성SDI": "006400", "엘앤에프": "066970", "에코프로머티": "450080", "코스모신소재": "005070", "포스코인터내셔널": "047050", "솔루스첨단소재": "336370", "금양": "001570"},
    "조선·해운·중공업": {"HD현대중공업": "329180", "한화오션": "042660", "삼성중공업": "010140", "HD한국조선해양": "009540", "한화엔진": "082740", "HD현대": "267250", "HD현대마린엔진": "071970", "HD현대마린솔루션": "443060", "한국카본": "017960", "HD현대미포": "010620", "HMM": "011200", "팬오션": "028670"},
    "전기·전자 (반도체/IT)": {"삼성전자": "005930", "SK하이닉스": "000660", "삼성전기": "009150", "LG이노텍": "011070", "한미반도체": "042700", "LG전자": "066570", "이수페타시스": "007660", "DB하이텍": "000990", "삼성에스디에스": "018260", "LG디스플레이": "034220", "해성디에스": "195870"},
    "자동차·운송장비": {"현대차": "005380", "기아": "000270", "현대모비스": "012330", "현대오토에버": "307950", "현대글로비스": "086280", "현대위아": "011210", "에스엘": "005850", "HL만도": "204320", "한국타이어앤테크놀로지": "161390"},
    "원전·전력인프라": {"한국전력": "015760", "두산에너빌리티": "034020", "한전기술": "052690", "한전KPS": "051600", "효성중공업": "298040", "산일전기": "062040", "대한전선": "001440", "일진전기": "103590", "LS ELECTRIC": "010120", "HD현대일렉트릭": "267260", "LS에코에너지": "229640", "LS": "006260", "효성": "004800"},
    "방위산업·우주항공": {"한화에어로스페이스": "012450", "현대로템": "064350", "한국항공우주": "047810", "한화시스템": "272210", "LIG넥스원": "079550", "한화": "000880", "풍산": "103140"},
    "제약·바이오": {"삼성바이오로직스": "207940", "셀트리온": "068270", "유한양행": "000100", "한미약품": "128940", "SK바이오팜": "326030", "녹십자": "006280", "대웅제약": "069620", "SK바이오사이언스": "302440", "종근당": "185750", "대원제약": "003220", "한올바이오파마": "009420"},
    "화장품·의류": {"아모레퍼시픽": "090430", "LG생활건강": "051900", "한국콜마": "161890", "코스맥스": "192820", "토니모리": "214420", "애경산업": "018250", "F&F": "383220", "영원무역": "111110"},
    "금융·지주": {"KB금융": "105560", "신한지주": "055550", "하나금융지주": "086790", "메리츠금융지주": "138040", "기업은행": "024110", "우리금융지주": "316140", "IM금융지주": "139130", "카카오뱅크": "323410", "카카오페이": "377300", "삼성물산": "028260", "SK": "034730"},
    "손해보험": {"삼성화재": "000810", "DB손해보험": "005830", "현대해상": "001450", "한화손해보험": "000370", "삼성생명": "032830", "롯데손해보험": "000400", "서울보증보험": "462520", "코리안리": "003690"},
    "증권사": {"삼성증권": "016360", "미래에셋증권": "006800", "한국금융지주": "071050", "키움증권": "039490", "SK증권": "001510", "NH투자증권": "005940", "한화투자증권": "003530", "현대차증권": "001500", "대신증권": "003540"},
    "인터넷·게임·플랫폼": {"NAVER": "035420", "카카오": "035720", "크래프톤": "259960", "엔씨소프트": "036570", "넷마블": "251270"},
    "건설·시공": {"현대건설": "000720", "대우건설": "047040", "GS건설": "006360", "DL이앤씨": "375500", "HDC현대산업개발": "294870"},
    "철강·금속": {"고려아연": "010130", "현대제철": "004020", "동국제강": "460860", "세아제강": "306200"},
    "음식료·유통": {"삼양식품": "003230", "CJ제일제당": "097950", "오리온": "271560", "농심": "004370", "BGF리테일": "282330", "이마트": "139480", "롯데쇼핑": "023530", "신세계": "004170", "하이트진로": "000080"}
}

KOSDAQ150_SECTORS = {
    "제약·바이오": {"알테오젠": "196170", "HLB": "028300", "삼천당제약": "000250", "리가켐바이오": "141080", "에스티팜": "237690", "HK이노엔": "195940", "동국제약": "086450", "디앤디파마텍": "347850", "올릭스": "226950", "에이비엘바이오": "298380", "펩트론": "087010", "오스코텍": "039200", "엘앤씨바이오": "290650", "셀트리온제약": "068760", "차바이오텍": "085660", "메디톡스": "086900", "보로노이": "310210"},
    "미용의료·화장품": {"휴젤": "145020", "클래시스": "214150", "실리콘투": "257720", "파마리서치": "214450", "제이시스메디칼": "287410", "원텍": "336570", "브이티": "018290", "아이패밀리에스씨": "393260", "마녀공장": "439090", "코스메카코리아": "241710"},
    "이차전지·소재": {"에코프로비엠": "247540", "에코프로": "086520", "엔켐": "348370", "대주전자재료": "078600", "서진시스템": "253010", "나노신소재": "121600", "피엔티": "137400", "동화기업": "025900", "한중엔시에스": "107640", "에코프로에이치엔": "383310", "성일하이텍": "365340", "더블유씨피": "393890", "윤성에프앤씨": "372170", "새빗켐": "107600"},
    "반도체 소부장": {"HPSP": "403870", "리노공업": "058470", "주성엔지니어링": "036930", "이오테크닉스": "039030", "솔브레인": "357780", "동진쎄미켐": "005290", "티씨케이": "064760", "ISC": "095340", "하나머티리얼즈": "166090", "대덕전자": "353200", "유진테크": "084370", "심텍": "222800", "원익IPS": "240810", "테크윙": "089030", "파크시스템스": "140860", "두산테스나": "131970", "필옵틱스": "161580", "원익QnC": "074600"},
    "엔터·미디어": {"JYP Ent.": "035900", "에스엠": "041510", "스튜디오드래곤": "253450", "CJ ENM": "035760", "와이지엔터테인먼트": "122870", "디어유": "376300", "초록뱀미디어": "047820", "삼화네트웍스": "046390"},
    "게임·소프트웨어": {"펄어비스": "263750", "카카오게임즈": "293490", "위메이드": "112040", "넥슨게임즈": "225570", "컴투스": "078340", "네오위즈": "095660", "웹젠": "069080", "엠게임": "058630", "안랩": "053800"},
    "로봇·자동화": {"레인보우로보틱스": "277810", "로보티즈": "108490", "에스에프에이": "056190", "휴림로봇": "090710", "로보스타": "090360", "에스피지": "058610", "하이젠알앤엠": "160190", "삼현": "437730", "유일로보틱스": "388720", "티로보틱스": "117730", "에브리봇": "270660", "뉴로메카": "348340", "알에스오토메이션": "140670"},
    "피팅·배관기자재": {"성광벤드": "014620", "태광": "023160", "하이록코리아": "013030", "디케이락": "105740", "비엠티": "086670", "태웅": "044490"}
}

TARGET_STOCKS = {}
for sector, companies in KOSPI200_SECTORS.items(): TARGET_STOCKS.update(companies)
for sector, companies in KOSDAQ150_SECTORS.items(): TARGET_STOCKS.update(companies)

def fetch_stock_data(name, ticker):
    stock_info = {
        "name": name, "price": "N/A", "targetPrice": "-", "changeRate": "0.00%", "direction": "FLAT", "rawPrice": 0,
        "marketCap": "-", "foreignRate": "-", "per": "-", "fwdPer": "-", "pbr": "-", "dividend": "-",
        "peg": "N/A", "pegDesc": "EPS 부족",
        "finance": { "years": [], "revs": [], "ops": [], "opMs": [], "npMs": [], "debts": [], "epss": [] }
    }
    
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    
    # 1. API 데이터 요청
    try: res_basic = session.get(f"https://m.stock.naver.com/api/stock/{ticker}/basic", timeout=3).json()
    except: res_basic = {}
    try: res_integ = session.get(f"https://m.stock.naver.com/api/stock/{ticker}/integration", timeout=3).json()
    except: res_integ = {}

    # 2. 기본 주가 데이터
    try:
        raw_price_str = "".join(filter(str.isdigit, str(res_basic.get("closePrice", "0"))))
        stock_info["rawPrice"] = int(raw_price_str) if raw_price_str else 0
        stock_info["price"] = res_basic.get("closePrice", "N/A")
        
        fluctuation = float(res_basic.get("fluctuationsRatio", 0))
        if fluctuation > 0: stock_info["direction"], stock_info["changeRate"] = "UP", f"▲ +{fluctuation}%"
        elif fluctuation < 0: stock_info["direction"], stock_info["changeRate"] = "DOWN", f"▼ {abs(fluctuation)}%"
    except: pass

    # 3. 주요 투자 지표 1차 추출 (API)
    try:
        if res_basic.get("dividendYield"): stock_info["dividend"] = str(res_basic["dividendYield"]) + "%"
        if res_basic.get("marketSum"): stock_info["marketCap"] = str(res_basic["marketSum"])
        if res_basic.get("foreignRatio"): stock_info["foreignRate"] = str(res_basic["foreignRatio"]) + "%"
        if res_basic.get("per"): stock_info["per"] = str(res_basic["per"])
        if res_basic.get("pbr"): stock_info["pbr"] = str(res_basic["pbr"])
        
        for info in res_integ.get("totalInfos", []):
            val = str(info.get("value", "-")).strip()
            if val == "-" or not val: continue
            n = str(info.get("name", "")).lower()
            k = str(info.get("key", "")).lower()
            
            if ("시가총액" in n or "시총" in n or "market" in k) and stock_info["marketCap"] == "-": stock_info["marketCap"] = val
            elif ("외인" in n or "외국인" in n or "foreign" in k) and stock_info["foreignRate"] == "-": stock_info["foreignRate"] = val
            elif ("추정per" in n or "cnsper" in k): stock_info["fwdPer"] = val.replace("배", "")
            elif ("per" in k and "추정" not in n) and stock_info["per"] == "-": stock_info["per"] = val.replace("배", "")
            elif ("pbr" in k) and stock_info["pbr"] == "-": stock_info["pbr"] = val.replace("배", "")
            elif ("배당" in n or "dividend" in k) and stock_info["dividend"] == "-": stock_info["dividend"] = val if "%" in val else f"{val}%"
    except: pass

    # 4. 🔥 무적의 목표주가 강제 추출 로직 (API -> 네이버웹 -> FnGuide웹) 🔥
    def get_tp(val):
        if not val: return None
        digits = "".join(filter(str.isdigit, str(val)))
        if digits and int(digits) > 100: return f"{int(digits):,}"
        return None

    tp = None
    # 4-1. API 시도
    if not tp: tp = get_tp(res_basic.get("cnsTargetPrice"))
    if not tp: tp = get_tp(res_integ.get("opinion", {}).get("targetPrice"))
    
    # 4-2. 네이버 PC 웹 크롤링 시도 (HD현대중공업 등 API 누락 종목 방어)
    if not tp:
        try:
            html = session.get(f"https://finance.naver.com/item/main.naver?code={ticker}", timeout=3).text
            match = re.search(r'목표주가.*?<td[^>]*>.*?<em[^>]*>([\d,]+)</em>', html, re.DOTALL | re.IGNORECASE)
            if match: tp = get_tp(match.group(1))
        except: pass

    # 4-3. FnGuide 원본 서버 크롤링 시도 (최후의 보루)
    if not tp:
        try:
            fng_html = session.get(f"https://comp.fnguide.com/SVO2/ASP/SVD_Consensus.asp?pGB=1&gicode=A{ticker}", timeout=3).text
            match = re.search(r'적정주가.*?<td[^>]*>\s*([\d,]+)\s*</td>', fng_html, re.DOTALL | re.IGNORECASE)
            if match: tp = get_tp(match.group(1))
        except: pass

    if tp: stock_info["targetPrice"] = tp

    # 5. 재무제표 
    try:
        res_fin = session.get(f"https://m.stock.naver.com/api/stock/{ticker}/finance/annual", timeout=5).json()
        fin_info = res_fin.get("financeInfo", {})
        if fin_info and "trTitleList" in fin_info and "rowList" in fin_info:
            keys = [item.get("key", "") for item in fin_info["trTitleList"][-5:]]
            years = [item.get("title", "") + ("(E)" if item.get("isConsensus")=="Y" and "(E)" not in item.get("title", "") else "") for item in fin_info["trTitleList"][-5:]]
            stock_info["finance"]["years"] = years
            
            def get_fin(keyword):
                for row in fin_info["rowList"]:
                    if keyword in row.get("title", ""):
                        return [str(row.get("columns", {}).get(k, {}).get("value", "-")) for k in keys]
                return ["-"] * len(keys)

            stock_info["finance"]["revs"] = get_fin("매출액")
            stock_info["finance"]["ops"] = get_fin("영업이익")
            stock_info["finance"]["opMs"] = get_fin("영업이익률")
            stock_info["finance"]["npMs"] = get_fin("순이익률")
            stock_info["finance"]["debts"] = get_fin("부채비율")
            stock_info["finance"]["epss"] = get_fin("EPS")
    except: pass
    
    # 6. PEG 계산
    try:
        per_val = stock_info["fwdPer"] if stock_info["fwdPer"] != "-" else stock_info["per"]
        per_float = float(str(per_val).replace(',', ''))
        
        eps_valid = [float(str(e).replace(',','')) for e in stock_info["finance"]["epss"] if str(e).replace(',','').replace('.','').replace('-','').isdigit() and str(e) != "-"]
        
        if per_float > 0 and len(eps_valid) >= 2:
            eps_c, eps_p = eps_valid[-1], eps_valid[-2]
            if eps_c > 0 and eps_p > 0:
                growth = ((eps_c - eps_p) / eps_p) * 100
                if growth > 0:
                    stock_info["peg"] = f"{per_float / growth:.2f}배"
                    stock_info["pegDesc"] = f"EPS 성장률(+{growth:.1f}%) 반영"
                else: stock_info["pegDesc"] = "EPS 역성장"
            else: stock_info["pegDesc"] = "적자지속/흑자전환"
    except: pass
    
    return ticker, stock_info

quant_data = {}
print(f"🚀 총 {len(TARGET_STOCKS)}개 주식 데이터 초고속 수집 시작...")
start_time = time.time()

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(fetch_stock_data, name, ticker): ticker for name, ticker in TARGET_STOCKS.items()}
    for future in futures:
        ticker, data = future.result()
        quant_data[ticker] = data

with open("quant_data.json", "w", encoding="utf-8") as f:
    json.dump(quant_data, f, ensure_ascii=False, indent=2)

end_time = time.time()
print(f"✅ 데이터 수집 완료! (소요 시간: {end_time - start_time:.2f}초) quant_data.json 저장됨.")
