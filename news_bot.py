import requests
import os

# Твои данные из секретов GitHub
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

def get_latest_vc_article():
    """Получает последнюю статью с vc.ru через их API"""
    url = "https://api.vc.ru/v1.7/feed"
    params = {
        "per_page": 1,
        "sort": "date"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data and data.get('result'):
            article = data['result'][0]
            title = article.get('title', 'Без заголовка')
            link = f"https://vc.ru/{article.get('id')}"
            return title, link
    except Exception as e:
        print(f"Ошибка при получении статьи: {e}")
    
    return None, None

def send_to_telegram(title, link):
    """Отправляет статью в Telegram"""
    message = f"📰 **Новая статья на vc.ru**\n\n**{title}**\n\nЧитать: {link}"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return {"ok": False}

def main():
    print("🚀 Проверяем vc.ru...")
    title, link = get_latest_vc_article()
    
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
