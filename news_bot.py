import requests
import os
import sys
import re
import time

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

TELEGRAM_CHANNELS = [
    "durov", "halikov", "ai_news_ru", "neural_network", "gpt_channel", "deeplearning_ru"
]

def improve_title_with_deepseek(original_title, retry=0):
    if not OPENROUTER_API_KEY:
        return original_title
    
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        prompt = f"""Перепиши этот заголовок новости об ИИ, сделай его:
- короче (максимум 80 символов)
- с одним эмодзи в начале
- без потери смысла

Оригинал: {original_title}

Только заголовок, ничего лишнего."""
        
        payload = {
            "model": "deepseek/deepseek-chat:free",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            improved = response.json()['choices'][0]['message']['content'].strip('"').strip("'")
            if len(improved) > 5 and len(improved) <= 100:
                print(f"  ✨ DeepSeek: {original_title[:30]}... → {improved[:30]}...")
                return improved
        elif response.status_code == 401:
            print(f"  ❌ Ошибка 401: неверный API-ключ OpenRouter")
        elif retry < 1:
            time.sleep(2)
            return improve_title_with_deepseek(original_title, retry+1)
    except Exception as e:
        print(f"  ⚠️ DeepSeek ошибка: {e}")
    return original_title

def is_ai_news(text):
    blacklist = ['санкц', 'дуа липа', 'samsung', 'фитнес', 'whoop', 'oura', 'onlyfans', 'авиаперевозк', 'github', 'день 153', 'день 154']
    text_lower = text.lower()
    for bad in blacklist:
        if bad in text_lower:
            return False
    keywords = ['openai', 'chatgpt', 'gpt-4', 'sora', 'dalle', 'deepseek', 'gemini', 'anthropic', 'claude', 'meta ai', 'llama', 'microsoft ai', 'copilot', 'nvidia', 'midjourney', 'stable diffusion', 'kling ai', 'yandex gpt', 'gigachat', 'kandinsky', 'sber ai', 'baidu', 'alibaba', 'qwen', 'ии', 'искусственный интеллект', 'нейросеть', 'нейронная сеть', 'машинное обучение', 'ml', 'llm', 'чат-бот', 'генеративный ии']
    for kw in keywords:
        if kw in text_lower:
            return True
    return False

def escape_html(text):
    if not text:
        return text
    for ch in ('&', '<', '>', '"', "'", '{', '}'):
        text = text.replace(ch, f'&#{ord(ch)};')
    return text

def get_news_from_telegram(channel_name, limit=8):
    articles = []
    url = f"https://t.me/s/{channel_name}"
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if r.status_code == 200:
            post_ids = re.findall(r'data-post="([^"]+)"', r.text)
            texts = re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', r.text, re.DOTALL)
            cleaned = []
            for t in texts[:limit]:
                clean = re.sub(r'<[^>]+>', '', t)
                clean = clean.replace('&quot;', '"').replace('&amp;', '&').strip()
                if clean and len(clean) > 30:
                    cleaned.append(clean)
            for i, txt in enumerate(cleaned[:limit]):
                if is_ai_news(txt):
                    link = f"https://t.me/{post_ids[i]}" if i < len(post_ids) else f"https://t.me/{channel_name}"
                    improved = improve_title_with_deepseek(txt[:200])
                    articles.append({'title': improved[:120], 'link': link})
        print(f"  @{channel_name}: {len(articles)} новостей")
    except Exception as e:
        print(f"Ошибка {channel_name}: {e}")
    return articles

def get_all_news():
    all_news, seen = [], set()
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
            msg += f"• <a href=\"{a['link']}\">{escape_html(a['title'])}</a>\n\n"
        msg += "📱 <a href=\"https://t.me/tAiT_news\">Подпишись: @tAiT_news</a>"
    
    r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
        "chat_id": CHANNEL_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True
    }, timeout=15)
    return r.json().get('ok', False)

def main():
    print("🚀 Запуск бота с DeepSeek...")
    print(f"📡 Канал: {CHANNEL_ID}")
    print(f"🔑 OPENROUTER_API_KEY: {'✅ НАЙДЕН' if OPENROUTER_API_KEY else '❌ НЕ НАЙДЕН'}")
    
    if not BOT_TOKEN or not CHANNEL_ID:
        print("❌ Ошибка: нет TELEGRAM_BOT_TOKEN или CHANNEL_ID")
        sys.exit(1)
    
    if not OPENROUTER_API_KEY:
        print("⚠️ ВНИМАНИЕ: DeepSeek не будет работать без OPENROUTER_API_KEY")
        print("   Добавь секрет в GitHub: Settings → Secrets → Actions")
    
    articles = get_all_news()
    print(f"📊 Всего новостей: {len(articles)}, отправим: {min(len(articles), 10)}")
    success = send_to_telegram(articles)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
