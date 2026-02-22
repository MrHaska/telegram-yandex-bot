import os
import json
import logging
import telebot
import requests
from typing import Dict, Any

# Настройка логирования для Yandex Cloud Functions
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Инициализация бота при старте функции (холодный старт)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
YAGPT_FOLDER_ID = os.environ.get('YAGPT_FOLDER_ID')
YAGPT_API_KEY = os.environ.get('YAGPT_API_KEY')

# Проверяем, что все переменные окружения заданы
if not all([BOT_TOKEN, YAGPT_FOLDER_ID, YAGPT_API_KEY]):
    logger.error("Missing required environment variables")
    # Не прерываем выполнение, но логируем ошибку

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)  # threaded=False важно для serverless

# Кэшируем промт для экономии ресурсов
SYSTEM_PROMPT = "Ты — полезный ассистент. Отвечай на вопросы пользователя кратко и по делу."

def call_yandex_gpt(user_message: str) -> str:
    """
    Функция для вызова Yandex GPT API
    Документация: https://cloud.yandex.ru/docs/yandexgpt/
    """
    if not YAGPT_API_KEY or not YAGPT_FOLDER_ID:
        return "Ошибка: не настроены параметры Yandex GPT"
    
    prompt = {
        "modelUri": f"gpt://{YAGPT_FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": "200"
        },
        "messages": [
            {
                "role": "system",
                "text": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "text": user_message
            }
        ]
    }
    
    try:
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {YAGPT_API_KEY}"
        }
        
        response = requests.post(url, headers=headers, json=prompt, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        # Парсим ответ от Yandex GPT
        gpt_response = result['result']['alternatives'][0]['message']['text']
        return gpt_response
        
    except requests.exceptions.Timeout:
        logger.error("Yandex GPT API timeout")
        return "Извините, сервис временно недоступен. Попробуйте позже."
    except Exception as e:
        logger.error(f"Error calling Yandex GPT: {str(e)}")
        return "Произошла ошибка при обращении к Yandex GPT."

# Обработчики команд бота
@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработка команды /start"""
    user_name = message.from_user.first_name
    welcome_text = (
        f"👋 Привет, {user_name}!\n\n"
        "Я бот на базе **Yandex GPT**, работающий на серверлес-технологиях "
        "Yandex Cloud. Я могу ответить на твои вопросы.\n\n"
        "Просто напиши мне что-нибудь, и я передам твой запрос нейросети!"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message):
    """Обработка команды /help"""
    help_text = (
        "📚 **Доступные команды:**\n"
        "/start - приветствие\n"
        "/help - эта справка\n\n"
        "Просто отправь любой текст, и я отвечу с помощью Yandex GPT."
    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    """
    Обработка всех текстовых сообщений.
    Передаем запрос в Yandex GPT и возвращаем ответ пользователю.
    """
    try:
        # Отправляем статус "печатает..."
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Получаем ответ от Yandex GPT
        gpt_answer = call_yandex_gpt(message.text)
        
        # Отправляем ответ пользователю
        bot.reply_to(message, gpt_answer)
        
    except Exception as e:
        logger.error(f"Error in message handler: {str(e)}")
        bot.reply_to(message, "Извините, произошла внутренняя ошибка.")

# Точка входа для Yandex Cloud Function
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Основная функция-обработчик для Yandex Cloud Functions.
    Получает HTTP-запрос от API Gateway и передает его боту.
    """
    try:
        # Парсим входящий запрос от Telegram (webhook)
        if event.get('httpMethod') == 'POST':
            # Yandex Cloud Functions передает тело запроса в base64
            if event.get('isBase64Encoded', False):
                import base64
                body = base64.b64decode(event['body']).decode('utf-8')
            else:
                body = event.get('body', '{}')
            
            # Преобразуем в JSON
            update = json.loads(body)
            
            # Передаем обновление в библиотеку telebot
            bot.process_new_updates([telebot.types.Update.de_json(update)])
            
            # Возвращаем успешный ответ для Telegram
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'ok': True})
            }
        else:
            # Неподдерживаемый метод
            return {
                'statusCode': 405,
                'body': json.dumps({'error': 'Method not allowed'})
            }
            
    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
