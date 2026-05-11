import requests
import os
import sys
import re

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
YC_API_KEY = os.environ.get("YC_API_KEY")
YC_FOLDER_ID = os.environ.get("YC_FOLDER_ID")

TELEGRAM_CHANNELS = ["deeplearning_ru"]

def improve_title_with_yandex_gpt(original_title):
    if not YC_API_KEY or not YC_FOLDER_ID:
        return original_title
    
    try:
        url = "https://llm.api.cloud.yandex.net/llm/v1alpha/chat/completions"
        headers = {
            "Authorization": f"Api-Key {YC_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"Перепиши заголовок: сделай короче (до 70 символов), добавь один эмодзи в начало. Без пояснений. Оригинал: {original_title}"
        
        # ИСПРАВЛЕНО: добавлен /latest в modelUri
        payload = {
            "modelUri": f"gpt://{YC_FOLDER_ID}/yandexgpt-lite/latest",
            "completionOptions": {
                "temperature": 0.7,
                "maxTokens": 100
            },
            "messages": [
                {"role": "system", "text": "Ты переписываешь заголовки новостей об ИИ кратко и с эмодзи."},
                {"role": "user", "text": prompt}
            ]
        }
        
        print(f"  📤 Отправка запроса к Yandex GPT...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"  📡 Статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'result' in result and 'alternatives' in result['result']:
                improved = result['result']['alternatives'][0]['message']['text'].strip()
                improved = improved.strip('"').strip("'")
                print(f"  ✅ Yandex GPT: {improved[:50]}...")
                if 5 < len(improved) <= 100:
                    return improved
            else:
                print(f"  ⚠️ Неожиданный формат ответа: {result}")
        else:
            print(f"  ❌ Ошибка {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"  ❌ Исключение: {e}")
    
    return original_title

def is_ai_news(text):
    keywords = ['gpt', 'chatgpt', 'openai', 'deepseek', 'claude', 'llama', 'gemini',
                'нейросеть', 'нейронная сеть', 'ии', 'ai', 'искусственный интеллект',
                'kling', 'midjourney', 'dalle', 'yandex gpt', 'gigachat']
    return any(kw in text.lower() for kw in keywords)

def escape_html(text):
    if not text:
        return text
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def get_news_from_telegram(channel_name, limit=3):
    articles = []
    url = f"https://t.me/s/{channel_name}"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if response.status_code == 200:
            html = response.text
            post_ids = re.findall(r'data-post="([^"]+)"', html)
            texts = re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', html, re.DOTALL)
            
            for i, t in enumerate(texts[:limit]):
                clean = re.sub(r'<[^>]+>', '', t)
                clean = clean.replace('&quot;', '"').replace('&amp;', '&').strip()
                if clean and len(clean) > 30 and is_ai_news(clean):
                    link = f"https://t.me/{post_ids[i]}" if i < len(post_ids) else f"https://t.me/{channel_name}"
                    original = clean[:200]
                    print(f"\n--- Обработка: {original[:60]}...")
                    improved = improve_title_with_yandex_gpt(original)
                    articles.append({'title': improved[:120], 'link': link})
    except Exception as e:
        print(f"Ошибка: {e}")
    return articles

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
    print("🚀 Бот с Yandex GPT")
    print(f"🔑 API ключ: {'✅' if YC_API_KEY else '❌'}")
    print(f"📁 Folder ID: {'✅' if YC_FOLDER_ID else '❌'}")
    
    if not YC_API_KEY or not YC_FOLDER_ID:
        print("❌ Секреты не найдены")
        sys.exit(1)
    
    articles = []
    for ch in TELEGRAM_CHANNELS:
        articles.extend(get_news_from_telegram(ch, 2))
    
    seen = set()
    unique = []
    for a in articles:
        if a['title'] not in seen:
            seen.add(a['title'])
            unique.append(a)
    
    print(f"\n📊 Новостей: {len(unique)}")
    send_to_telegram(unique)

if __name__ == "__main__":
    main()
