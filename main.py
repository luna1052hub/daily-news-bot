import os
import requests
from bs4 import BeautifulSoup
import json

# -------------------------------------------------------------
# 1. 깃허브 Secrets에 GEMINI_API_KEY를 등록하셨다면 자동으로 읽어옵니다.
# 2. 코드에 직접 넣으시려면 아래 따옴표 안에 키를 적어주세요.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "여기에_GEMINI_API_KEY_입력"

BOT_TOKEN = "8806819870:AAFfZZ5SZbjfK4EUWmpxsPYwR353FwrTn6w"
CHAT_ID = "8434942322"
# -------------------------------------------------------------

def analyze_news_impact_with_gemini(news_list):
    key = GEMINI_API_KEY.strip()
    
    # 키 입력 여부 즉시 검증
    if not key or key.startswith("여기에"):
        return "⚠️ [API 키 미입력] GEMINI_API_KEY 값이 설정되지 않았습니다."

    # Gemini 2.5 Flash 안정화 엔드포인트
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    news_text = "\n".join(news_list)
    prompt = f"다음 뉴스를 읽고 국내 증시 영향을 3줄로 짧게 예측해줘:\n{news_text}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        # 타임아웃 10초 지정
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if res.status_code == 200:
            result = res.json()
            return result['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            return f"⚠️ [API 응답 오류] 상태코드: {res.status_code}\n내용: {res.text[:200]}"
            
    except requests.exceptions.Timeout:
        return "⚠️ [통신 시간 초과] Gemini API 응답이 10초를 초과했습니다."
    except Exception as e:
        return f"⚠️ [시스템 에러] {e}"


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
        news_res = requests.get(news_url, headers=headers, timeout=5)
        news_soup = BeautifulSoup(news_res.text, 'html.parser')
        items = news_soup.find_all('item')

        count = 0
        for item in items:
            title_tag = item.find('title')
            if title_tag and title_tag.text.strip():
                count += 1
                title = title_tag.text.strip()
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
            stock_res = requests.get(stock_url, headers=headers, timeout=5)
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
