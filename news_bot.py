import requests
import os
import json
import time

# === ТВОИ СЕКРЕТЫ ИЗ GITHUB ===
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

def get_news_from_deepseek(retry_count=0):
    """Получает новости от DeepSeek API с веб-поиском и повторной попыткой при сбое"""
    
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    prompt = """Ты — редактор новостного канала об искусственном интеллекте.
    
Найди в интернете 5 самых важных новостей об ИИ, AI, нейросетях за последние сутки.

Для каждой новости укажи:
1. Заголовок
2. Краткое описание (1-2 предложения)
3. Ссылку на источник

Оформи ответ в таком формате (используй Markdown):

**1. [Заголовок]**
[Описание]
🔗 [Источник]

**2. [Заголовок]**
[Описание]
🔗 [Источник]

... и так до 5 новостей.

В конце добавь: 📱 [Подпишись: @tAiT_news](https://t.me/tAiT_news)

Ответь строго на русском языке."""

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "tools": [{"type": "web_search_20250305", "max_uses": 3}],
        "max_tokens": 2000,
        "temperature": 0.7
    }
    
    try:
        print(f"🔍 Запрос к DeepSeek (попытка {retry_count + 1}/2)...")
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        
        if response.status_code == 200:
            result = response.json()
            # !!! КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: проверяем, что ответ не пустой и не равен None
            message = result['choices'][0]['message']['content']
            
            if message and len(message.strip()) > 50:  # Если ответ осмысленный
                print("✅ DeepSeek вернул осмысленный ответ.")
                return message
            else:
                print(f"⚠️ DeepSeek вернул пустой или слишком короткий ответ: '{message}'")
                if retry_count < 1:  # Пробуем еще раз
                    print("🔄 Повторная попытка через 10 секунд...")
                    time.sleep(10)
                    return get_news_from_deepseek(retry_count + 1)
                else:
                    return None
        else:
            print(f"❌ Ошибка API: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def send_to_telegram(message):
    """Отправляет результат в Telegram"""
    
    if not message or len(message.strip()) < 50:
        message = "⚠️ Не удалось получить актуальные новости от DeepSeek. Возможно, API временно перегружен. Попробуй позже.\n\n📱 [Подпишись: @tAiT_news](https://t.me/tAiT_news)"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
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
    print("🚀 Запуск бота с веб-поиском...")
    
    if not all([BOT_TOKEN, CHANNEL_ID, DEEPSEEK_API_KEY]):
        print("❌ Ошибка: не хватает секретов!")
        return
    
    news = get_news_from_deepseek()
    send_to_telegram(news)

if __name__ == "__main__":
    main()
