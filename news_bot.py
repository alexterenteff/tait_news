import requests
import os
import json

# === ТВОИ СЕКРЕТЫ ИЗ GITHUB ===
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

def get_news_from_deepseek():
    """Получает свежие новости об ИИ через DeepSeek API с веб-поиском"""
    
    url = "https://api.deepseek.com/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    # Промпт для DeepSeek — просим найти и красиво оформить новости
    prompt = """Ты — редактор новостного канала об искусственном интеллекте.
    
Найди в интернете 5 самых важных новостей об ИИ, AI, нейросетях за последние сутки.

Для каждой новости укажи:
1. Заголовок
2. Краткое описание (1-2 предложения)
3. Ссылку на источник

Оформи ответ в таком формате:

🤖 **СВЕЖИЕ НОВОСТИ ИИ**

**1. [Заголовок]**
[Описание]
🔗 [Источник]

**2. [Заголовок]**
[Описание]
🔗 [Источник]

... и так до 5 новостей.

В конце добавь: 📱 Подпишись: @tAiT_news

Используй эмодзи по теме (🤖, 🧠, 💡, ⚡, 📰).
Ответ должен быть только на русском языке."""

    payload = {
        "model": "deepseek-chat",  # или deepseek-v4-flash для более быстрого ответа
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "tools": [
            {
                "type": "web_search_20250305",  # включает веб-поиск
                "name": "web_search",
                "max_uses": 3
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.7
    }
    
    try:
        print("🔍 Отправляем запрос DeepSeek с веб-поиском...")
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content']
            print("✅ DeepSeek успешно ответил")
            return message
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"Ответ: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка при запросе к DeepSeek: {e}")
        return None

def send_to_telegram(message):
    """Отправляет сообщение в Telegram канал"""
    
    if not message:
        message = "❌ Не удалось получить новости от DeepSeek. Попробуйте позже.\n\n📱 Подпишись: @tAiT_news"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False  # Пусть ссылки отображаются
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        if result.get("ok"):
            print("✅ Сообщение отправлено в Telegram")
        else:
            print(f"❌ Ошибка Telegram: {result}")
        return result
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return {"ok": False}

def main():
    print("🚀 Запуск бота на DeepSeek с веб-поиском...")
    
    # Проверяем наличие секретов
    if not BOT_TOKEN:
        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден")
        return
    if not CHANNEL_ID:
        print("❌ ОШИБКА: CHANNEL_ID не найден")
        return
    if not DEEPSEEK_API_KEY:
        print("❌ ОШИБКА: DEEPSEEK_API_KEY не найден")
        print("   Добавь его в Secrets в GitHub!")
        return
    
    print(f"✅ Все секреты на месте. Канал: {CHANNEL_ID}")
    
    # Получаем новости от DeepSeek
    news_message = get_news_from_deepseek()
    
    # Отправляем в Telegram
    result = send_to_telegram(news_message)
    
    if result.get("ok"):
        print("✅ Новости опубликованы в канале!")
    else:
        print("❌ Не удалось опубликовать новости")

if __name__ == "__main__":
    main()
