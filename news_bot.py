import requests
import os
import sys
import re
import time

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

TELEGRAM_CHANNELS = [
    "deeplearning_ru"  # пока только один канал для теста
]

def improve_title_with_deepseek(original_title, retry=0):
    """Переписывает заголовок через DeepSeek (OpenRouter)"""
    
    print(f"\n  🔵=== DeepSeek START ===🔵")
    print(f"  📝 Оригинал: {original_title[:80]}...")
    print(f"  🔑 API ключ: {'ЕСТЬ' if OPENROUTER_API_KEY else 'НЕТ'}")
    
    if not OPENROUTER_API_KEY:
        print(f"  ❌ Нет API-ключа, возвращаем оригинал")
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
        
        print(f"  ⏳ Отправка запроса к OpenRouter (таймаут 60 сек)...")
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        print(f"  📡 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            improved = result['choices'][0]['message']['content'].strip()
            improved = improved.strip('"').strip("'")
            print(f"  ✅ DeepSeek ответ: {improved[:80]}...")
            print(f"  📏 Длина ответа: {len(improved)} символов")
            
            if len(improved) > 5 and len(improved) <= 100:
                print(f"  ✨ ВОЗВРАЩАЕМ УЛУЧШЕННЫЙ ЗАГОЛОВОК ✨")
                print(f"  🔵=== DeepSeek END (успех) ===🔵\n")
                return improved
            else:
                print(f"  ⚠️ Ответ не подходит по длине, возвращаем оригинал")
                print(f"  🔵=== DeepSeek END (неудача) ===🔵\n")
                return original_title
        else:
            print(f"  ❌ Ошибка API: {response.status_code}")
            print(f"  📄 Текст ответа: {response.text[:200]}")
            if retry < 2:
                print(f"  🔄 Повторная попытка {retry+1}/2 через 5 секунд...")
                time.sleep(5)
                return improve_title_with_deepseek(original_title, retry+1)
            print(f"  🔵=== DeepSeek END (ошибка) ===🔵\n")
            return original_title
            
    except requests.exceptions.Timeout:
        print(f"  ❌ ТАЙМАУТ запроса к DeepSeek")
        if retry < 2:
            print(f"  🔄 Повторная попытка {retry+1}/2 через 5 секунд...")
            time.sleep(5)
            return improve_title_with_deepseek(original_title, retry+1)
        print(f"  🔵=== DeepSeek END (таймаут) ===🔵\n")
        return original_title
    except Exception as e:
        print(f"  ❌ ИСКЛЮЧЕНИЕ: {type(e).__name__}: {e}")
        print(f"  🔵=== DeepSeek END (исключение) ===🔵\n")
        return original_title

def is_ai_news(text):
    keywords = ['openai', 'chatgpt', 'deepseek', 'gemini', 'claude', 'llama', 'gpt', 'нейросеть', 'ии', 'ai']
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)

def escape_html(text):
    if not text:
        return text
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('"', '&quot;').replace("'", '&#39;')
    text = text.replace('{', '&#123;').replace('}', '&#125;')
    return text

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
            
            cleaned_texts = []
            for t in texts[:limit]:
                clean = re.sub(r'<[^>]+>', '', t)
                clean = clean.replace('&quot;', '"').replace('&amp;', '&').strip()
                if clean and len(clean) > 30:
                    cleaned_texts.append(clean)
            
            print(f"\n📡 Канал @{channel_name}: найдено {len(cleaned_texts)} текстов")
            
            for i, text in enumerate(cleaned_texts[:limit]):
                print(f"\n--- Новость {i+1} ---")
                print(f"📄 Исходный текст: {text[:100]}...")
                
                if is_ai_news(text):
                    print(f"✅ Текст релевантен ИИ")
                    post_link = f"https://t.me/{post_ids[i]}" if i < len(post_ids) else f"https://t.me/{channel_name}"
                    
                    original_title = text[:200]
                    print(f"🎨 Вызываем DeepSeek для заголовка...")
                    improved_title = improve_title_with_deepseek(original_title)
                    print(f"📝 Результат DeepSeek: {improved_title[:80]}...")
                    print(f"🔄 Оригинал: {original_title[:80]}...")
                    
                    if improved_title != original_title:
                        print(f"✨ ЗАГОЛОВОК ИЗМЕНИЛСЯ! ✨")
                    else:
                        print(f"⚠️ ЗАГОЛОВОК НЕ ИЗМЕНИЛСЯ")
                    
                    articles.append({
                        'title': improved_title[:120],
                        'link': post_link
                    })
                else:
                    print(f"❌ Текст не релевантен ИИ, пропускаем")
    except Exception as e:
        print(f"Ошибка {channel_name}: {e}")
    
    return articles

def get_all_news():
    all_news = []
    seen_titles = set()
    
    for channel in TELEGRAM_CHANNELS:
        news = get_news_from_telegram(channel, limit=2)
        for item in news:
            if item['title'] not in seen_titles:
                seen_titles.add(item['title'])
                all_news.append(item)
    return all_news

def send_to_telegram(articles):
    if not articles:
        message = "🤖 Новостей об ИИ не найдено.\n\n📱 Подпишись: @tAiT_news"
    else:
        message = "🧠 <b>Свежие новости об ИИ</b>\n\n"
        for art in articles[:5]:
            safe_title = escape_html(art['title'])
            message += f"• <a href=\"{art['link']}\">{safe_title}</a>\n\n"
        message += "📱 <a href=\"https://t.me/tAiT_news\">Подпишись: @tAiT_news</a>"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
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
    print("=" * 60)
    print("🚀 ЗАПУСК БОТА С МАКСИМАЛЬНОЙ ДИАГНОСТИКОЙ")
    print("=" * 60)
    
    print(f"\n🔍 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
    print(f"   TELEGRAM_BOT_TOKEN: {'✅ НАЙДЕН' if BOT_TOKEN else '❌ НЕТ'}")
    print(f"   CHANNEL_ID: {'✅ НАЙДЕН' if CHANNEL_ID else '❌ НЕТ'}")
    print(f"   OPENROUTER_API_KEY: {'✅ НАЙДЕН' if OPENROUTER_API_KEY else '❌ НЕТ'}")
    
    if not BOT_TOKEN or not CHANNEL_ID:
        print("❌ Ошибка: нет секретов")
        sys.exit(1)
    
    articles = get_all_news()
    
    print(f"\n📊 ИТОГИ:")
    print(f"   Найдено новостей: {len(articles)}")
    
    if articles:
        print(f"\n📝 ПЕРВЫЙ ЗАГОЛОВОК ДЛЯ ОТПРАВКИ:")
        print(f"   {articles[0]['title']}")
        print(f"   Ссылка: {articles[0]['link']}")
    
    success = send_to_telegram(articles)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
