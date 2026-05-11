import os
import feedparser
import requests
from datetime import datetime, timedelta
from openai import OpenAI

# === НАСТРОЙКИ ===
RSS_SOURCES = [
    "https://habr.com/ru/rss/hub/ai/all/?fl=ru",
    "https://3dnews.ru/news/ai/export_rss_news/",
    "https://www.cnews.ru/rubric/ai/export_rss_news/",
    "https://robohunter.ru/feed.xml",
    "https://www.ixbt.com/export/news/ai.rss",
    "https://vc.ru/rss/all",                    
    "https://tproger.ru/feed/",                 
    "https://json.tv/rss",
]

# === ИНИЦИАЛИЗАЦИЯ ===
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

def fetch_news_from_rss(feed_url):
    """Загружает новости из RSS за последний час"""
    feed = feedparser.parse(feed_url)
    news_list = []
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    for entry in feed.entries:
        # Пытаемся получить дату
        pub_date = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            pub_date = datetime(*entry.updated_parsed[:6])
        
        # Если дата есть и новость свежая — добавляем
        if pub_date and pub_date > one_hour_ago:
            news_list.append({
                'title': entry.title,
                'link': entry.link,
                'summary': entry.summary[:500] if hasattr(entry, 'summary') else '',
                'source': feed_url
            })
    return news_list

def collect_news():
    """Собирает новости со всех источников"""
    all_news = []
    for source in RSS_SOURCES:
        try:
            news = fetch_news_from_rss(source)
            all_news.extend(news)
        except Exception as e:
            print(f"Ошибка {source}: {e}")
    return all_news

def generate_summary(news_list):
    """Генерирует сводку с помощью DeepSeek"""
    if not news_list:
            footer = f"\n\n📱 Подпишись: @tAiT"
    return header + summary + footer
        return "За последний час нет новых новостей об ИИ."
    
    # Берем только первые 5 новостей, чтобы не перегружать API
    news_text = "\n\n".join([
        f"🔹 {item['title']}\n{item['summary'][:200]}\n{item['link']}"
        for item in news_list[:5]
    ])
    
    prompt = f"""
    Ты — редактор новостного канала об ИИ.
    Сделай краткую сводку из этих новостей.
    Формат: каждая новость начинается с 🔹, затем заголовок, затем ссылка.
    Максимум 300 символов на новость.
    
    Новости:
    {news_text}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.5
        )
        summary = response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка DeepSeek: {e}")
        summary = "Не удалось сгенерировать сводку из-за ошибки API."
    
    header = f"🤖 Новости ИИ на {datetime.now().strftime('%H:%M')}\n\n"
    return header + summary

def publish_to_telegram(message):
    """Отправляет сообщение в Telegram канал"""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    channel_id = os.environ.get("CHANNEL_ID")
    
    if not bot_token or not channel_id:
        print("❌ Ошибка: не заданы TELEGRAM_BOT_TOKEN или CHANNEL_ID")
        return {"ok": False}
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": message,
        "parse_mode": "HTML"
    }
    return requests.post(url, json=payload).json()

# === ГЛАВНЫЙ ЗАПУСК ===
def main():
    print("🚀 Начинаем сбор новостей...")
    news = collect_news()
    print(f"📰 Найдено свежих новостей: {len(news)}")
    
    print("🤖 Генерируем сводку через DeepSeek...")
    summary = generate_summary(news)
    
    print("📤 Отправляем в Telegram...")
    result = publish_to_telegram(summary)
    
    if result.get("ok"):
        print("✅ Готово! Пост опубликован.")
    else:
        print(f"❌ Ошибка при публикации: {result}")

if __name__ == "__main__":
    main()
RSS_SOURCES = [
    "https://habr.com/ru/rss/hub/ai/all/?fl=ru",
    "https://3dnews.ru/news/ai/export_rss_news/",
    "https://www.cnews.ru/rubric/ai/export_rss_news/",
    "https://robohunter.ru/feed.xml",           # добавил
    "https://www.ixbt.com/export/news/ai.rss"   # добавил
]
