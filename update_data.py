import json
import requests
from bs4ッド import BeautifulSoup  # BeautifulSoup import
from bs4 import BeautifulSoup

def get_naver_stock_data(code):
    """네이버 금융에서 주가, 등락률, 시가총액, 외국인 소진율 크롤링"""
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    try:
        # 주가
        price_tag = soup.select_one('.no_today .blind')
        current_price = price_tag.get_text() if price_tag else "N/A"
        
        # 시가총액 및 외국인 소진율 등 추가 정보 파싱
        # (실제 운영 시 네이버 금융 구조에 맞춰 세부 셀렉터 정밀 매칭 필요)
        market_cap_tag = soup.select_one('#_market_sum')
        market_cap = market_cap_tag.get_text() if market_cap_tag else "N/A"
        
        foreign_rate_tag = soup.select_one('.rate_info tr:nth-child(4) .blind') # 예시 셀렉터
        foreign_rate = foreign_rate_tag.get_text() if foreign_rate_tag else "N/A"

        return {
            "current_price": current_price,
            "market_cap": market_cap,
            "foreign_rate": foreign_rate
        }
    except Exception as e:
        print(f"Naver scraping error for {code}: {e}")
        return {}

def get_fnguide_data(code):
    """FnGuide에서 PER, PBR, 매출액, 영업이익률, 순이익률, 부채비율, PEG, 3년 컨센서스 가져오기"""
    # FnGuide API 또는 웹 페이지 구조 활용
    url = f"https://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A{code}"
    # 실무에서는 FnGuide 공식 데이터 연동 API 또는 파싱 로직 적용
    # 아래는 구조 예시 데이터 반환
    return {
        "per": "15.42",
        "pbr": "1.85",
        "revenue": "3조 5,000억",
        "op_margin": "14.2%",
        "net_margin": "10.1%",
        "debt_ratio": "45.2%",
        "peg": "1.2",
        "consensus": {
            "year_1": "매출 3.8조 / 영업이익 5,200억",
            "year_2": "매출 4.2조 / 영업이익 6,100억",
            "year_3": "매출 4.8조 / 영업이익 7,500억"
        }
    }

def get_morningstar_moat(code):
    """모닝스타 기준 경제적 해자 정보 가져오기 (Wide / Narrow / None)"""
    # 모닝스타 리서치 데이터 연동 또는 크롤링 로직
    return "Wide Moat (넓은 해자)"

def main():
    target_stocks = [
        {"code": "005930", "name": "삼성전자"},
        {"code": "000660", "name": "SK하이닉스"}
    ]
    
    database = {}
    for stock in target_stocks:
        code = stock["code"]
        name = stock["name"]
        
        naver_data = get_naver_stock_data(code)
        fnguide_data = get_fnguide_data(code)
        moat = get_morningstar_moat(code)
        
        database[code] = {
            "name": name,
            "code": code,
            **naver_data,
            **fnguide_data,
            "economic_moat": moat
        }
        
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=4)
    print("Data successfully updated and saved to data.json")

if __name__ == "__main__":
    main()
