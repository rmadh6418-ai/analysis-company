import requests
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor

# ================= KOSPI 200 전체 종목 분류 ================= #
KOSPI200_SECTORS = {
    "반도체·IT (H/W)": {"삼성전자": "005930", "SK하이닉스": "000660", "삼성전기": "009150", "LG이노텍": "011070", "LG전자": "066570", "LG디스플레이": "034220", "한미반도체": "042700", "DB하이텍": "000990", "이수페타시스": "007660", "해성디에스": "195870", "LX세미콘": "108320", "한솔케미칼": "014680"},
    "이차전지·소재": {"LG에너지솔루션": "373220", "POSCO홀딩스": "005490", "삼성SDI": "006400", "포스코퓨처엠": "003670", "에코프로머티": "450080", "엘앤에프": "066970", "코스모신소재": "005070", "코스모화학": "005420", "솔루스첨단소재": "336370", "금양": "001570", "더블유씨피": "393890", "롯데에너지머티리얼즈": "020150", "SK아이이테크놀로지": "361610"},
    "플랫폼·게임·IT(S/W)": {"NAVER": "035420", "카카오": "035720", "크래프톤": "259960", "엔씨소프트": "036570", "넷마블": "251270", "카카오페이": "377300", "카카오뱅크": "323410", "삼성에스디에스": "018260", "현대오토에버": "307950", "롯데이노베이트": "286940", "더존비즈온": "012510", "포스코DX": "022100", "다우기술": "023590", "에스원": "012750"},
    "통신·미디어": {"SK텔레콤": "017670", "KT": "030200", "LG유플러스": "032640", "제일기획": "030000", "이노션": "214320", "CJ ENM": "035760", "스튜디오드래곤": "253450"},
    "자동차·부품·타이어": {"현대차": "005380", "기아": "000270", "현대모비스": "012330", "현대글로비스": "086280", "현대위아": "011210", "HL만도": "204320", "에스엘": "005850", "한국타이어앤테크놀로지": "161390", "금호타이어": "073240", "넥센타이어": "002350", "화신": "010690", "성우하이텍": "015750", "명신산업": "009900", "DN오토모티브": "007340"},
    "조선·기계·운송": {"HD한국조선해양": "009540", "HD현대중공업": "329180", "삼성중공업": "010140", "한화오션": "042660", "HD현대미포": "010620", "한화엔진": "082740", "HD현대마린엔진": "071970", "HD현대마린솔루션": "443060", "HMM": "011200", "대한항공": "003490", "아시아나항공": "020560", "팬오션": "028670", "CJ대한통운": "000120", "두산밥캣": "241560", "HD현대건설기계": "267270", "HD현대인프라코어": "042670", "한국카본": "017960", "현대엘리베이": "017800", "두산로보틱스": "454910", "SK오션플랜트": "100090"},
    "방위산업·우주항공": {"한화에어로스페이스": "012450", "현대로템": "064350", "한국항공우주": "047810", "LIG넥스원": "079550", "한화시스템": "272210", "풍산": "103140"},
    "원전·전력설비": {"두산에너빌리티": "034020", "한국전력": "015760", "한전기술": "052690", "한전KPS": "051600", "LS ELECTRIC": "010120", "HD현대일렉트릭": "267260", "효성중공업": "298040", "대한전선": "001440", "일진전기": "103590", "두산퓨얼셀": "336260", "씨에스윈드": "112610", "LS에코에너지": "229640"},
    "제약·바이오": {"삼성바이오로직스": "207940", "셀트리온": "068270", "유한양행": "000100", "한미약품": "128940", "SK바이오팜": "326030", "SK바이오사이언스": "302440", "녹십자": "006280", "종근당": "185750", "대웅제약": "069620", "대원제약": "003220", "보령": "003850", "JW중외제약": "001060", "영진약품": "003520", "일동제약": "249420", "환인제약": "016580", "한올바이오파마": "009420", "신풍제약": "019170", "에스디바이오센서": "137310", "대웅": "003090", "바이오노트": "377740"},
    "화학·정유·에너지": {"LG화학": "051910", "SK이노베이션": "096770", "S-Oil": "010950", "한화솔루션": "009830", "롯데케미칼": "011170", "금호석유": "011780", "SKC": "011790", "효성첨단소재": "298050", "효성티앤씨": "298020", "OCI홀딩스": "010060", "대한유화": "006650", "한국가스공사": "036460", "SK가스": "018670", "롯데정밀화학": "004000", "애경케미칼": "161000", "태광산업": "003240", "후성": "093370", "케이카": "381970", "TKG휴켐스": "069260", "이수스페셜티케미컬": "457190", "PI첨단소재": "178920", "SK케미칼": "285130", "OCI": "456040"},
    "철강·비철금속·소재": {"고려아연": "010130", "현대제철": "004020", "동국제강": "460860", "세아제강": "306200", "세아베스틸지주": "001430", "KG모빌리티": "003620", "영풍": "000670", "동원산업": "006040", "포스코인터내셔널": "047050", "세아제강지주": "003030", "삼아알미늄": "006110"},
    "금융·지주사": {"KB금융": "105560", "신한지주": "055550", "하나금융지주": "086790", "우리금융지주": "316140", "메리츠금융지주": "138040", "기업은행": "024110", "BNK금융지주": "138930", "DGB금융지주": "139130", "JB금융지주": "175330", "SK": "034730", "LG": "003550", "HD현대": "267250", "CJ": "001040", "LS": "006260", "한화": "000880", "GS": "078930", "삼성물산": "028260", "두산": "000150", "효성": "004800", "BGF": "027410"},
    "증권·보험": {"삼성생명": "032830", "삼성화재": "000810", "DB손해보험": "005830", "현대해상": "001450", "한화생명": "088350", "한화손해보험": "000370", "롯데손해보험": "000400", "코리안리": "003690", "미래에셋증권": "006800", "한국금융지주": "071050", "NH투자증권": "005940", "삼성증권": "016360", "키움증권": "039490", "대신증권": "003540", "한화투자증권": "003530", "동양생명": "082640"},
    "건설·건자재": {"현대건설": "000720", "GS건설": "006360", "대우건설": "047040", "DL이앤씨": "375500", "HDC현대산업개발": "294870", "삼성E&A": "028050", "쌍용C&E": "003410", "KCC": "002380", "아세아시멘트": "183190", "한일시멘트": "300720", "동서": "026960"},
    "화장품·의류·소비재": {"아모레퍼시픽": "090430", "LG생활건강": "051900", "한국콜마": "161890", "코스맥스": "192820", "아모레G": "002790", "애경산업": "018250", "F&F": "383220", "영원무역": "111110", "한섬": "020000", "휠라홀딩스": "081660", "코웨이": "021240", "쿠쿠홈시스": "284740", "에이피알": "278470", "영원무역홀딩스": "009970", "신세계인터내셔날": "031430"},
    "음식료·유통·엔터": {"KT&G": "033780", "CJ제일제당": "097950", "삼양식품": "003230", "오리온": "271560", "농심": "004370", "롯데웰푸드": "280360", "하이트진로": "000080", "대상": "001680", "오뚜기": "007310", "롯데칠성": "005300", "동원F&B": "049770", "이마트": "139480", "BGF리테일": "282330", "GS리테일": "007070", "신세계": "004170", "롯데쇼핑": "023530", "현대백화점": "069960", "호텔신라": "008770", "강원랜드": "035250", "GKL": "114090", "현대홈쇼핑": "057050", "빙그레": "005180", "현대그린푸드": "453340"}
}

# ================= KOSDAQ 150 전체 종목 분류 ================= #
KOSDAQ150_SECTORS = {
    "반도체·장비 (IT H/W)": {"씨엠티엑스": "388210", "리노공업": "058470", "HPSP": "403870", "이오테크닉스": "039030", "주성엔지니어링": "036930", "솔브레인": "357780", "동진쎄미켐": "005290", "하나머티리얼즈": "166090", "원익IPS": "240810", "테크윙": "089030", "ISC": "095340", "심텍": "222800", "대덕전자": "353200", "파크시스템스": "140860", "티씨케이": "064760", "원익QnC": "074600", "두산테스나": "131970", "유진테크": "084370", "SFA반도체": "036540", "네오셈": "253590", "덕산네오룩스": "213420", "피에스케이": "031980", "고영": "098460", "제주반도체": "080220", "테스": "095610", "원익홀딩스": "030530", "에스티아이": "039440", "아이쓰리시스템": "214430", "하나마이크론": "067310", "에스앤에스텍": "101490", "티에스이": "131290", "코미코": "183300", "와이씨": "232140", "퀄리타스반도체": "432720", "어보브반도체": "102120", "가온칩스": "399720", "오픈엣지테크놀로지": "394280", "에이직랜드": "445090", "텔레칩스": "054450", "넥스틴": "348210", "파두": "440110"},
    "이차전지·소재": {"에코프로비엠": "247540", "에코프로": "086520", "대주전자재료": "078600", "엔켐": "348370", "나노신소재": "121600", "피엔티": "137400", "동화기업": "025900", "성일하이텍": "365340", "더블유씨피": "393890", "윤성에프앤씨": "372170", "천보": "278280", "에코프로에이치엔": "383310", "새빗켐": "107600", "씨아이에스": "222080", "신성델타테크": "065350", "레이크머티리얼즈": "281740", "포스코엠텍": "009520", "이녹스첨단소재": "272290", "유진테크놀로지": "439370", "탑머티리얼": "360070", "제이오": "418550", "신성에스티": "416180"},
    "제약·바이오": {"알테오젠": "196170", "HLB": "028300", "삼천당제약": "000250", "리가켐바이오": "141080", "에스티팜": "237690", "휴젤": "145020", "클래시스": "214150", "파마리서치": "214450", "셀트리온제약": "068760", "케어젠": "214370", "에이비엘바이오": "298380", "메디톡스": "086900", "오스코텍": "039200", "펩트론": "087010", "차바이오텍": "085660", "보로노이": "310210", "HK이노엔": "195940", "네이처셀": "007390", "올릭스": "226950", "엘앤씨바이오": "290650", "씨젠": "096530", "동국제약": "086450", "디앤디파마텍": "347850", "제넥신": "095700", "현대바이오": "048410", "젬백스": "082270", "루닛": "328130", "뷰노": "338220", "제이엘케이": "322510", "코어라인소프트": "384470", "큐로셀": "372320", "신테카바이오": "226330", "툴젠": "199800", "바이오다인": "314930"},
    "게임·IT(S/W)": {"펄어비스": "263750", "카카오게임즈": "293490", "위메이드": "112040", "넥슨게임즈": "225570", "컴투스": "078340", "네오위즈": "095660", "웹젠": "069080", "안랩": "053800", "위메이드맥스": "101730", "데브시스터즈": "194480", "한글과컴퓨터": "030520", "다우데이타": "032190", "엠게임": "058630", "아이티센": "124500", "코나아이": "052400", "NHN한국사이버결제": "060250", "엠로": "058970", "마음AI": "377220", "솔트룩스": "304100", "크라우드웍스": "355390", "폴라리스오피스": "041020", "이스트소프트": "047560"},
    "엔터·미디어·플랫폼": {"JYP Ent.": "035900", "에스엠": "041510", "와이지엔터테인먼트": "122870", "SOOP": "067160", "CJ ENM": "035760", "스튜디오드래곤": "253450", "디어유": "376300", "초록뱀미디어": "047820", "삼화네트웍스": "046390", "카페24": "042000"},
    "미용의료·화장품·소비재": {"실리콘투": "257720", "제이시스메디칼": "287410", "원텍": "336570", "브이티": "018290", "마녀공장": "439090", "아이패밀리에스씨": "393260", "코스메카코리아": "241710", "펌텍코리아": "251970", "감성코퍼레이션": "036620", "메가스터디교육": "215200", "아난티": "025980", "제이투케이바이오": "420570", "씨앤씨인터내셔널": "352480", "비올": "335890"},
    "로봇·기계·부품": {"레인보우로보틱스": "277810", "에스에프에이": "056190", "로보티즈": "108490", "에스피지": "058610", "휴림로봇": "090710", "로보스타": "090360", "티로보틱스": "117730", "유일로보틱스": "388720", "에브리봇": "270660", "유진로봇": "056080", "알에스오토메이션": "140670", "하이젠알앤엠": "160190", "삼현": "437730", "성광벤드": "014620", "태광": "023160", "서진시스템": "253010", "비에이치아이": "083650", "엔젤로보틱스": "455900", "뉴로메카": "348340", "에스비비테크": "389500"},
    "통신장비·기타": {"케이엠더블유": "032500", "쏠리드": "050890", "인텔리안테크": "189300", "RFHIC": "218410", "쎄트렉아이": "099320", "제룡전기": "033100", "LS마린솔루션": "060370", "동성화인텍": "033500", "시노펙스": "025320", "우리기술투자": "041190", "미래에셋벤처투자": "100790", "서부T&D": "006730", "삼표시멘트": "038500", "하림지주": "003380", "우진엔텍": "453040", "에코아이": "448280"}
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
    
    # 1. API 데이터 요청 (에러 방어)
    try: res_basic = session.get(f"https://m.stock.naver.com/api/stock/{ticker}/basic", timeout=5).json()
    except: res_basic = {}
    try: res_integ = session.get(f"https://m.stock.naver.com/api/stock/{ticker}/integration", timeout=5).json()
    except: res_integ = {}
    try: res_fin = session.get(f"https://m.stock.naver.com/api/stock/{ticker}/finance/annual", timeout=5).json()
    except: res_fin = {}

    # 2. 기본 주가 데이터
    try:
        raw_price_str = "".join(filter(str.isdigit, str(res_basic.get("closePrice", "0"))))
        stock_info["rawPrice"] = int(raw_price_str) if raw_price_str else 0
        stock_info["price"] = res_basic.get("closePrice", "N/A")
        
        fluctuation = float(res_basic.get("fluctuationsRatio", 0))
        if fluctuation > 0: stock_info["direction"], stock_info["changeRate"] = "UP", f"▲ +{fluctuation}%"
        elif fluctuation < 0: stock_info["direction"], stock_info["changeRate"] = "DOWN", f"▼ {abs(fluctuation)}%"
    except: pass

    # 3. 목표주가 및 지표 1차 추출 (모바일 API)
    try:
        if res_basic.get("cnsTargetPrice"):
            digits = "".join(filter(str.isdigit, str(res_basic["cnsTargetPrice"])))
            if digits and int(digits) > 0: stock_info["targetPrice"] = f"{int(digits):,}"
            
        opinion = res_integ.get("opinion")
        if isinstance(opinion, dict) and stock_info["targetPrice"] == "-":
            tp_val = str(opinion.get("targetPrice", ""))
            digits = "".join(filter(str.isdigit, tp_val))
            if digits and int(digits) > 0: stock_info["targetPrice"] = f"{int(digits):,}"

        for info in res_integ.get("totalInfos", []):
            k = str(info.get("key", "")).lower()
            c = str(info.get("code", "")).lower()
            n = str(info.get("name", "")).lower()
            t = str(info.get("title", "")).lower()
            val = str(info.get("value", "-")).strip()
            
            if val == "-" or not val: continue
            comb = f"{k} {c} {n} {t}"
            
            if any(x in comb for x in ["marketvalue", "marketsum", "시가총액", "시총"]) and stock_info["marketCap"] == "-":
                stock_info["marketCap"] = val
            elif any(x in comb for x in ["foreign", "외국인", "외인"]) and stock_info["foreignRate"] == "-":
                stock_info["foreignRate"] = val
            elif any(x in comb for x in ["cnsper", "추정per"]):
                stock_info["fwdPer"] = val.replace("배", "")
            elif "per" in comb and not any(x in comb for x in ["cns", "추정", "fwd"]) and stock_info["per"] == "-":
                stock_info["per"] = val.replace("배", "")
            elif "pbr" in comb and stock_info["pbr"] == "-":
                stock_info["pbr"] = val.replace("배", "")
            elif ("dividend" in comb or "배당" in comb) and stock_info["dividend"] == "-":
                stock_info["dividend"] = val if "%" in val else f"{val}%"
            elif ("target" in comb or "목표" in comb) and stock_info["targetPrice"] == "-":
                digits = "".join(filter(str.isdigit, val))
                if digits and int(digits) > 0: stock_info["targetPrice"] = f"{int(digits):,}"
    except: pass

    # 4. 🔥 무조건 찾아내는 PC 웹 크롤링 (목표주가 2차 방어선) 🔥
    try:
        html = session.get(f"https://finance.naver.com/item/main.naver?code={ticker}", timeout=5).text
        
        # 목표주가 강제 추출
        if stock_info["targetPrice"] == "-":
            idx = html.find('목표주가')
            if idx != -1:
                sub_html = html[idx:idx+200]
                nums = re.findall(r'[\d,]{4,}', sub_html)
                for n in nums:
                    clean_n = n.replace(',', '').strip()
                    if clean_n.isdigit() and int(clean_n) > 0:
                        stock_info["targetPrice"] = f"{int(clean_n):,}"
                        break

        # 배당수익률 강제 추출
        if stock_info["dividend"] == "-":
            idx = html.find('배당수익률')
            if idx != -1:
                sub_html = html[idx:idx+200]
                nums = re.findall(r'>\s*([\d.]+)\s*<', sub_html)
                for n in nums:
                    if n.replace('.', '', 1).isdigit():
                        stock_info["dividend"] = n + "%"
                        break
                        
        if stock_info["per"] == "-":
            idx = html.find('PER')
            if idx != -1:
                match = re.search(r'<em[^>]*>([\d.]+)</em>', html[idx:idx+200])
                if match: stock_info["per"] = match.group(1)
                
        if stock_info["pbr"] == "-":
            idx = html.find('PBR')
            if idx != -1:
                match = re.search(r'<em[^>]*>([\d.]+)</em>', html[idx:idx+200])
                if match: stock_info["pbr"] = match.group(1)
    except: pass

    # 5. 재무제표 
    try:
        fin_info = res_fin.get("financeInfo", {})
        if fin_info and "trTitleList" in fin_info and "rowList" in fin_info:
            tr_list = fin_info["trTitleList"]
            r_list = fin_info["rowList"]
            valid_cols = tr_list[-5:]
            keys = [item.get("key", "") for item in valid_cols]
            years = []
            for item in valid_cols:
                y_text = item.get("title", "")
                if item.get("isConsensus") == "Y" and "(E)" not in y_text: y_text += "(E)"
                years.append(y_text)
            stock_info["finance"]["years"] = years
            
            def get_fin_valid(keyword):
                for row in r_list:
                    if keyword in row.get("title", ""):
                        cols = row.get("columns", {})
                        return [str(cols.get(k, {}).get("value", "-")) for k in keys]
                return ["-"] * len(keys)

            stock_info["finance"]["revs"] = get_fin_valid("매출액")
            stock_info["finance"]["ops"] = get_fin_valid("영업이익")
            stock_info["finance"]["opMs"] = get_fin_valid("영업이익률")
            stock_info["finance"]["npMs"] = get_fin_valid("순이익률")
            stock_info["finance"]["debts"] = get_fin_valid("부채비율")
            stock_info["finance"]["epss"] = get_fin_valid("EPS")
    except: pass

    # 6. PEG 계산
    try:
        target_per = stock_info["fwdPer"] if stock_info["fwdPer"] != "-" else stock_info["per"]
        per_float = float(str(target_per).replace(',', ''))
        eps_valid = []
        for e in stock_info["finance"]["epss"]:
            clean_e = str(e).replace(',', '').strip()
            if clean_e and clean_e != "-":
                try: eps_valid.append(float(clean_e))
                except: pass
            
        if per_float > 0 and len(eps_valid) >= 2:
            eps_current, eps_prev = eps_valid[-1], eps_valid[-2]
            if eps_current > 0 and eps_prev > 0:
                growth = ((eps_current - eps_prev) / eps_prev) * 100
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
