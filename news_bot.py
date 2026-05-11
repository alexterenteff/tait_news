import requests
import os
import sys
import re
import time

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# === НАСТРОЙКИ ===
TELEGRAM_CHANNELS = [
    "durov",
    "halikov",
    "ai_news_ru",
    "neural_network",
    "gpt_channel",
    "deeplearning_ru"
]

def improve_title_with_deepseek(original_title, retry=0):
    """Переписывает заголовок через DeepSeek R1 (OpenRouter)"""
    if not OPENROUTER_API_KEY:
        return original_title
    
    print(f"  🔄 DeepSeek запрос для: {original_title[:50]}...")
    
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
- без кавычек в ответе

Оригинал: {original_title}

Только заголовок, ничего лишнего."""
        
        payload = {
            "model": "deepseek/deepseek-r1:free",  # ← ИСПРАВЛЕНАЯ МОДЕЛЬ
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            improved = result['choices'][0]['message']['content'].strip()
            improved = improved.strip('"').strip("'")
            print(f"  ✅ DeepSeek ответ: {improved[:50]}...")
            if len(improved) > 5 and len(improved) <= 100:
                return improved
            else:
                print(f"  ⚠️ Ответ слишком короткий или длинный: {len(improved)} символов")
                return original_title
        elif response.status_code == 401:
            print(f"  ❌ Ошибка 401: неверный API-ключ OpenRouter")
            return original_title
        elif response.status_code == 429:
            print(f"  ⚠️ Лимит запросов DeepSeek, пробуем без улучшения")
            return original_title
        else:
            print(f"  ❌ Ошибка API: {response.status_code}")
            if retry < 2:
                print(f"  🔄 Повторная попытка {retry+1}/2 через 5 секунд...")
                time.sleep(5)
                return improve_title_with_deepseek(original_title, retry+1)
            return original_title
            
    except requests.exceptions.Timeout:
        print(f"  ❌ Таймаут запроса к DeepSeek")
        if retry < 2:
            print(f"  🔄 Повторная попытка {retry+1}/2 через 5 секунд...")
            time.sleep(5)
            return improve_title_with_deepseek(original_title, retry+1)
        return original_title
    except Exception as e:
        print(f"  ❌ Исключение: {e}")
        return original_title

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
    """Экранирует HTML-спецсимволы"""
    if not text:
        return text
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#39;')
    text = text.replace('{', '&#123;')
    text = text.replace('}', '&#125;')
    return text

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
                    
                    # Улучшаем заголовок через DeepSeek
                    improved_title = improve_title_with_deepseek(text[:200])
                    
                    # Если DeepSeek не сработал, оставляем оригинал
                    if not improved_title or len(improved_title) < 5:
                        improved_title = text[:120]
                    
                    articles.append({
                        'title': improved_title[:120] + ('...' if len(improved_title) > 120 else ''),
                        'link': post_link
                    })
            
            print(f"  @{channel_name}: найдено {len(articles)} новостей")
                    
    except Exception as e:
        print(f"  Ошибка {channel_name}: {e}")
    
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
    """Отправляет новости в Telegram канал (без источника, без предпросмотра)"""
    articles_to_send = articles[:10]
    
    if not articles_to_send:
        message = "🤖 Новостей об ИИ не найдено.\n\n📱 Подпишись: @tAiT_news"
    else:
        message = "🧠 <b>Свежие новости об ИИ</b>\n\n"
        for art in articles_to_send:
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
    print("🚀 Запуск бота с DeepSeek R1 (OpenRouter)...")
    print(f"📡 Канал: {CHANNEL_ID}")
    
    # === ДИАГНОСТИКА ===
    print("🔍 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
    if BOT_TOKEN:
        print(f"   ✅ TELEGRAM_BOT_TOKEN: НАЙДЕН")
    else:
        print("   ❌ TELEGRAM_BOT_TOKEN: НЕ НАЙДЕН")
    
    if CHANNEL_ID:
        print(f"   ✅ CHANNEL_ID: НАЙДЕН ({CHANNEL_ID})")
    else:
        print("   ❌ CHANNEL_ID: НЕ НАЙДЕН")
    
    if OPENROUTER_API_KEY:
        print(f"   ✅ OPENROUTER_API_KEY: НАЙДЕН (начинается с {OPENROUTER_API_KEY[:12]}...)")
    else:
        print("   ❌ OPENROUTER_API_KEY: НЕ НАЙДЕН")
    # ===================
    
    if not BOT_TOKEN or not CHANNEL_ID:
        print("❌ Ошибка: отсутствуют TELEGRAM_BOT_TOKEN или CHANNEL_ID")
        sys.exit(1)
    
    articles = get_all_news()
    print(f"📊 Всего новостей: {len(articles)}, отправим: {min(len(articles), 10)}")
    
    success = send_to_telegram(articles)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
