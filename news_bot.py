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

def improve_title_simple(title):
    """Простое улучшение заголовка без API (эмодзи + чистка)"""
    # Убираем мусор в конце
    title = re.sub(r'\s*[-–]\s*([A-Z][a-z]+(\s+[A-Z][a-z]+)*)$', '', title)
    title = re.sub(r'\s*\([^)]+\)$', '', title)
    title = re.sub(r'\s*—\s*$', '', title)
    title = re.sub(r'\s+$', '', title)
    
    # Добавляем эмодзи по ключевым словам
    emoji_map = [
        ('chatgpt', '🤖'), ('openai', '🤖'), ('gpt', '🤖'),
        ('claude', '🎨'), ('anthropic', '🎨'),
        ('gemini', '🔵'), ('google', '🔵'),
        ('deepseek', '🐋'), ('midjourney', '🎨'), ('dalle', '🎨'),
        ('kandinsky', '🎨'), ('yandex', '🟡'), ('sber', '🟢'),
        ('нейросеть', '🧠'), ('ии', '💡'), ('ai', '💡')
    ]
    
    title_lower = title.lower()
    for kw, emoji in emoji_map:
        if kw in title_lower:
            title = f"{emoji} {title}"
            break
    else:
        title = f"📰 {title}"
    
    # Сокращаем длинные заголовки
    if len(title) > 100:
        title = title[:97] + "..."
    
    return title

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

def escape_html(text):
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('"', '&quot;').replace("'", '&#39;')
    text = text.replace('{', '&#123;').replace('}', '&#125;')
    return text

def get_news_from_telegram(channel_name, limit=8):
    articles = []
    url = f"https://t.me/s/{channel_name}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            html = response.text
            post_ids = re.findall(r'data-post="([^"]+)"', html)
            texts = re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', html, re.DOTALL)
            
            cleaned = []
            for t in texts[:limit]:
                clean = re.sub(r'<[^>]+>', '', t)
                clean = clean.replace('&quot;', '"').replace('&amp;', '&')
                clean = clean.strip()
                if clean and len(clean) > 30:
                    cleaned.append(clean)
            
            for i, text in enumerate(cleaned[:limit]):
                if is_ai_news(text):
                    link = f"https://t.me/{post_ids[i]}" if i < len(post_ids) else f"https://t.me/{channel_name}"
                    articles.append({
                        'title': improve_title_simple(text[:150]),
                        'link': link,
                        'source': f"@{channel_name}"
                    })
            print(f"  @{channel_name}: релевантных {len(articles)}")
    except Exception as e:
        print(f"Ошибка {channel_name}: {e}")
    return articles

def get_all_news():
    all_news = []
    seen = set()
    for ch in TELEGRAM_CHANNELS:
        for item in get_news_from_telegram(ch, 8):
            if item['title'] not in seen:
                seen.add(item['title'])
                all_news.append(item)
    return all_news

def send_to_telegram(articles):
    articles = articles[:10]
    if not articles:
        msg = "🤖 Новостей об ИИ не найдено.\n\n📱 Подпишись: @tAiT_news"
    else:
        msg = "🧠 <b>Свежие новости об ИИ</b>\n\n"
        for a in articles:
            msg += f"• <a href=\"{a['link']}\">{escape_html(a['title'])}</a> <code>[{a['source']}]</code>\n\n"
        msg += "📱 <a href=\"https://t.me/tAiT_news\">Подпишись: @tAiT_news</a>"
    
    r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
        "chat_id": CHANNEL_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True
    }, timeout=15)
    return r.json().get('ok', False)

def main():
    print("🚀 Запуск бота (улучшение заголовков без API)...")
    if not BOT_TOKEN or not CHANNEL_ID:
        print("❌ Ошибка: нет секретов")
        sys.exit(1)
    articles = get_all_news()
    print(f"📊 Найдено {len(articles)} новостей, отправляем {min(len(articles), 10)}")
    ok = send_to_telegram(articles)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
