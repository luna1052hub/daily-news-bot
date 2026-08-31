import os
import requests
from bs4 import BeautifulSoup

# -------------------------------------------------------------
# GitHub Secrets에서 토큰과 CHAT_ID를 안전하게 불러옵니다.
# (Secrets가 없을 경우를 대비해 코드 내 기본값도 예비로 유지합니다)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "여기에_토큰을_직접_넣으셔도_됩니다")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8434942322")
# -------------------------------------------------------------

def get_market_and_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    msg_lines = []
    
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
            if title_tag:
                # CDATA 특수 태그 깔끔하게 제거
                title = title_tag.get_text(strip=True).replace("<![CDATA[", "").replace("]]>", "").strip()
                if title:
                    count += 1
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

    return "\n".join(msg_lines)


def send_telegram_message(message):
    token = BOT_TOKEN.strip()
    chat_id = CHAT_ID.strip()
    
    if not token or token == "여기에_토큰을_직접_넣으셔도_됩니다":
        print("❌ 오류: 텔레그램 BOT_TOKEN이 설정되지 않았습니다.")
        return

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
if __name__ == "__main__":
    final_message = get_market_and_news()
    send_telegram_message(final_message)
