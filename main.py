import requests
from bs4 import BeautifulSoup
import json

# -------------------------------------------------------------
# ⚠️ 본인의 정보(토큰, ID, API키)를 정확히 입력해 주세요.
BOT_TOKEN = "8806819870:AAFfZZ5SZbjfK4EUWmpxsPYwR353FwrTn6w"
CHAT_ID = "8434942322"
GEMINI_API_KEY = "AQ.Ab8RN6K3WjcKpVeAW2tVf2lHjj0UHTHjq-MBbiEbaoBcjzmgAw"
# -------------------------------------------------------------

def analyze_news_impact_with_gemini(news_list):
    """Gemini 2.5 Flash REST API 직통 호출"""
    api_key = GEMINI_API_KEY.strip()
    
    # Gemini 2.5 Flash 최신 공식 엔드포인트
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    news_text = "\n".join(news_list)
    prompt = f"""
다음은 오늘의 주요 뉴스 헤드라인입니다:
{news_text}

위 뉴스 내용들을 바탕으로, 국내 증시(삼성전자, SK하이닉스, KODEX 200 등)에 미칠 영향과 전망을 3~4줄로 핵심만 요약/예측해 주세요.
부드럽고 신뢰감 있는 어조로 작성해 주세요.
"""
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        
        if res.status_code == 200:
            result = res.json()
            return result['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            # 실패 시 에러 원인을 텔레그램 메시지에 출력
            try:
                err_detail = res.json().get('error', {}).get('message', res.text)
            except:
                err_detail = res.text
            return f"⚠️ AI 분석 불러오기 실패 (코드: {res.status_code})\n원인: {err_detail}"
            
    except Exception as e:
        return f"⚠️ 통신 중 오류 발생: {e}"


def get_market_and_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    msg_lines = []
    news_titles = []
    
    # [1] 뉴스 수집
    msg_lines.append("📰 오늘의 주요 뉴스")
    msg_lines.append("-" * 25)
    try:
        news_url = "https://www.mk.co.kr/rss/30000001/"
        news_res = requests.get(news_url, headers=headers, timeout=10)
        news_soup = BeautifulSoup(news_res.text, 'html.parser')
        items = news_soup.find_all('item')

        count = 0
        for item in items:
            title_tag = item.find('title')
            if title_tag:
                title = title_tag.text.strip()
                if title:
                    count += 1
                    news_titles.append(f"- {title}")
                    msg_lines.append(f"{count}. {title}")
                    if count == 5:
                        break
    except Exception as e:
        msg_lines.append(f"뉴스 수집 실패: {e}")

    # [2] 주가 수집
    msg_lines.append("\n📈 주요 증시 및 ETF")
    msg_lines.append("-" * 25)
    
    stocks = {
        "삼성전자": "005930",
        "SK하이닉스": "000660",
        "KODEX 200": "069500"
    }

    for name, code in stocks.items():
        try:
            stock_url = f"https://finance.naver.com/item/main.naver?code={code}"
            stock_res = requests.get(stock_url, headers=headers, timeout=10)
            stock_soup = BeautifulSoup(stock_res.text, 'html.parser')
            price_tag = stock_soup.select_one("p.no_today span.blind")
            
            if price_tag:
                msg_lines.append(f"• {name}: {price_tag.text}원")
            else:
                msg_lines.append(f"• {name}: 정보 없음")
        except:
            msg_lines.append(f"• {name}: 수집 실패")

    # [3] AI 기반 증시 영향 분석/예측
    msg_lines.append("\n🤖 AI의 증시 영향 분석 및 예측")
    msg_lines.append("-" * 25)
    
    if news_titles:
        ai_analysis = analyze_news_impact_with_gemini(news_titles)
        msg_lines.append(ai_analysis)
    else:
        msg_lines.append("수집된 뉴스가 없어 AI 분석을 진행하지 못했습니다.")

    return "\n".join(msg_lines)


def send_telegram_message(message):
    token = BOT_TOKEN.strip()
    chat_id = CHAT_ID.strip()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message
    }
    res = requests.post(url, data=data)
    if res.status_code == 200:
        print("📲 메시지 전송 완료!")
    else:
        print(f"❌ 전송 실패: {res.text}")

# --- 실행 ---
final_message = get_market_and_news()
send_telegram_message(final_message)
