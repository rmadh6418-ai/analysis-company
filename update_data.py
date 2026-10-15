import json
import time
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup
import FinanceDataReader as fdr

# 유저님 이미지에 있던 주요 섹터별 KOSPI/KOSDAQ 기업들을 모두 통합했습니다.
COMPANIES = [
    # 기존 검색 종목
    "삼성전자", "현대로템", "셀트리온", "SK바이오팜", "유한양행", "오스코텍", "리노공업", "HD현대마린엔진",
    # 화학/에너지/이차전지
    "LG화학", "S-Oil", "SK이노베이션", "롯데케미칼", "LG에너지솔루션", "POSCO홀딩스", "포스코퓨처엠", "삼성SDI", "에코프로비엠", "에코프로", "엔켐",
    # 조선/해운/전기/전자/반도체
    "HD현대중공업", "한화오션", "삼성중공업", "SK하이닉스", "삼성전기", "한미반도체", "HPSP", "주성엔지니어링", "이오테크닉스", "솔브레인", "동진쎄미켐",
    # 자동차/운송/방산/우주항공
    "현대차", "기아", "현대모비스", "한화에어로스페이스", "한국항공우주", "LIG넥스원",
    # 제약/바이오/미용/의료
    "삼성바이오로직스", "알테오젠", "HLB", "삼천당제약", "리가켐바이오", "에스티팜", "휴젤", "클래시스", "실리콘투",
    # 금융/지주/증권
    "KB금융", "신한지주", "하나금융지주", "메리츠금융지주", "카카오뱅크", "삼성물산", "삼성증권", "미래에셋증권", "한국금융지주",
    # 인터넷/게임/엔터/로봇
    "NAVER", "카카오", "크래프톤", "엔씨소프트", "JYP Ent.", "에스엠", "펄어비스", "레인보우로보틱스", "로보티즈",
    # 음식료/건설/철강
    "삼양식품", "CJ제일제당", "현대건설", "고려아연", "현대제철"
]

def fetch_stock_data():
    print("종목 코드를 불러오는 중...")
    df_krx = fdr.StockListing('KRX')
    ticker_dict = dict(zip(df_krx['Name'], df_krx['Code']))
    
    results = {}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for name in set(COMPANIES): # 중복 제거 방어
        ticker = ticker_dict.get(name)
        if not ticker:
            print(f"[{name}] 티커를 찾을 수 없습니다.")
            continue
            
        print(f"[{name}] 네이버 금융 데이터 수집 중...")
        url = f"https://finance.naver.com/item/main.naver?code={ticker}"
        
        try:
            res = requests.get(url, headers=headers)
            res.encoding = 'euc-kr' # 네이버 금융 한글 깨짐 방지
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 1. 현재가 파싱
            current_price_tag = soup.select_one('.no_today .blind')
            current_price = int(current_price_tag.text.replace(',', '')) if current_price_tag else 0
            
            # 2. 목표주가 파싱
            target_price = "-"
            ems = soup.select('.r_info em')
            for i, em in enumerate(ems):
                if '목표주가' in em.text:
                    try:
                        target_price = ems[i+1].text.replace(',', '')
                    except:
                        pass
                    break
            
            # 3. 재무제표 (기업실적분석 표) 파싱
            dfs = pd.read_html(res.text)
            fin_df = None
            for df in dfs:
                # '최근 연간 실적' 이라는 단어가 표 안에 있으면 그 표를 가져옴
                if df.columns.nlevels >= 2 and '최근 연간 실적' in str(df.columns):
                    fin_df = df
                    break

            data = {
                "name": name,
                "ticker": ticker,
                "currentPrice": current_price,
                "targetPrice": target_price,
                "per": "-", "pbr": "-", "eps": "-", "roe": "-", "peg": "-",
                "debtRatio": "-", "revenue": "-", "operatingProfit": "-",
                "operatingMargin": "-", "netMargin": "-",
                "consensus": None,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            if fin_df is not None:
                # 첫 번째 열(매출액, 영업이익 등)을 인덱스로 설정
                fin_df.set_index(fin_df.columns[0], inplace=True)
                
                # 연간 데이터 컬럼만 추출
                annual_cols = [c for c in fin_df.columns if '최근 연간 실적' in c[0]]
                
                def get_val(row_name):
                    try:
                        row = fin_df.loc[row_name, annual_cols]
                        val = row.dropna().values[-1] # 가장 최근 값(보통 올해 컨센서스 또는 작년 확정치)
                        if isinstance(val, str):
                            val = val.replace(',', '')
                        return float(val)
                    except:
                        return "-"

                # 네이버 금융 표에서 직접 값 추출 (단위: 억원, %, 원, 배)
                data['revenue'] = get_val('매출액')
                data['operatingProfit'] = get_val('영업이익')
                data['operatingMargin'] = get_val('영업이익률')
                data['netMargin'] = get_val('순이익률')
                data['roe'] = get_val('ROE(지배)')
                data['debtRatio'] = get_val('부채비율')
                data['eps'] = get_val('EPS(원)')
                data['per'] = get_val('PER(배)')
                data['pbr'] = get_val('PBR(배)')
                
                # 3년치 컨센서스 차트 데이터 구성
                try:
                    last_3_cols = annual_cols[-3:]
                    years = [str(c[1]) for c in last_3_cols]
                    rev_series = fin_df.loc['매출액', last_3_cols].fillna(0)
                    op_series = fin_df.loc['영업이익', last_3_cols].fillna(0)
                    
                    data['consensus'] = {
                        "years": years,
                        "revenue": [float(str(x).replace(',', '')) for x in rev_series.values],
                        "opProfit": [float(str(x).replace(',', '')) for x in op_series.values]
                    }
                except:
                    pass
                    
            results[name] = data
            time.sleep(0.3) # 네이버 서버 과부하 및 차단 방지 (필수)
            
        except Exception as e:
            print(f"[{name}] 수집 실패: {e}")
            continue

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("✅ data.json 네이버 금융 기반 업데이트 완료!")

if __name__ == "__main__":
    fetch_stock_data()
