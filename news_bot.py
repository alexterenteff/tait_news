import requests
import os
import sys

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

def is_ai_news(title):
    keywords = [
        'openai', 'chatgpt', 'gpt-4', 'deepseek', 'gemini', 'google ai',
        'anthropic', 'claude', 'meta ai', 'llama', 'microsoft ai', 'copilot',
        'nvidia', 'midjourney', 'stable diffusion', 'runway', 'pika',
        'yandex gpt', 'gigachat', 'kandinsky', 'sber ai',
        'baidu', 'alibaba', 'qwen', 'kling ai', 'moonshot',
        'ии', 'ai', 'искусственный интеллект', 'нейросеть', 'нейронная сеть',
        'машинное обучение', 'llm', 'чат-бот'
    ]
    title_lower = title.lower()
    return any(kw in title_lower for kw in keywords)

def get_news():
    converter_url = "https://tools.aimylogic.com/api/rss2json?url=https://vc.ru/rss/all"
    try:
        response = requests.get(converter_url, timeout=15)
        print(f"Статус ответа: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Конвертер вернул {response.status_code}")
            return None
            
        news_data = response.json()
        
        if not isinstance(news_data, list):
            print(f"❌ Данные не список")
            return None
            
        articles = []
        for item in news_data[:25]:
            title = item.get('title', '')
            if title and is_ai_news(title):
                articles.append({
                    'title': title,
                    'link': item.get('link', '#')
                })
                print(f"✅ Найдено: {title[:50]}...")
        
        print(f"📰 Найдено релевантных новостей: {len(articles)}")
        return articles
        
    except Exception as e:
        print(f"❌ Ошибка в get_news: {e}")
        return None

def send_to_telegram(articles):
    try:
        if articles is None:
            message = "❌ Ошибка: не удалось получить данные от RSS-конвертера"
        elif not articles:
            message = "🤖 Новостей об ИИ не найдено.\n\n📱 Подпишись: @tAiT_news"
        else:
            message = "🧠 Свежие новости об ИИ\n\n"
            for art in articles[:7]:
                # Без Markdown — просто текст и ссылка
                message += f"• {art['title']}\n{art['link']}\n\n"
            message += "📱 Подпишись: @tAiT_news"
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHANNEL_ID,
            "text": message,
            "disable_web_page_preview": True
            # parse_mode НЕ указываем — обычный текст
        }
        result = requests.post(url, json=payload, timeout=15).json()
        print(f"Telegram ответ: {result}")
        
        if not result.get('ok'):
            print(f"❌ Ошибка Telegram: {result}")
            return False
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в send_to_telegram: {e}")
        return False

def main():
    print("🚀 Запуск бота...")
    
    if not BOT_TOKEN or not CHANNEL_ID:
        print("❌ Ошибка: отсутствуют секреты!")
        sys.exit(1)
    
    articles = get_news()
    
    if articles is None:
        print("❌ Критическая ошибка: get_news вернул None")
        sys.exit(1)
    
    success = send_to_telegram(articles)
    
    if not success:
        print("❌ Ошибка при отправке в Telegram")
        sys.exit(1)
    
    print("✅ Бот успешно отработал")
    sys.exit(0)

if __name__ == "__main__":
    main()
