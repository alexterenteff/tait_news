import requests
import os
import sys

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

def is_ai_news(title):
    # Чёрный список — то, что точно не про ИИ
    blacklist = [
        'санкц', 'дуа липа', 'samsung', 'фитнес-трекер', 'whoop', 'oura',
        'onlyfans', 'авиаперевозк', 'github ограничени', 'день 153', 'день 154'
    ]
    title_lower = title.lower()
    for bad in blacklist:
        if bad in title_lower:
            print(f"❌ Отфильтровано (чёрный список): {title[:50]}...")
            return False
    
    # Белый список — ключевые слова по ИИ
    keywords = [
        'openai', 'chatgpt', 'gpt-4', 'gpt-5', 'sora', 'dalle',
        'deepseek', 'gemini', 'google ai', 'anthropic', 'claude',
        'meta ai', 'llama', 'microsoft ai', 'copilot', 'nvidia',
        'midjourney', 'stable diffusion', 'runway', 'pika labs',
        'yandex gpt', 'yandexart', 'gigachat', 'kandinsky', 'sber ai',
        'baidu', 'alibaba', 'qwen', 'kling ai', 'moonshot',
        'mistral ai', 'hugging face', 'perplexity ai',
        'ии', 'искусственный интеллект', 'нейросеть', 'нейронная сеть',
        'машинное обучение', 'ml', 'llm', 'большая языковая модель',
        'чат-бот', 'генеративный ии', 'компьютерное зрение',
        'распознавание лиц', 'автопилот', 'беспилотник',
        'агент', 'агенты', 'раг', 'retrieval', 'fine-tuning',
        'трансформер', 'диффузия', 'diffusion', 'latent'
    ]
    
    for kw in keywords:
        if kw in title_lower:
            print(f"✅ Прошло фильтр: {title[:50]}...")
            return True
    return False

def get_news():
    converter_url = "https://tools.aimylogic.com/api/rss2json?url=https://vc.ru/rss/all"
    try:
        response = requests.get(converter_url, timeout=15)
        print(f"Статус ответа: {response.status_code}")
        
        if response.status_code != 200:
            return None
            
        news_data = response.json()
        if not isinstance(news_data, list):
            return None
            
        articles = []
        for item in news_data[:30]:  # Проверяем 30 последних
            title = item.get('title', '')
            if title and is_ai_news(title):
                articles.append({
                    'title': title,
                    'link': item.get('link', '#')
                })
        
        print(f"📰 Найдено релевантных новостей: {len(articles)}")
        return articles
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def send_to_telegram(articles):
    try:
        if articles is None:
            message = "❌ Ошибка: не удалось получить данные"
        elif not articles:
            message = "🤖 Новостей об ИИ не найдено.\n\n📱 Подпишись: @tAiT_news"
        else:
            message = "🧠 Свежие новости об ИИ\n\n"
            for art in articles[:7]:
                message += f"• {art['title']}\n{art['link']}\n\n"
            message += "📱 Подпишись: @tAiT_news"
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHANNEL_ID,
            "text": message,
            "disable_web_page_preview": True
        }
        result = requests.post(url, json=payload, timeout=15).json()
        
        if not result.get('ok'):
            print(f"❌ Ошибка Telegram: {result}")
            return False
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    print("🚀 Запуск бота...")
    
    if not BOT_TOKEN or not CHANNEL_ID:
        print("❌ Ошибка: отсутствуют секреты!")
        sys.exit(1)
    
    articles = get_news()
    
    if articles is None:
        print("❌ Критическая ошибка")
        sys.exit(1)
    
    success = send_to_telegram(articles)
    
    if not success:
        print("❌ Ошибка при отправке")
        sys.exit(1)
    
    print("✅ Бот успешно отработал")
    sys.exit(0)

if __name__ == "__main__":
    main()
