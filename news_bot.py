import requests
import os
import sys
import re
import time

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
YC_API_KEY = os.environ.get("YC_API_KEY")      # ← API-ключ сервисного аккаунта
YC_FOLDER_ID = os.environ.get("YC_FOLDER_ID")  # ← folder-id из каталога

TELEGRAM_CHANNELS = ["deeplearning_ru"]

def improve_title_with_yandex_gpt(original_title):
    """Переписывает заголовок через Yandex GPT"""
    if not YC_API_KEY:
        print("  ⚠️ Нет API-ключа Yandex Cloud")
        return original_title
    
    if not YC_FOLDER_ID:
        print("  ⚠️ Нет folder-id Yandex Cloud")
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
            "modelUri": f"gpt://{YC_FOLDER_ID}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,
                "maxTokens": 100
            },
            "messages": [
                {"role": "system", "text": "Ты — редактор новостного канала, переписываешь заголовки кратко и с эмодзи."},
                {"role": "user", "text": prompt}
            ]
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            improved = result['result']['alternatives'][0]['message']['text'].strip()
            improved = improved.strip('"').strip("'")
            print(f"  ✅ Yandex GPT: {improved[:50]}...")
            if len(improved) > 5 and len(improved) <= 100:
                return improved
        else:
            print(f"  ❌ Ошибка: {response.status_code}")
            print(f"  {response.text[:200]}")
            
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    
    return original_title

def is_ai_news(text):
    keywords = ['openai', 'chatgpt', 'gpt', 'deepseek', 'gemini', 'claude', 
                'llama', 'нейросеть', 'нейронная сеть', 'ии', 'ai']
    return any(kw in text.lower() for kw in keywords)

def escape_html(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') if text else text

def get_news_from_telegram(channel_name, limit=3):
    articles = []
    url = f"https://t.me/s/{channel_name}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            html = response.text
            post_ids = re.findall(r'data-post="([^"]+)"', html)
            texts = re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', html, re.DOTALL)
            
            for i, t in enumerate(texts[:limit]):
                clean = re.sub(r'<[^>]+>', '', t)
                clean = clean.replace('&quot;', '"').replace('&amp;', '&').strip()
                if clean and len(clean) > 30 and is_ai_news(clean):
                    link = f"https://t.me/{post_ids[i]}" if i < len(post_ids) else f"https://t.me/{channel_name}"
                    improved = improve_title_with_yandex_gpt(clean[:200])
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
        print("❌ Добавь секреты YC_API_KEY и YC_FOLDER_ID в GitHub")
        sys.exit(1)
    
    articles = []
    for ch in TELEGRAM_CHANNELS:
        articles.extend(get_news_from_telegram(ch, 3))
    
    seen = set()
    unique = []
    for a in articles:
        if a['title'] not in seen:
            seen.add(a['title'])
            unique.append(a)
    
    print(f"📊 Новостей: {len(unique)}")
    send_to_telegram(unique)

if __name__ == "__main__":
    main()
