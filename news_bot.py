import requests
import os
import json
import time

# === ТВОИ СЕКРЕТЫ ИЗ GITHUB ===
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

def get_news_from_deepseek(retry_count=0):
    """
    Получает новости, используя deepseek-chat (не deepseek-reasoner!)
    Эта модель работает с веб-поиском стабильно и без ошибки reasoning_content.
    """
    
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    # Промпт для модели deepseek-chat
    prompt = """Ты — редактор новостного канала. Твоя задача — найти 5 самых свежих новостей об ИИ.
Действуй строго по алгоритму:
1. Сначала используй поисковый инструмент, чтобы найти актуальные новости о событиях за последние 1-2 дня.
2. После получения данных, НЕМЕДЛЕННО сформулируй ответ на русском языке.
3. НЕ пиши "я ищу", "я думаю" или "анализирую". Только готовый результат.
4. Если поиск не дал результатов, напиши "Новостей за последний час нет".

КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать "режим мышления". Отвечай сразу от лица ассистента.

Формат ответа (Markdown):
Для каждой новости:
**1. Заголовок новости**
Краткое описание.
🔗 [Источник](ссылка_на_источник)"""

    # Теперь используем модель deepseek-chat, которая работает со всем инструментарием без ошибок
    payload = {
        "model": "deepseek-chat",  # <-- КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: используем chat, а не reasoner
        "messages": [{"role": "user", "content": prompt}],
        "tools": [{"type": "web_search_20250305", "max_uses": 3}],
        "max_tokens": 2000,
        "temperature": 0.3  
    }
    
    try:
        print(f"🔍 Запрос к DeepSeek (попытка {retry_count + 1}/2)...")
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        
        if response.status_code == 200:
            result = response.json()
            # Пытаемся получить content
            message_content = result['choices'][0]['message'].get('content')
            
            if message_content and len(message_content.strip()) > 50:
                print("✅ DeepSeek вернул полноценный ответ.")
                return message_content
            else:
                # Проверяем, может быть, DeepSeek просто сказал, что ничего не нашёл?
                if message_content and "Новостей за последний час нет" in message_content:
                     print("⚠️ DeepSeek не нашёл новостей.")
                     return None
                else:
                    print(f"⚠️ DeepSeek вернул пустой или короткий ответ: '{message_content}'")
                    if retry_count < 1:
                        print("🔄 Повторная попытка через 10 секунд...")
                        time.sleep(10)
                        return get_news_from_deepseek(retry_count + 1)
                    else:
                        return None
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"Ответ: {response.text[:200]}...")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def clean_telegram_message(message):
    """Финальная очистка сообщения перед отправкой."""
    if not message:
        return "⚠️ Не удалось получить новости. DeepSeek не нашёл свежих событий. Попробуйте позже.\n\n📱 [Подпишись: @tAiT_news](https://t.me/tAiT_news)"
    
    # Удаляем пугающие пользователя фразы, которые иногда проскакивают
    import re
    message = re.sub(r'Я ищу...|Я думаю...|Я анализирую...|Поиск...', '', message, flags=re.IGNORECASE)
    message = message.strip()
    
    if len(message) < 30:
        return "⚠️ Новостей пока нет или ответ слишком короткий. Загляните позже!\n\n📱 [Подпишись: @tAiT_news](https://t.me/tAiT_news)"
    
    # Добавляем футер, если его нет
    if "@tAiT_news" not in message:
        message += "\n\n📱 [Подпишись: @tAiT_news](https://t.me/tAiT_news)"
    
    return message

def send_to_telegram(message):
    """Отправляет результат в Telegram"""
    final_message = clean_telegram_message(message)
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": final_message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    
    try:
        result = requests.post(url, json=payload, timeout=30).json()
        if result.get("ok"):
            print("✅ Сообщение отправлено в Telegram!")
        else:
            print(f"❌ Ошибка Telegram: {result}")
        return result
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return {"ok": False}

def main():
    print("🚀 Запуск бота с веб-поиском (модель deepseek-chat)...")
    
    if not all([BOT_TOKEN, CHANNEL_ID, DEEPSEEK_API_KEY]):
        print("❌ Ошибка: не хватает секретов!")
        return
    
    news = get_news_from_deepseek()
    send_to_telegram(news)

if __name__ == "__main__":
    main()
