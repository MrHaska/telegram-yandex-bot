# telegram-yandex-bot

# Telegram Bot на Yandex Cloud + Yandex GPT

Этот бот демонстрирует использование бессерверных технологий Yandex Cloud и нейросети Yandex GPT.

## Архитектура решения

- **Telegram Bot API** — интерфейс взаимодействия с пользователями
- **Yandex API Gateway** — принимает webhook-запросы от Telegram
- **Yandex Cloud Function** — выполняет бизнес-логику на Python
- **Yandex GPT** — генерирует ответы на запросы пользователей
- **Yandex Lockbox** — безопасное хранение токенов и ключей

## Инструкция по развертыванию

### 1. Создание бота в Telegram
1. Найди в Telegram бота [@BotFather](https://t.me/BotFather)
2. Отправь команду `/newbot` и следуй инструкциям
3. Сохрани полученный токен (например, `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 2. Получение доступа к Yandex GPT
1. В [консоли Yandex Cloud](https://console.cloud.yandex.ru) создай каталог
2. В сервисе "Сервисные аккаунты" создай аккаунт с ролью `ai.languageModels.user`
3. Создай API-ключ для этого аккаунта и сохрани его
4. Скопируй ID каталога (Folder ID)

### 3. Создание секретов в Yandex Lockbox
1. В консоли Yandex Cloud перейди в сервис Lockbox
2. Создай новый секрет с именем `telegram-bot-secrets`
3. Добавь три ключа:
   - `BOT_TOKEN` = токен от BotFather
   - `YAGPT_FOLDER_ID` = ID твоего каталога
   - `YAGPT_API_KEY` = API-ключ для Yandex GPT

### 4. Создание Cloud Function
1. Перейди в сервис "Cloud Functions"
2. Нажми "Создать функцию", укажи имя `telegram-gpt-bot`
3. Выбери среду выполнения Python 3.11
4. В редакторе создай файлы `index.py` и `requirements.txt` с кодом из этого репозитория
5. В параметрах функции укажи:
   - **Таймаут**: 10 секунд
   - **Память**: 256 MB
   - **Сервисный аккаунт**: выбери созданный ранее
6. В разделе "Переменные окружения" добавь ссылку на секреты из Lockbox
7. Нажми "Создать версию"

### 5. Настройка API Gateway
1. Перейди в сервис "API Gateway"
2. Создай новый шлюз со спецификацией:

```yaml
openapi: 3.0.0
info:
  title: Telegram Bot API
  version: 1.0.0
paths:
  /telegram-webhook:
    post:
      x-yc-apigateway-integration:
        type: cloud_functions
        function_id: <ID_ТВОЕЙ_ФУНКЦИИ>
        service_account_id: <ID_СЕРВИСНОГО_АККАУНТА>
      operationId: telegramWebhook
```

3. Сохрани шлюз и скопируй его публичный URL

### 6. Установка webhook для Telegram
Выполни команду в терминале (замени токен и URL):

```bash
curl -X POST "https://api.telegram.org/bot<ТОКЕН_БОТА>/setWebhook?url=https://<ДОМЕН_API_GATEWAY>/telegram-webhook"
```

### 7. Тестирование
Напиши своему боту в Telegram любое сообщение. Он должен ответить с помощью Yandex GPT!

## Почему это заинтересует Яндекс?

- ✅ Использование **бессерверных технологий** (Yandex Cloud Functions, API Gateway)
- ✅ Интеграция с **Yandex GPT** — флагманским AI-продуктом Яндекса
- ✅ Применение **Lockbox** для безопасного хранения секретов
- ✅ Чистый, документированный код с обработкой ошибок
- ✅ Готовность к продакшену (логирование, таймауты, корректные ответы)
- ✅ Понимание архитектуры serverless-приложений
