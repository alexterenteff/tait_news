import requests
import os
import sys

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

def is_ai_news(title):
    """Проверяет, относится ли новость к ИИ (чёрный список + белый список)"""
    
    # Чёрный список — то, что точно не про ИИ
    blacklist = [
        'санкц', 'дуа липа', 'samsung', 'фитнес-трекер', 'whoop', 'oura',
        'onlyfans', 'авиаперевозк', 'github', 'день 153', 'день 154',
        'день 155', 'день 156'
    ]
    title_lower = title.lower()
    for bad in blacklist:
        if bad in title_lower:
            print(f"❌ Отфильтровано (чёрный список): {title[:50]}...")
            return False
    
    # Белый список — ключевые слова по ИИ
    keywords = [
        # AI-компании (международные)
        'openai', 'chatgpt', 'gpt-4', 'gpt-5', 'sora', 'dalle',
        'deepseek', 'gemini', 'google ai', 'anthropic', 'claude',
        'meta ai', 'llama', 'microsoft ai', 'copilot', 'nvidia',
        'midjourney', 'stable diffusion', 'runway', 'pika labs',
        'mistral ai', 'hugging face', 'perplexity ai',
        # AI-компании (Китай)
        'baidu', 'alibaba', 'qwen', 'kling ai', 'moonshot',
        # AI-компании (Россия)
        'yandex gpt', 'yandexart', 'gigachat', 'kandinsky', 'sber ai',
        # Русские термины
        'ии', 'искусственный интеллект', 'нейросеть', 'нейронная сеть',
        'машинное обучение', 'ml', 'llm', 'большая языковая модель',
        'чат-бот', 'генеративный ии', 'компьютерное зрение',
        'распознавание лиц', 'автопилот', 'беспилотник',
        # Технические термины
        'агент', 'агенты', 'раг', 'retrieval', 'fine-tuning',
        'трансформер', 'диффузия', 'diffusion', 'latent'
    ]
    
    for kw in keywords:
        if kw in title_lower:
            print(f"✅ Прошло фильтр: {title[:50]}...")
            return True
    return False

def get_news_from_vc():
    """Получает новости с vc.ru через конвертер Aimylogic"""
    converter_url = "https://tools.aimylogic.com/api/rss2json?url=https://vc.ru/rss/all"
    articles = []
    try:
        print("📡 Запрос к vc.ru...")
        response = requests.get(converter_url, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ vc.ru вернул {response.status_code}")
            return []
            
        news_data = response.json()
        if not isinstance(news_data, list):
            print("❌ vc.ru: данные не в формате списка")
            return []
            
        for item in news_data[:25]:
            title = item.get('title', '')
            if title and is_ai_news(title):
                articles.append({
                    'title': title,
                    'link': item.get('link', '#'),
                    'source': 'vc.ru'
                })
        print(f"📰 vc.ru: найдено {len(articles)} новостей")
    except Exception as e:
        print(f"❌ Ошибка vc.ru: {e}")
    return articles

def get_news_from_habr():
    """Получает новости с Habr через конвертер Aimylogic"""
    converter_url = "https://tools.aimylogic.com/api/rss2json?url=https://habr.com/ru/rss/hub/ai/all/?fl=ru"
    articles = []
    try:
        print("📡 Запрос к Habr...")
        response = requests.get(converter_url, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ Habr вернул {response.status_code}")
            return []
            
        news_data = response.json()
        if not isinstance(news_data, list):
            print("❌ Habr: данные не в формате списка")
            return []
            
        for item in news_data[:25]:
            title = item.get('title', '')
            if title and is_ai_news(title):
                articles.append({
                    'title': title,
                    'link': item.get('link', '#'),
                    'source': 'habr'
                })
        print(f"📰 Habr: найдено {len(articles)} новостей")
    except Exception as e:
        print(f"❌ Ошибка Habr: {e}")
    return articles

def get_news():
    """Собирает новости из всех источников и удаляет дубликаты"""
    all_news = []
    
    # Собираем из всех источников
    all_news.extend(get_news_from_vc())
    all_news.extend(get_news_from_habr())
    
    # Удаляем дубликаты по заголовкам
    seen = set()
    unique_news = []
    for art in all_news:
        if art['title'] not in seen:
            seen.add(art['title'])
            unique_news.append(art)
    
    print(f"📊 Всего уникальных новостей: {len(unique_news)}")
    return unique_news

def send_to_telegram(articles):
    """Отправляет новости в Telegram канал (без Markdown)"""
    try:
        if articles is None:
            message = "❌ Ошибка: не удалось получить данные от RSS-конвертера"
        elif not articles:
            message = "🤖 Новостей об ИИ не найдено.\n\n📱 Подпишись: @tAiT_news"
        else:
            message = "🧠 Свежие новости об ИИ\n\n"
            for art in articles[:10]:  # Не больше 10 новостей за раз
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
            print("✅ Сообщение отправлено в Telegram")
        else:
            print(f"❌ Ошибка Telegram: {result}")
        return result.get('ok', False)
        
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

def main():
    print("🚀 Запуск бота для сбора новостей об ИИ...")
    print(f"📡 Канал: {CHANNEL_ID}")
    
    # Проверяем секреты
    if not BOT_TOKEN or not CHANNEL_ID:
        print("❌ Ошибка: отсутствуют секреты TELEGRAM_BOT_TOKEN или CHANNEL_ID")
        sys.exit(1)
    
    # Получаем новости
    articles = get_news()
    
    if articles is None:
        print("❌ Критическая ошибка: не удалось получить новости")
        sys.exit(1)
    
    # Отправляем в Telegram
    success = send_to_telegram(articles)
    
    if success:
        print("✅ Бот успешно отработал")
        sys.exit(0)
    else:
        print("❌ Ошибка при отправке в Telegram")
        sys.exit(1)

if __name__ == "__main__":
    main()
