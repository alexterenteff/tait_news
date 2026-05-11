import os
import re
import feedparser
import requests
from datetime import datetime, timedelta
from openai import OpenAI
from bs4 import BeautifulSoup

# === НАСТРОЙКИ ===
RSS_SOURCES = [
    "https://habr.com/ru/rss/hub/ai/all/?fl=ru",  # резерв, но Хабр мы парсим напрямую
    "https://naked-science.ru/tags/iskusstvennyj-intellekt/feed",
    "https://www.ixbt.com/export/news/ai.rss",
    "https://robohunter.ru/feed.xml",
    "https://tproger.ru/feed/",
    "https://vc.ru/rss/all",
    "https://3dnews.ru/news/ai/export_rss_news/",
    "https://www.cnews.ru/rubric/ai/export_rss_news/"
]

# === ИНИЦИАЛИЗАЦИЯ DeepSeek ===
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

def parse_habr():
    """Парсит свежие новости с Хабра напрямую"""
    news_list = []
    url = "https://habr.com/ru/hub/ai/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Находим все статьи на странице
        articles = soup.find_all('article', class_=re.compile('post|article'))
        
        for article in articles[:15]:  # Берём максимум 15 статей
            try:
                # Заголовок и ссылка
                title_tag = article.find('a', class_=re.compile('title|link'))
                if not title_tag:
                    continue
                    
                title = title_tag.get_text(strip=True)
                link = title_tag.get('href')
                if link and not link.startswith('http'):
                    link = 'https://habr.com' + link
                
                # Дата публикации
                time_tag = article.find('time')
                pub_date = None
                if time_tag and time_tag.get('datetime'):
                    try:
                        # Парсим дату из атрибута datetime
                        pub_date = datetime.fromisoformat(time_tag['datetime'].replace('Z', '+00:00'))
                    except:
                        pass
                
                # Если даты нет, пропускаем статью
                if not pub_date:
                    continue
                
                # Оставляем только статьи за последний час
                one_hour_ago = datetime.now() - timedelta(hours=1)
                if pub_date > one_hour_ago:
                    news_list.append({
                        'title': title,
                        'link': link,
                        'summary': title,  # Краткое описание = заголовок
                        'published': pub_date,
                        'source': 'Habr (парсинг)'
                    })
            except Exception as e:
                print(f"Ошибка при парсинге статьи: {e}")
                
    except Exception as e:
        print(f"Ошибка при парсинге Хабра: {e}")
    
    return news_list

def fetch_news_from_rss(feed_url):
    """Загружает новости из RSS за последний час"""
    feed = feedparser.parse(feed_url)
    news_list = []
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    for entry in feed.entries:
        pub_date = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            pub_date = datetime(*entry.updated_parsed[:6])
        
        if pub_date and pub_date > one_hour_ago:
            news_list.append({
                'title': entry.title,
                'link': entry.link,
                'summary': entry.summary[:500] if hasattr(entry, 'summary') else '',
                'published': pub_date,
                'source': feed_url
            })
    return news_list

def collect_news():
    """Собирает новости со всех источников (парсинг + RSS)"""
    all_news = []
    seen_titles = set()  # Для удаления дубликатов
    
    # 1. Парсим Хабр напрямую
    print("Парсим Хабр...")
    habr_news = parse_habr()
    for news in habr_news:
        if news['title'] not in seen_titles:
            seen_titles.add(news['title'])
            all_news.append(news)
    print(f"Найдено новостей на Хабре: {len(habr_news)}")
    
    # 2. Собираем из RSS
    for source in RSS_SOURCES:
        try:
            print(f"Проверяю RSS: {source}")
            news = fetch_news_from_rss(source)
            for n in news:
                if n['title'] not in seen_titles:
                    seen_titles.add(n['title'])
                    all_news.append(n)
            print(f"  Найдено: {len(news)}")
        except Exception as e:
            print(f"Ошибка при загрузке {source}: {e}")
    
    return all_news

def generate_summary(news_list):
    """Генерирует сводку с помощью DeepSeek"""
    if not news_list:
        return "За последний час нет новых новостей об ИИ.\n\n📱 Подпишись: @tAiT"
    
    # Берем только первые 7 новостей, чтобы не перегружать API
    news_text = "\n\n".join([
        f"🔹 {item['title']}\n{item['link']}"
        for item in news_list[:7]
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
    # Убираем футер, так как он уже есть в случае "нет новостей",
    # но для обычных постов его не добавляем, чтобы не повторяться.
    # Если хочешь футер и здесь — раскомментируй строку ниже:
    # footer = "\n\n📱 Подпишись: @tAiT"
    return header + summary  # + footer

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

def main():
    print("🚀 Начинаем сбор новостей...")
    news = collect_news()
    print(f"📰 Всего найдено свежих новостей: {len(news)}")
    
    if news:
        print("🤖 Генерируем сводку через DeepSeek...")
        summary = generate_summary(news)
    else:
        summary = "За последний час нет новых новостей об ИИ.\n\n📱 Подпишись: @tAiT"
    
    print("📤 Отправляем в Telegram...")
    result = publish_to_telegram(summary)
    
    if result.get("ok"):
        print("✅ Готово! Пост опубликован.")
    else:
        print(f"❌ Ошибка при публикации: {result}")

if __name__ == "__main__":
    main()
