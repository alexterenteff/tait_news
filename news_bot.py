import requests
import os
import feedparser
import re

# === ТВОИ СЕКРЕТЫ ИЗ GITHUB ===
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

def is_ai_related(title, summary):
    """Проверяет, относится ли новость к ИИ."""
    # Объединяем заголовок и описание, приводим к нижнему регистру
    text_to_check = f"{title} {summary}".lower()
    
    # Список ключевых слов (можно легко дополнять)
    keywords = [
        'ии', 'ai', 'искусственный интеллект', 'нейросеть', 'нейронная сеть',
        'машинное обучение', 'ml', 'deep learning', 'чат-бот', 'llm', 'gpt',
        'deepseek', 'аналитика данных', 'компьютерное зрение', 'робот',
        'автопилот', 'беспилотник', 'большие данные', 'big data', 'распознавание'
    ]
    
    # Ищем любое из ключевых слов как отдельное слово
    pattern = r'\b(' + '|'.join(keywords) + r')\b'
    return bool(re.search(pattern, text_to_check))

def get_news():
    """Получает новости из RSS-ленты vc.ru и фильтрует по теме ИИ"""
    
    # Используем главную RSS-ленту vc.ru
    rss_url = "https://vc.ru/rss/all"
    
    try:
        print(f"Загружаем RSS: {rss_url}")
        feed = feedparser.parse(rss_url)
        
        if feed.bozo:  # если есть ошибки парсинга
            print(f"Предупреждение при парсинге RSS: {feed.bozo_exception}")
        
        articles = []
        for entry in feed.entries[:20]:  # Проверяем последние 20 записей
            title = entry.get('title', '')
            summary = entry.get('summary', '')
            
            # Проверяем, относится ли новость к ИИ
            if is_ai_related(title, summary):
                articles.append({
                    'title': title,
                    'link': entry.get('link', '#')
                })
                print(f"✅ Найдена новость об ИИ: {title[:50]}...")
        
        print(f"📰 Всего найдено релевантных новостей: {len(articles)}")
        return articles
        
    except Exception as e:
        print(f"❌ Ошибка при получении новостей: {e}")
        return []

def send_to_telegram(articles):
    """Отправляет новости в Telegram канал"""
    
    if not articles:
        message = "🤖 За последний час не найдено новых новостей об искусственном интеллекте.\n\n📱 Подпишись: @tAiT"
    else:
        message = "🧠 **Свежие новости об ИИ**\n\n"
        for art in articles[:7]:  # Отправляем не больше 7 новостей за раз
            message += f"🔹 [{art['title']}]({art['link']})\n\n"
        
        message += "📱 Подпишись: @tAiT_news"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        if result.get("ok"):
            print("✅ Сообщение успешно отправлено в Telegram")
        else:
            print(f"❌ Ошибка Telegram: {result}")
        return result
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")
        return {"ok": False}

def main():
    print("🚀 Запуск бота для поиска новостей об ИИ...")
    
    # Проверяем наличие секретов
    if not BOT_TOKEN:
        print("❌ ОШИБКА: Не найден TELEGRAM_BOT_TOKEN")
        return
    if not CHANNEL_ID:
        print("❌ ОШИБКА: Не найден CHANNEL_ID")
        return
    
    print(f"✅ Telegram бот найден, канал: {CHANNEL_ID}")
    
    # Получаем и фильтруем новости
    articles = get_news()
    
    # Отправляем результат в Telegram
    result = send_to_telegram(articles)
    
    if result.get("ok"):
        print("✅ Работа успешно завершена!")
    else:
        print("❌ Произошла ошибка при отправке")

if __name__ == "__main__":
    main()
