import os
import requests
from bs4 import BeautifulSoup
import json

# -------------------------------------------------------------
# GitHub Secrets 또는 직접 입력 중 작동합니다.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AQ.Ab8RN6K3WjcKpVeAW2tVf2lHjj0UHTHjq-MBbiEbaoBcjzmgAw"
BOT_TOKEN = "8806819870:AAFfZZ5SZbjfK4EUWmpxsPYwR353FwrTn6w"
CHAT_ID = "8434942322"
# -------------------------------------------------------------

def analyze_news_impact_with_gemini(news_list):
    key = GEMINI_API_KEY.strip() if GEMINI_API_KEY else ""
    
    print(f"DEBUG: 현재 설정된 API KEY 길이: {len(key)}")
    
    if not key or "여기에" in key or len(key) < 10:
        return "⚠️ [설정 오류] GEMINI_API_KEY가 정상적으로 전달되지 않았습니다. Secrets 설정 또는 코드 내 입력값을 확인해 주세요."

    # Gemini 1.5 Flash 최신 REST API 엔드포인트
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    news_text = "\n".join(news_list)
    prompt = f"다음 뉴스를 보고 국내 증시 영향과 전망을 3줄로 핵심만 요약 예측해줘:\n\n{news_text}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        print("DEBUG: Gemini API 요청 보내는 중...")
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        print(f"DEBUG: 응답 코드 = {res.status_code}")
        
        if res.status_code == 200:
            result = res.json()
            try:
                ai_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                return ai_text if ai_text else "⚠️ AI 응답이 비어있습니다."
            except Exception as parse_err:
                return f"⚠️ [파싱 에러] 결과 추출 실패: {parse_err}"
        else:
            return f"⚠️ [API 오류] 코드: {res.status_code}\n내용: {res.text}"
            
    except Exception as e:
        print(f"DEBUG: 예외 발생 = {e}")
        return f"⚠️ [시스템 예외 발생] {e}"


def get_market_and_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
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
            if title_tag and title_tag.text.strip():
                title = title_tag.text.strip()
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
        msg_lines.append(str(ai_analysis))
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
