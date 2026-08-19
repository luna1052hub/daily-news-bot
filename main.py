import os
import requests
from bs4 import BeautifulSoup
import json

# -------------------------------------------------------------
# 1) GitHub Secrets 환경변수에서 키를 읽어옵니다.
# 2) Secrets 설정을 안 하셨다면 아래 따옴표 안에 직접 넣어주세요.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AQ.Ab8RN6K3WjcKpVeAW2tVf2lHjj0UHTHjq-MBbiEbaoBcjzmgAw"

BOT_TOKEN = "8806819870:AAFfZZ5SZbjfK4EUWmpxsPYwR353FwrTn6w"
CHAT_ID = "8434942322"
# -------------------------------------------------------------

def analyze_news_impact_with_gemini(news_list):
    key = GEMINI_API_KEY.strip()
    
    if not key or "여기에" in key:
        return "⚠️ [설정 오류] GEMINI_API_KEY가 입력되지 않았습니다."

    # Gemini 1.5 Flash 공식 엔드포인트
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    news_text = "\n".join(news_list)
    prompt = f"다음 뉴스 5개를 참고하여 국내 증시(삼성전자, SK하이닉스, KODEX 200 등)에 미칠 영향과 전망을 3줄로 요약 예측해줘:\n\n{news_text}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        
        if res.status_code == 200:
            result = res.json()
            try:
                ai_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                return ai_text if ai_text else "⚠️ AI 응답 텍스트가 비어있습니다."
            except (KeyError, IndexError):
                return f"⚠️ [응답 파싱 오류] 응답 구조 이상: {result}"
        else:
            # 실패 시 에러 사유를 텔레그램 메세지에 직접 출력
            try:
                err_msg = res.json().get('error', {}).get('message', res.text)
            except:
                err_msg = res.text
            return f"⚠️ [Gemini API 연결 실패]\n- 응답코드: {res.status_code}\n- 상세사유: {err_msg}"
            
    except requests.exceptions.Timeout:
        return "⚠️ [통신 에러] Gemini API 응답이 15초를 초과했습니다."
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
