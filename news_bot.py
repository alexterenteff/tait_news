import requests
import os

# === ТВОИ СЕКРЕТЫ ИЗ GITHUB ===
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

def get_news():
    """Получает новости через конвертер RSS в JSON"""
    
    # Конвертер Aimylogic (бесплатный, не требует регистрации)
    converter_url = "https://tools.aimylogic.com/api/rss2json?url=https://vc.ru/rss/all"
    
    try:
        response = requests.get(converter_url, timeout=10)
        print(f"Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            news_data = response.json()
            print(f"Тип полученных данных: {type(news_data)}")
            
            # Если данные — это список (массив новостей)
            if isinstance(news_data, list):
                articles = []
                for item in news_data[:5]:  # берём первые 5 новостей
                    articles.append({
                        'title': item.get('title', 'Без заголовка'),
                        'link': item.get('link', '#')
                    })
                print(f"Найдено новостей: {len(articles)}")
                return articles
            else:
                print("Данные пришли не в виде списка")
                print(news_data[:200])  # покажем первые 200 символов для отладки
                return []
        else:
            print(f"Ошибка конвертера: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Ошибка при получении новостей: {e}")
        return []

def send_to_telegram(articles):
    """Отправляет новости в Telegram канал"""
    
    if not articles:
        message = "❌ Не удалось получить новости. Возможно, сайт vc.ru временно недоступен."
    else:
        message = "📰 **Свежие новости с vc.ru**\n\n"
        for art in articles:
            message += f"🔹 [{art['title']}]({art['link']})\n\n"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True  # чтобы ссылки не разворачивались
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        print(f"Результат отправки: {result.get('ok')}")
        return result
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return {"ok": False}

def main():
    print("🚀 Запуск бота...")
    print(f"CHANNEL_ID: {CHANNEL_ID}")
    print(f"BOT_TOKEN: {'есть' if BOT_TOKEN else 'НЕТ!!!'}")
    
    articles = get_news()
    result = send_to_telegram(articles)
    
    if result.get("ok"):
        print("✅ Пост успешно отправлен в канал!")
    else:
        print(f"❌ Ошибка: {result}")

if __name__ == "__main__":
    main()
