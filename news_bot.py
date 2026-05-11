import requests
import os
import sys
import re
import time
import json

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
YC_API_KEY = os.environ.get("YC_API_KEY")  # ← API-ключ сервисного аккаунта

# === НАСТРОЙКИ ===
TELEGRAM_CHANNELS = [
    "deeplearning_ru"
]

# Твой folder_id из Yandex Cloud (где создан сервисный аккаунт)
YANDEX_FOLDER_ID = "aje1g1ells11bc7c042q"  # ← ВСТАВЬ СВОЙ!

def improve_title_with_yandex_gpt(original_title, retry=0):
    """Переписывает заголовок через Yandex GPT с авторизацией по API-ключу"""
    if not YC_API_KEY:
        print("  ⚠️ Нет API-ключа Yandex Cloud")
        return original_title
    
    try:
        url = "https://llm.api.cloud.yandex.net/llm/v1alpha/chat/completions"
        headers = {
            "Authorization": f"Api-Key {YC_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Перепиши этот заголовок новости об ИИ, сделай его:
- короче (максимум 80 символов)
- с одним эмодзи в начале
- без потери смысла

Оригинал: {original_title}"""
        
        payload = {
            "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,
                "maxTokens": 100
            },
            "messages": [
                {
                    "role": "system",
                    "text": "Ты — редактор новостного канала, переписываешь заголовки кратко и с эмодзи."
                },
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }
        
        print(f"  ⏳ Запрос к Yandex GPT...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            improved = result['result']['alternatives'][0]['message']['text'].strip()
            improved = improved.strip('"').strip("'")
            print(f"  ✅ Yandex GPT: {improved[:50]}...")
            if len(improved) > 5 and len(improved) <= 100:
                return improved
            else:
                print(f"  ⚠️ Ответ не подходит по длине: {len(improved)} символов")
                return original_title
        elif response.status_code == 401:
            print(f"  ❌ Ошибка 401: неверный API-ключ Yandex Cloud")
            print(f"  Проверь секрет YC_API_KEY в GitHub Secrets")
            return original_title
        else:
            print(f"  ❌ Ошибка Yandex GPT: {response.status_code}")
            print(f"  Ответ: {response.text[:200]}")
            if retry < 2:
                print(f"  🔄 Повторная попытка {retry+1}/2 через 5 секунд...")
                time.sleep(5)
                return improve_title_with_yandex_gpt(original_title, retry+1)
            return original_title
            
    except Exception as e:
        print(f"  ❌ Исключение: {e}")
        return original_title

def is_ai_news(text):
    keywords = ['openai', 'chatgpt', 'gpt', 'deepseek', 'gemini', 'claude', 
                'llama', 'нейросеть', 'нейронная сеть', 'ии', 'ai', 
                'искусственный интеллект', 'kling', 'midjourney', 'dalle']
    text_lower = text.lower()
    for kw in keywords:
        if kw in text_lower:
            return True
    return False

def escape_html(text):
    if not text:
        return text
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def get_news_from_telegram(channel_name, limit=5):
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
                clean = clean.replace('&quot;', '"').replace('&amp;', '&').strip()
                if clean and len(clean) > 30:
                    cleaned.append(clean)
            
            for i, text in enumerate(cleaned[:limit]):
                if is_ai_news(text):
                    link = f"https://t.me/{post_ids[i]}" if i < len(post_ids) else f"https://t.me/{channel_name}"
                    original = text[:200]
                    print(f"\n--- Обработка новости ---")
                    print(f"📝 Оригинал: {original[:80]}...")
                    improved = improve_title_with_yandex_gpt(original)
                    print(f"✨ Результат: {improved[:80]}...")
                    articles.append({'title': improved[:120], 'link': link})
    except Exception as e:
        print(f"Ошибка {channel_name}: {e}")
    
    return articles

def get_all_news():
    all_news = []
    seen = set()
    for ch in TELEGRAM_CHANNELS:
        for item in get_news_from_telegram(ch, 3):
            if item['title'] not in seen:
                seen.add(item['title'])
                all_news.append(item)
    return all_news

def send_to_telegram(articles):
    if not articles:
        msg = "🤖 Новостей об ИИ не найдено.\n\n📱 Подпишись: @tAiT_news"
    else:
        msg = "🧠 <b>Свежие новости об ИИ</b>\n\n"
        for a in articles[:5]:
            msg += f"• <a href=\"{a['link']}\">{escape_html(a['title'])}</a>\n\n"
        msg += "📱 <a href=\"https://t.me/tAiT_news\">Подпишись: @tAiT_news</a>"
    
    r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
        "chat_id": CHANNEL_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True
    }, timeout=15)
    return r.json().get('ok', False)

def main():
    print("🚀 Запуск бота с Yandex GPT...")
    print(f"📡 Канал: {CHANNEL_ID}")
    print(f"🔑 Yandex Cloud API ключ: {'✅ НАЙДЕН' if YC_API_KEY else '❌ НЕТ'}")
    
    if YC_API_KEY:
        print(f"   Начинается с: {YC_API_KEY[:10]}...")
    
    if not BOT_TOKEN or not CHANNEL_ID:
        print("❌ Ошибка: нет TELEGRAM_BOT_TOKEN или CHANNEL_ID")
        sys.exit(1)
    
    if not YC_API_KEY:
        print("⚠️ Yandex GPT не будет работать — добавь секрет YC_API_KEY")
        print("   Создай API-ключ для сервисного аккаунта в Yandex Cloud")
    
    articles = get_all_news()
    print(f"\n📊 Всего новостей: {len(articles)}")
    
    if articles:
        print(f"\n📝 ПЕРВАЯ НОВОСТЬ ДЛЯ ОТПРАВКИ:")
        print(f"   {articles[0]['title']}")
    
    success = send_to_telegram(articles)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
