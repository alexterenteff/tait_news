import requests
import os
import sys
import re
from datetime import datetime, timedelta, timezone

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
YC_API_KEY = os.environ.get("YC_API_KEY")
YC_FOLDER_ID = os.environ.get("YC_FOLDER_ID")

# === НАСТРОЙКИ ===
TELEGRAM_CHANNELS = [
    "deeplearning_ru",
    "vibecoding_tg"
]
NEWS_LIMIT = 10           # Максимум новостей с канала (для парсинга)
MAX_AGE_HOURS = 24        # ← НОВОЕ: публикуем только новости за последние 24 часа

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
            print(f"  ✅ Yandex GPT: {improved[:50]}...")
            if 5 < len(improved) <= 100:
                return improved
        else:
            print(f"  ❌ Ошибка {response.status_code}")
    except Exception as e:
        print(f"  ⚠️ Ошибка: {e}")
    
    return original_title

def is_ai_news(text):
    keywords = ['gpt', 'chatgpt', 'openai', 'deepseek', 'claude', 'llama', 'gemini', 'kling',
                'нейросеть', 'нейронная сеть', 'ии', 'ai', 'искусственный интеллект',
                'midjourney', 'dalle', 'yandex gpt', 'gigachat', 'vibecoding']
    return any(kw in text.lower() for kw in keywords)

def escape_html(text):
    if not text:
        return text
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def parse_telegram_date(date_text):
    """Преобразует дату из формата Telegram в datetime объект"""
    # Форматы дат в веб-версии Telegram:
    # "2024-05-12T15:30:00+00:00" или "2024-05-12T15:30:00Z" или "15:30"
    try:
        # Если только время (сегодняшний пост)
        if re.match(r'^\d{2}:\d{2}$', date_text):
            now = datetime.now(timezone.utc)
            return now.replace(hour=int(date_text[:2]), minute=int(date_text[3:]), second=0, microsecond=0)
        # Полная дата с часовым поясом
        return datetime.fromisoformat(date_text.replace('Z', '+00:00'))
    except:
        return datetime.now(timezone.utc) - timedelta(days=1)  # если ошибка, считаем старым

def get_news_from_telegram(channel_name, limit=NEWS_LIMIT):
    """Парсит Telegram-канал и возвращает только свежие новости (за MAX_AGE_HOURS часов)"""
    articles = []
    url = f"https://t.me/s/{channel_name}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # Вычисляем пороговую дату
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=MAX_AGE_HOURS)
    print(f"  🔍 Берём новости не старше {MAX_AGE_HOURS} часов (с {cutoff_time.strftime('%Y-%m-%d %H:%M')})")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            html = response.text
            
            # Ищем ID постов, текст и дату
            post_ids = re.findall(r'data-post="([^"]+)"', html)
            texts = re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', html, re.DOTALL)
            dates = re.findall(r'<time datetime="([^"]+)"', html)
            
            print(f"  📡 Найдено {len(texts)} сообщений, проверяем даты...")
            
            fresh_count = 0
            for i, t in enumerate(texts[:limit]):
                # Проверяем, есть ли дата для этого поста
                post_date = None
                if i < len(dates):
                    post_date = parse_telegram_date(dates[i])
                
                # Если дата не найдена или пост слишком старый — пропускаем
                if post_date and post_date < cutoff_time:
                    print(f"  ⏭️ Старая новость от {post_date.strftime('%Y-%m-%d %H:%M')}, пропускаем")
                    continue
                
                # Очищаем текст
                clean = re.sub(r'<[^>]+>', '', t)
                clean = clean.replace('&quot;', '"').replace('&amp;', '&').strip()
                
                if clean and len(clean) > 30 and is_ai_news(clean):
                    link = f"https://t.me/{post_ids[i]}" if i < len(post_ids) else f"https://t.me/{channel_name}"
                    print(f"  ✅ Свежая новость ({post_date.strftime('%Y-%m-%d %H:%M') if post_date else 'дата неизвестна'}): {clean[:60]}...")
                    improved = improve_title_with_yandex_gpt(clean[:200])
                    articles.append({'title': improved[:120], 'link': link})
                    fresh_count += 1
                elif clean and len(clean) > 30:
                    print(f"  ⏭️ Не ИТ-новость: {clean[:50]}...")
            
            print(f"  📊 @{channel_name}: свежих новостей {fresh_count}")
    except Exception as e:
        print(f"❌ Ошибка парсинга {channel_name}: {e}")
    
    return articles

def send_to_telegram(articles):
    if not articles:
        msg = "🤖 Свежих новостей об ИИ не найдено.\n\n📱 Подпишись: @tAiT_news"
    else:
        msg = "🧠 <b>Свежие новости об ИИ</b>\n\n"
        for a in articles[:10]:
            msg += f"• <a href=\"{a['link']}\">{escape_html(a['title'])}</a>\n\n"
        msg += "📱 <a href=\"https://t.me/tAiT_news\">Подпишись: @tAiT_news</a>"
    
    r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
        "chat_id": CHANNEL_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True
    }, timeout=15)
    return r.json().get('ok', False)

def main():
    print("🚀 Бот с Yandex GPT и фильтром по времени")
    print(f"📡 Каналы: {', '.join(TELEGRAM_CHANNELS)}")
    print(f"⏰ Публикуем новости не старше {MAX_AGE_HOURS} часов")
    
    if not YC_API_KEY or not YC_FOLDER_ID:
        print("❌ Секреты YC_API_KEY или YC_FOLDER_ID не найдены")
        sys.exit(1)
    
    all_articles = []
    for channel in TELEGRAM_CHANNELS:
        print(f"\n--- Обработка канала @{channel} ---")
        articles = get_news_from_telegram(channel, NEWS_LIMIT)
        all_articles.extend(articles)
        print(f"📊 @{channel}: добавлено {len(articles)} свежих новостей")
    
    # Удаление дубликатов по заголовку
    seen = set()
    unique_articles = []
    for a in all_articles:
        if a['title'] not in seen:
            seen.add(a['title'])
            unique_articles.append(a)
    
    print(f"\n📊 Всего уникальных свежих новостей: {len(unique_articles)}")
    print(f"📤 Отправляем в Telegram...")
    
    success = send_to_telegram(unique_articles)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
