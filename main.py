import requests
from bs4 import BeautifulSoup

# -------------------------------------------------------------
# 📌 확인된 정보가 적용되어 있습니다!
BOT_TOKEN = "8806819870:AAFfZZ5SZbjfK4EUWmpxsPYwR353FwrTn6w"
CHAT_ID = "8434942322"  # 👈 확인된 CHAT ID 입력 완료!
# -------------------------------------------------------------

def get_market_and_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    msg_lines = []
    
    # [1] 뉴스 수집 (매경 RSS)
    msg_lines.append("📰 오늘의 주요 뉴스")
    msg_lines.append("-" * 20)
    try:
        news_url = "https://www.mk.co.kr/rss/30000001/"
        news_res = requests.get(news_url, headers=headers)
        news_soup = BeautifulSoup(news_res.text, 'xml')
        items = news_soup.find_all('item')

        count = 0
        for item in items:
            title = item.find('title').text.strip()
            if title:
                count += 1
                msg_lines.append(f"{count}. {title}")
                if count == 5:
                    break
    except Exception as e:
        msg_lines.append("뉴스 수집 실패")

    msg_lines.append("\n📈 주요 증시 및 ETF")
    msg_lines.append("-" * 20)
    
    # [2] 주가 수집 (네이버 증권)
    stocks = {
        "삼성전자": "005930",
        "SK하이닉스": "000660",
        "KODEX 200": "069500"
    }

    for name, code in stocks.items():
        try:
            stock_url = f"https://finance.naver.com/item/main.naver?code={code}"
            stock_res = requests.get(stock_url, headers=headers)
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
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    res = requests.post(url, data=data)
    if res.status_code == 200:
        print("📲 [성공] 텔레그램으로 메세지가 전송되었습니다!")
    else:
        print(f"❌ [실패] 전송 오류: {res.text}")

# --- 실행 ---
final_message = get_market_and_news()
send_telegram_message(final_message)
