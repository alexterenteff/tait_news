import requests
import os
import sys
import re
import json
from datetime import datetime, timedelta, timezone

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
YC_API_KEY = os.environ.get("YC_API_KEY")
YC_FOLDER_ID = os.environ.get("YC_FOLDER_ID")

# === НАСТРОЙКИ ===
TELEGRAM_CHANNELS = [
    "vibecoding_tg",
    "deeplearning_ru"
]
NEWS_LIMIT = 15
MAX_AGE_DAYS = 2
MAX_POSTS_IN_MESSAGE = 10
HISTORY_FILE = "published.json"  # файл для хранения ID опубликованных новостей

def load_published_history():
    """Загружает список уже опубликованных новостей из файла"""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_published_history(history):
    """Сохраняет список опубликованных новостей в файл"""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def improve_title_with_yandex_gpt(original_title):
    if not YC_API_KEY or not YC_FOLDER_ID:
        return original_title

    try:
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {YC_API_KEY}",
            "x-folder-id": YC_FOLDER_ID,
            "Content-Type": "application/json"
        }

        prompt = f"Перепиши заголовок новости об ИИ: сделай короче (до 60 символов), добавь эмодзи в начало, сохрани смысл. Только заголовок. Оригинал: {original_title}"

        payload = {
            "modelUri": f"gpt://{YC_FOLDER_ID}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,
                "maxTokens": 100
            },
            "messages": [
                {"role": "system", "text": "Переписывай заголовки новостей об ИИ кратко и с эмодзи."},
                {"role": "user", "text": prompt}
            ]
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            improved = response.json()['result']['alternatives'][0]['message']['text'].strip()
            improved = improved.strip('"').strip("'")
            if 5 < len(improved) <= 100:
                return improved
    except Exception as e:
        print(f"  ⚠️ Ошибка Yandex GPT: {e}")
    
    return original_title

def is_ai_news(text):
    keywords = [
        'gpt', 'chatgpt', 'openai', 'deepseek', 'claude', 'llama', 'gemini', 'kling',
        'нейросеть', 'нейронная сеть', 'ии', 'ai', 'искусственный интеллект',
        'midjourney', 'dalle', 'yandex gpt', 'gigachat', 'vibecoding'
    ]
    return any(kw in text.lower() for kw in keywords)

def escape_html(text):
    if not text:
        return text
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def parse_telegram_date(date_str):
    try:
        if date_str.endswith('Z'):
            date_str = date_str[:-1] + '+00:00'
        return datetime.fromisoformat(date_str)
    except:
        return None

def is_fresh(post_date):
    if not post_date:
        return True
    now = datetime.now(timezone.utc)
    age = now - post_date
    return age.days <= MAX_AGE_DAYS

def get_news_from_telegram(channel_name, published_ids, limit=NEWS_LIMIT):
    """Парсит канал и возвращает только НЕопубликованные новости"""
    articles = []
    url = f"https://t.me/s/{channel_name}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            html = response.text
            post_ids = re.findall(r'data-post="([^"]+)"', html)
            texts = re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', html, re.DOTALL)
            dates = re.findall(r'<time datetime="([^"]+)"', html)
            
            for i, t in enumerate(texts[:limit]):
                clean = re.sub(r'<[^>]+>', '', t)
                clean = clean.replace('&quot;', '"').replace('&amp;', '&').strip()
                
                # Получаем уникальный ID поста
                post_unique_id = None
                if i < len(post_ids):
                    post_unique_id = post_ids[i]
                
                # Пропускаем, если уже опубликовано
                if post_unique_id and post_unique_id in published_ids:
                    print(f"  ⏭️ Уже опубликовано: {clean[:40]}... (ID: {post_unique_id})")
                    continue
                
                post_date = None
                if i < len(dates):
                    post_date = parse_telegram_date(dates[i])
                
                if not is_fresh(post_date):
                    continue
                
                if clean and len(clean) > 30 and is_ai_news(clean):
                    link = f"https://t.me/{post_ids[i]}" if i < len(post_ids) else f"https://t.me/{channel_name}"
                    print(f"  ✅ Новая новость: {clean[:60]}...")
                    improved = improve_title_with_yandex_gpt(clean[:200])
                    articles.append({
                        'title': improved[:120],
                        'link': link,
                        'unique_id': post_unique_id
                    })
    except Exception as e:
        print(f"❌ Ошибка {channel_name}: {e}")
    
    return articles

def send_to_telegram(articles):
    if not articles:
        msg = "🤖 Свежих новостей об ИИ не найдено.\n\n📱 Подпишись: @tAiT_news"
    else:
        msg = "🧠 <b>Свежие новости об ИИ</b>\n\n"
        for a in articles[:MAX_POSTS_IN_MESSAGE]:
            safe_title = escape_html(a['title'])
            msg += f"• <a href=\"{a['link']}\">{safe_title}</a>\n\n"
        msg += "📱 <a href=\"https://t.me/tAiT_news\">Подпишись: @tAiT_news</a>"
    
    try:
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
            "chat_id": CHANNEL_ID,
            "text": msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }, timeout=15)
        return r.json().get('ok', False), msg
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False, ""

def main():
    print("🚀 Бот с Yandex GPT (без дублей)")
    print(f"📡 Каналы: {', '.join(TELEGRAM_CHANNELS)}")
    
    # Загружаем историю опубликованных новостей
    published_ids = load_published_history()
    print(f"📚 Уже опубликовано новостей: {len(published_ids)}")
    
    if not BOT_TOKEN or not CHANNEL_ID:
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN или CHANNEL_ID не найдены")
        sys.exit(1)
    
    all_articles = []
    for channel in TELEGRAM_CHANNELS:
        print(f"\n--- Обработка @{channel} ---")
        articles = get_news_from_telegram(channel, published_ids, NEWS_LIMIT)
        all_articles.extend(articles)
    
    # Удаление дубликатов по заголовку (внутри текущей выборки)
    seen = set()
    unique_articles = []
    for a in all_articles:
        if a['title'] not in seen:
            seen.add(a['title'])
            unique_articles.append(a)
    
    if not unique_articles:
        print("\n📊 Новых новостей нет")
        sys.exit(0)
    
    print(f"\n📊 Найдено новых уникальных новостей: {len(unique_articles)}")
    print(f"📤 Отправляем в Telegram...")
    
    success, _ = send_to_telegram(unique_articles)
    
    if success:
        # Сохраняем ID опубликованных новостей
        for article in unique_articles:
            if article.get('unique_id'):
                published_ids.append(article['unique_id'])
        save_published_history(published_ids)
        print(f"✅ Готово! Сохранено {len(unique_articles)} новых ID")
    else:
        print("❌ Ошибка при отправке")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
