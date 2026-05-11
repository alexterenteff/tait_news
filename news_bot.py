import requests
import os
import sys

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

def is_ai_news(title):
    blacklist = [
        'санкц', 'дуа липа', 'samsung', 'фитнес-трекер', 'whoop', 'oura',
        'onlyfans', 'авиаперевозк', 'github', 'день 153', 'день 154'
    ]
    title_lower = title.lower()
    for bad in blacklist:
        if bad in title_lower:
            return False
    
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
        'агент', 'агенты', 'rag', 'retrieval', 'fine-tuning'
    ]
    
    for kw in keywords:
        if kw in title_lower:
            return True
    return False

def get_news_from_vc():
    converter_url = "https://tools.aimylogic.com/api/rss2json?url=https://vc.ru/rss/all"
    articles = []
    try:
        response = requests.get(converter_url, timeout=15)
        if response.status_code == 200:
            news_data = response.json()
            if isinstance(news_data, list):
                for item in news_data[:25]:
                    title = item.get('title', '')
                    if title and is_ai_news(title):
                        articles.append({
                            'title': title,
                            'link': item.get('link', '#'),
                        })
    except Exception as e:
        print(f"Ошибка vc.ru: {e}")
    return articles

def get_news_from_habr():
    converter_url = "https://tools.aimylogic.com/api/rss2json?url=https://habr.com/ru/rss/hub/ai/all/?fl=ru"
    articles = []
    try:
        response = requests.get(converter_url, timeout=15)
        if response.status_code == 200:
            news_data = response.json()
            if isinstance(news_data, list):
                for item in news_data[:25]:
                    title = item.get('title', '')
                    if title and is_ai_news(title):
                        articles.append({
                            'title': title,
                            'link': item.get('link', '#'),
                        })
    except Exception as e:
        print(f"Ошибка Habr: {e}")
    return articles

def get_news():
    all_news = []
    all_news.extend(get_news_from_vc())
    all_news.extend(get_news_from_habr())
    
    seen = set()
    unique_news = []
    for art in all_news:
        if art['title'] not in seen:
            seen.add(art['title'])
            unique_news.append(art)
    
    return unique_news

def send_to_telegram(articles):
    try:
        if not articles:
            message = "🤖 Новостей об ИИ не найдено.\n\n📱 Подпишись: @tAiT_news"
        else:
            message = "🧠 Свежие новости об ИИ\n\n"
            for art in articles[:10]:
                message += f"• {art['title']}\n{art['link']}\n\n"
            message += "📱 Подпишись: @tAiT_news"
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHANNEL_ID,
            "text": message,
            "disable_web_page_preview": True
        }
        result = requests.post(url, json=payload, timeout=15).json()
        
        if result.get('ok'):
            print("✅ Сообщение отправлено")
        else:
            print(f"❌ Ошибка: {result}")
        return result.get('ok', False)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    print("🚀 Запуск бота...")
    
    if not BOT_TOKEN or not CHANNEL_ID:
        print("❌ Ошибка: нет секретов")
        sys.exit(1)
    
    articles = get_news()
    success = send_to_telegram(articles)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
