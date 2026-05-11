import requests
import os

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

def is_ai_news(title):
    """Проверяет, похож ли заголовок на новость про ИИ"""
    keywords = [
        # Русские ключевые слова
        'ии', 'ai', 'искусственный интеллект', 'нейросеть', 'нейронная сеть',
        'машинное обучение', 'ml', 'большая языковая модель', 'llm', 'чат-бот',
        'компьютерное зрение', 'распознавание лиц', 'генеративный ии',
        
        # Названия AI-компаний (международные)
        'openai', 'chatgpt', 'gpt-4', 'gpt-5', 'sora', 'dalle', 'dall-e',
        'deepseek', 'googledeepmind', 'gemini', 'google ai',
        'anthropic', 'claude', 'meta ai', 'llama', 'meta llama',
        'microsoft ai', 'copilot', 'bing ai', 'bings',
        'amazon ai', 'aws ai', 'bedrock ai',
        'nvidia', 'nvidia ai', 'cuda', 'dgx',
        'xai', 'grok', 'elon mask ia',
        'midjourney', 'stable diffusion', 'stability ai',
        'hugging face', 'perplexity ai', 'character ai',
        'cohere', 'mistral ai', 'adept', 'runway ml',
        
        # Китайские AI-компании
        'baidu ernie', 'ernie bot', 'alibaba tongyi', 'qwen',
        'tencent hunyuan', 'kuaishou kling', 'kling ai',
        'moonshot ai', 'stepfun', 'zhipu ai', 'chatglm',
        'minimax', 'sensetime', 'megvii',
        'algorithm of thoughts', '01 ai', 'spark desk',
        
        # Российские AI-компании и проекты
        'yandex gpt', 'yandexart', 'yandex gpt', 'yandex ai',
        'sber ai', 'giga chat', 'gigachat', 'candinsky', 'kandinsky',
        'salute ai', 'sber gpt', 'sberdevice', 'smartmark',
        'vk ai', 'vkontakte ai', 'mail ru ai', 'mts ai',
        
        # Зарубежные AI-продукты
        'd-id', 'synthesia', 'hey gen', 'heyげん', 'pika labs', 'runway gen',
        'capcut ai', 'bytedance ai', 'tiktok ai',
        'replika', 'pi ai', 'inflection ai', 'glean',
        'cognition ai', 'devin ai', 'replit ai', 'cursor ai',
        'github copilot', 'codeium', 'tabnine', 'amazon q',
        
        # AI-железо и чипы
        'nvidia h100', 'nvidia b200', 'blackwell', 'amd instinct',
        'intel gaudi', 'apple m4 neural', 'qualcomm ai',
        
        # Технологии и исследования
        'transformer', 'diffusion', 'latent diffusion', 'vae',
        'rag', 'agent', 'multi modal', 'multimodal m',
        'agi', 'asi', 'superintelligence', 'alignment',
        'fine tuning', 'rlhf', 'constitutional ai', 'mechanistic' 'interpretability'
    ]
    
    title_lower = title.lower()
    for kw in keywords:
        if kw in title_lower:
            return True
    return False

def get_news():
    """Получает новости через конвертер Aimylogic"""
    converter_url = "https://tools.aimylogic.com/api/rss2json?url=https://vc.ru/rss/all"
    try:
        response = requests.get(converter_url, timeout=10)
        if response.status_code == 200:
            news_data = response.json()
            if isinstance(news_data, list):
                articles = []
                for item in news_data[:20]:  # проверяем 20 последних новостей
                    title = item.get('title', '')
                    if is_ai_news(title):
                        articles.append({
                            'title': title,
                            'link': item.get('link', '#')
                        })
                        print(f"✅ Найдено: {title[:60]}...")
                return articles
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    return []

def send_to_telegram(articles):
    if not articles:
        message = "🤖 За последнее время нет новостей об ИИ.\n\n📱 Подпишись: @tAiT_news"
    else:
        message = "🧠 **Свежие новости об ИИ**\n\n"
        for art in articles[:7]:  # отправляем не больше 7 новостей
            message += f"🔹 [{art['title']}]({art['link']})\n\n"
        message += "📱 Подпишись: @tAiT_news"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    return requests.post(url, json=payload).json()

def main():
    print("🚀 Запуск бота для поиска новостей об ИИ...")
    print(f"📡 Канал: {CHANNEL_ID}")
    articles = get_news()
    print(f"📰 Найдено новостей: {len(articles)}")
    result = send_to_telegram(articles)
    if result.get('ok'):
        print("✅ Отправлено успешно!")
    else:
        print(f"❌ Ошибка: {result}")

if __name__ == "__main__":
    main()
