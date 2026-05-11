import requests
import os
import sys
import re

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
YC_API_KEY = os.environ.get("YC_API_KEY")
YC_FOLDER_ID = os.environ.get("YC_FOLDER_ID")

# === НАСТРОЙКИ ===
TELEGRAM_CHANNELS = [
    "deeplearning_ru",
    "vibecoding_tg"        # ← добавлен новый канал
]
NEWS_LIMIT = 6  # Количество новостей с канала

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

def get_news_from_telegram(channel_name, limit=NEWS_LIMIT):
    articles = []
    url = f"https://t.me/s/{channel_name}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            html = response.text
            post_ids = re.findall(r'data-post="([^"]+)"', html)
            texts = re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', html, re.DOTALL)
            
            print(f"📡 Парсинг @{channel_name}: найдено {len(texts)} сообщений")
            
            for i, t in enumerate(texts[:limit]):
                clean = re.sub(r'<[^>]+>', '', t)
                clean = clean.replace('&quot;', '"').replace('&amp;', '&').strip()
                if clean and len(clean) > 30 and is_ai_news(clean):
                    link = f"https://t.me/{post_ids[i]}" if i < len(post_ids) else f"https://t.me/{channel_name}"
                    print(f"  ✅ Релевантная новость: {clean[:60]}...")
                    improved = improve_title_with_yandex_gpt(clean[:200])
                    articles.append({'title': improved[:120], 'link': link})
                else:
                    print(f"  ⏭️ Пропущено (не ИИ или короткое): {clean[:40]}...")
    except Exception as e:
        print(f"❌ Ошибка парсинга {channel_name}: {e}")
    
    return articles

def send_to_telegram(articles):
    if not articles:
        msg = "🤖 Новостей об ИИ не найдено.\n\n📱 Подпишись: @tAiT_news"
    else:
        msg = "🧠 <b>Свежие новости об ИИ</b>\n\n"
        for a in articles[:NEWS_LIMIT]:
            msg += f"• <a href=\"{a['link']}\">{escape_html(a['title'])}</a>\n\n"
        msg += "📱 <a href=\"https://t.me/tAiT_news\">Подпишись: @tAiT_news</a>"
    
    r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
        "chat_id": CHANNEL_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True
    }, timeout=15)
    return r.json().get('ok', False)

def main():
    print("🚀 Бот с Yandex GPT")
    print(f"📡 Каналы: {', '.join(TELEGRAM_CHANNELS)}")
    print(f"📊 Лимит новостей с канала: {NEWS_LIMIT}")
    
    if not YC_API_KEY or not YC_FOLDER_ID:
        print("❌ Секреты YC_API_KEY или YC_FOLDER_ID не найдены")
        sys.exit(1)
    
    all_articles = []
    for channel in TELEGRAM_CHANNELS:
        print(f"\n--- Обработка канала @{channel} ---")
        articles = get_news_from_telegram(channel, NEWS_LIMIT)
        all_articles.extend(articles)
        print(f"📊 @{channel}: добавлено {len(articles)} новостей")
    
    # Удаление дубликатов по заголовку
    seen = set()
    unique_articles = []
    for a in all_articles:
        if a['title'] not in seen:
            seen.add(a['title'])
            unique_articles.append(a)
    
    print(f"\n📊 Всего уникальных новостей: {len(unique_articles)}")
    print(f"📤 Отправляем в Telegram...")
    
    success = send_to_telegram(unique_articles)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
