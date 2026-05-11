import requests
import os
import sys
import re

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

# === НАСТРОЙКИ ===
TELEGRAM_CHANNELS = [
    "durov",
    "halikov",
    "ai_news_ru",
    "neural_network",
    "gpt_channel",
    "deeplearning_ru"
]

def is_ai_news(text):
    """Проверяет, относится ли текст к ИИ"""
    blacklist = [
        'санкц', 'дуа липа', 'samsung', 'фитнес-трекер', 'whoop', 'oura',
        'onlyfans', 'авиаперевозк', 'github', 'день 153', 'день 154'
    ]
    text_lower = text.lower()
    for bad in blacklist:
        if bad in text_lower:
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
        if kw in text_lower:
            return True
    return False

def escape_markdown(text):
    """Экранирует спецсимволы для MarkdownV2"""
    special_chars = r'([_*\[\]()~`>#+\-=|{}.!\\])'
    return re.sub(special_chars, r'\\\1', text)

def get_news_from_telegram(channel_name, limit=8):
    """Парсит Telegram-канал через веб-версию"""
    articles = []
    url = f"https://t.me/s/{channel_name}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            html = response.text
            
            post_pattern = r'data-post="([^"]+)"'
            text_pattern = r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>'
            
            post_ids = re.findall(post_pattern, html)
            texts = re.findall(text_pattern, html, re.DOTALL)
            
            cleaned_texts = []
            for t in texts[:limit]:
                clean = re.sub(r'<[^>]+>', '', t)
                clean = clean.replace('&quot;', '"').replace('&amp;', '&')
                clean = clean.strip()
                if clean and len(clean) > 30:
                    cleaned_texts.append(clean)
            
            for i, text in enumerate(cleaned_texts[:limit]):
                if is_ai_news(text):
                    post_link = f"https://t.me/{post_ids[i]}" if i < len(post_ids) else f"https://t.me/{channel_name}"
                    articles.append({
                        'title': text[:150] + ('...' if len(text) > 150 else ''),
                        'link': post_link,
                        'source': f"@{channel_name}"
                    })
            
            print(f"  @{channel_name}: найдено текстов {len(cleaned_texts)}, релевантных {len(articles)}")
                    
    except Exception as e:
        print(f"Ошибка Telegram-канала {channel_name}: {e}")
    
    return articles

def get_all_news():
    """Собирает новости из всех Telegram-каналов"""
    all_news = []
    seen_titles = set()
    
    print("📡 Сбор новостей из Telegram-каналов...")
    for channel in TELEGRAM_CHANNELS:
        news = get_news_from_telegram(channel, limit=8)
        for item in news:
            if item['title'] not in seen_titles:
                seen_titles.add(item['title'])
                all_news.append(item)
        print(f"  @{channel}: добавлено {len(news)} новостей")
    
    return all_news

def send_to_telegram(articles):
    """Отправляет новости в Telegram канал с кликабельными заголовками"""
    if not articles:
        message = "🤖 Новостей об ИИ не найдено.\n\n📱 Подпишись: @tAiT_news"
    else:
        message = "🧠 **Свежие новости об ИИ**\n\n"
        for art in articles[:15]:
            # Экранируем заголовок для MarkdownV2
            safe_title = escape_markdown(art['title'])
            # Ссылка экранируется автоматически, но скобки в ней нужно экранировать
            safe_link = art['link'].replace(')', '\\)').replace('(', '\\(')
            # Формируем кликабельный заголовок: [текст](ссылка)
            message += f"• [{safe_title}]({safe_link})\n\n"
        message += "📱 [Подпишись: @tAiT_news](https://t.me/tAiT_news)"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": False
    }
    
    try:
        result = requests.post(url, json=payload, timeout=15).json()
        if result.get('ok'):
            print("✅ Сообщение отправлено в Telegram")
        else:
            print(f"❌ Ошибка Telegram: {result}")
        return result.get('ok', False)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    print("🚀 Запуск бота для сбора новостей об ИИ (только Telegram)...")
    print(f"📡 Канал: {CHANNEL_ID}")
    
    if not BOT_TOKEN or not CHANNEL_ID:
        print("❌ Ошибка: отсутствуют секреты")
        sys.exit(1)
    
    articles = get_all_news()
    print(f"📊 Всего найдено уникальных новостей: {len(articles)}")
    
    if articles:
        print("📰 Первые 3 новости:")
        for art in articles[:3]:
            print(f"  - {art['title'][:60]}...")
    
    success = send_to_telegram(articles)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
