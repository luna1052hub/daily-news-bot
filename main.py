import os
import requests
from bs4 import BeautifulSoup
import json
import re

# -------------------------------------------------------------
# ⚠️ 본인의 정보(토큰, ID, API키)를 확인해 주세요.
# GitHub Secrets를 사용 중이시면 GEMINI_API_KEY는 그대로 두셔도 됩니다.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AQ.Ab8RN6K3WjcKpVeAW2tVf2lHjj0UHTHjq-MBbiEbaoBcjzmgAw"
BOT_TOKEN = "8806819870:AAFfZZ5SZbjfK4EUWmpxsPYwR353FwrTn6w"
CHAT_ID = "8434942322"
# -------------------------------------------------------------

def clean_text(text):
    """텔레그램 메시지 전송 오류를 방지하기 위해 특수문자 정리"""
    if not text:
        return ""
    # 마크다운 특수문자 제거 (*, _, `, # 등)
    text = re.sub(r'[\*_`#]', '', text)
    return text.strip()

def analyze_news_impact_with_gemini(news_list):
    key = GEMINI_API_KEY.strip() if GEMINI_API_KEY else ""
    
    if not key or "여기에" in key or len(key) < 10:
        return "⚠️ [설정 오류] API 키가 입력되지 않았습니다. Secrets 설정 또는 코드 내 입력값을 확인해 주세요."

    # Gemini 1.5 Flash 최신 REST API 엔드포인트
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    news_text = "\n".join(news_list)
    prompt = f"다음 뉴스를 바탕으로 국내 증시(삼성전자, SK하이닉스 등)에 미칠 영향을 3줄로 핵심만 요약 예측해줘. 마크다운 기호(*, _ 등)는 사용하지 마세요:\n\n{news_text}"
    
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
                candidates = result.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        raw_text = parts[0].get('text', '')
                        cleaned = clean_text(raw_text)
                        return cleaned if cleaned else "⚠️ [결과 오류] AI 응답 텍스트가 비어있습니다."
                return f"⚠️ [응답 오류] AI 답변 구조 추출 실패: {result}"
            except Exception as parse_err:
                return f"⚠️ [파싱 오류] {parse_err}"
        else:
            try:
                err_msg = res.json().get('error', {}).get('message', res.text)
            except:
                err_msg = res.text
            return f"⚠️ [Gemini API 오류]\n코드: {res.status_code}\n사유: {err_msg}"
            
    except requests.exceptions.Timeout:
        return "⚠️ [통신 시간 초과] Gemini API 응답이 15초를 초과했습니다."
    except Exception as e:
        return f"⚠️ [시스템 예외 발생] {e}"


def get_market_and_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    msg_lines = []
    news_titles = []
    
    # [1] 뉴스 수집 (매경 RSS)
    msg_lines.append("📰 오늘의 주요 뉴스")
    msg_lines.append("-------------------------")
    try:
        news_url = "https://www.mk.co.kr/rss/30000001/"
        news_res = requests.get(news_url, headers=headers, timeout=10)
        news_soup = BeautifulSoup(news_res.text, 'html.parser')
        items = news_soup.find_all('item')

        count = 0
        for item in items:
            title_tag = item.find('title')
            if title_tag and title_tag.text.strip():
                title = clean_text(title_tag.text.strip())
                count += 1
                news_titles.append(f"- {title}")
                msg_lines.append(f"{count}. {title}")
                if count == 5:
                    break
    except Exception as e:
        msg_lines.append(f"뉴스 수집 실패: {e}")

    # [2] 주가 수집 (네이버 증권)
    msg_lines.append("\n📈 주요 증시 및 ETF")
    msg_lines.append("-------------------------")
    
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
    msg_lines.append("-------------------------")
    
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
    
    # parse_mode를 지정하지 않고 안전하게 순수 텍스트(Plain Text)로 전송
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
