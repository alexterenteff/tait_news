import feedparser
import requests
from datetime import datetime

# Настройки
RSS_FEED = "https://vc.ru/rss/all"  # RSS-лента всех новостей vc.ru
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

def get_latest_article():
    """Получает самую свежую статью с vc.ru через RSS"""
    feed = feedparser.parse(RSS_FEED)
    
    if not feed.entries:
        return None, None
    
    # Первая запись в RSS — самая новая
    latest = feed.entries[0]
    title = latest.title
    link = latest.link
    
    return title, link

def send_to_telegram(title, link):
    """Отправляет статью в Telegram"""
    message = f"📰 **Новая статья на vc.ru**\n\n**{title}**\n\nЧитать: {link}"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    response = requests.post(url, json=payload)
    return response.json()

def main():
    print("🚀 Проверяем vc.ru...")
    title, link = get_latest_article()
    
    if title and link:
        print(f"📰 Найдено: {title}")
        result = send_to_telegram(title, link)
        if result.get("ok"):
            print("✅ Отправлено в Telegram!")
        else:
            print(f"❌ Ошибка Telegram: {result}")
    else:
        print("❌ Не удалось получить статью")

if __name__ == "__main__":
    main()
