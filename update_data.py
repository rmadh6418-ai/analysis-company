import json
from datetime import datetime, timedelta
from pykrx import stock

# 유저님 이미지에 있던 모든 섹터별 주요 기업 티커 하드코딩 (오류 원천 봉쇄)
TICKERS = {
    "삼성전자": "005930", "현대로템": "064350", "셀트리온": "068270", "SK바이오팜": "326030", 
    "유한양행": "000100", "오스코텍": "039200", "리노공업": "053980", "HD현대마린엔진": "071970",
    "LG화학": "051910", "S-Oil": "010950", "SK이노베이션": "096770", "롯데케미칼": "011170", 
    "LG에너지솔루션": "373220", "POSCO홀딩스": "005490", "포스코퓨처엠": "003670", "삼성SDI": "006400", 
    "에코프로비엠": "247540", "에코프로": "086520", "엔켐": "348370", "HD현대중공업": "329180", 
    "한화오션": "042660", "삼성중공업": "010140", "SK하이닉스": "000660", "삼성전기": "009150", 
    "한미반도체": "042700", "HPSP": "403870", "주성엔지니어링": "036930", "이오테크닉스": "039030", 
    "솔브레인": "357780", "동진쎄미켐": "005290", "현대차": "005380", "기아": "000270", 
    "현대모비스": "012330", "한화에어로스페이스": "012450", "한국항공우주": "047810", "LIG넥스원": "079550",
    "삼성바이오로직스": "207940", "알테오젠": "196170", "HLB": "028300", "삼천당제약": "000250", 
    "리가켐바이오": "141080", "에스티팜": "237690", "휴젤": "145020", "클래시스": "214150", 
    "실리콘투": "257720", "KB금융": "105560", "신한지주": "055550", "하나금융지주": "086790", 
    "메리츠금융지주": "138040", "카카오뱅크": "323410", "삼성물산": "028260", "삼성증권": "016360", 
    "미래에셋증권": "006800", "한국금융지주": "071050", "NAVER": "035420", "카카오": "035720", 
    "크래프톤": "259960", "엔씨소프트": "036570", "JYP Ent.": "035900", "에스엠": "041510", 
    "펄어비스": "263750", "레인보우로보틱스": "277810", "로보티즈": "108490", "삼양식품": "003230", 
    "CJ제일제당": "097950", "현대건설": "000720", "고려아연": "010130", "현대제철": "004020"
}

def fetch_data():
    today = datetime.today()
    date_str = today.strftime("%Y%m%d")
    
    try:
        print("한국거래소(KRX) 데이터 통신 시도 중...")
        # 1. 가격 데이터 전체 가져오기
        df_price = stock.get_market_ohlcv_by_ticker(date_str, market="ALL")
        
        # 오늘이 주말이거나 장 시작 전이라 데이터가 비어있다면, 최근 평일로 거슬러 올라감
        days_subtracted = 0
        while df_price.empty and days_subtracted < 7:
            days_subtracted += 1
            date_str = (today - timedelta(days=days_subtracted)).strftime("%Y%m%d")
            df_price = stock.get_market_ohlcv_by_ticker(date_str, market="ALL")
            
        # 2. PER, PBR 등 밸류에이션 전체 가져오기
        df_val = stock.get_market_fundamental_by_ticker(date_str, market="ALL")
        print(f"기준일자 [{date_str}] 데이터 성공적으로 획득 완료.")
        
        results = {}
        for name, ticker in TICKERS.items():
            if ticker in df_price.index and ticker in df_val.index:
                price = int(df_price.loc[ticker, "종가"])
                per = df_val.loc[ticker, "PER"]
                pbr = df_val.loc[ticker, "PBR"]
                eps = df_val.loc[ticker, "EPS"]
                
                # 데이터 누락 방어 로직 (0으로 나오면 N/A 처리되도록 "-" 로 변환)
                per_val = round(float(per), 2) if per != 0 else "-"
                pbr_val = round(float(pbr), 2) if pbr != 0 else "-"
                eps_val = int(eps) if eps != 0 else "-"
                
                # ROE 수동 추산 (ROE = PBR / PER)
                roe_val = round((float(pbr) / float(per)) * 100, 2) if (per != 0 and pbr != 0) else "-"
                
                results[name] = {
                    "name": name,
                    "ticker": ticker,
                    "currentPrice": price,
                    "targetPrice": "-",  # 정적 페이지 보안상 목표주가는 수집 제외
                    "per": per_val,
                    "pbr": pbr_val,
                    "eps": eps_val,
                    "roe": roe_val,
                    "peg": "-",
                    "debtRatio": "-",
                    "revenue": "-",
                    "operatingProfit": "-",
                    "operatingMargin": "-",
                    "netMargin": "-",
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
        # JSON 저장
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print("✅ data.json 생성 완료!")
            
    except Exception as e:
        print(f"❌ 데이터 수집 중 치명적 오류 발생: {e}")
        # 오류 발생 시 빈 파일이라도 만들어서 웹페이지가 다운되는 것을 막음
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump({"삼성전자": {"name": "오류발생", "currentPrice": 0}}, f)

if __name__ == "__main__":
    fetch_data()
