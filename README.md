# DhanHQ Open Interest API Server

Сервер для получения данных об открытом интересе (Open Interest) через WebSocket API DhanHQ и предоставления этих данных для индикаторов TradingView.

## Особенности

- Автоматический поиск Security ID для новых тикеров
- WebSocket подключение к API DhanHQ для получения данных в реальном времени
- Расчёт изменений открытого интереса за различные интервалы времени
- REST API для индикаторов TradingView

## Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/your-username/dhan-oi-server.git
   cd dhan-oi-server
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Настройте файл `config.json` с вашими учетными данными DhanHQ:
   ```json
   {
     "token": "YOUR_DHAN_TOKEN",
     "client_id": "YOUR_CLIENT_ID",
     "auth_type": 2,
     "tickers": [
       {
         "symbol": "NIFTY",
         "exchange_segment": "NSE_FNO",
         "security_id": "13"
       },
       {
         "symbol": "BANKNIFTY",
         "exchange_segment": "NSE_FNO",
         "security_id": "25"
       }
     ]
   }
   ```

## Запуск

```bash
python app.py
```

Сервер будет доступен по адресу http://localhost:5000

## API Endpoints

### GET /get_oi?ticker=SYMBOL

Returns the current open interest for the specified ticker. 

## Автоматический поиск Security ID

Сервер теперь автоматически находит Security ID для тикеров, которых нет в конфигурации:

1. Когда индикатор TradingView запрашивает данные с новым тикером, сервер ищет его Security ID в файле `Cleaned_Ticker_Security_ID_List.csv`
2. Найденный Security ID автоматически добавляется в конфигурацию
3. WebSocket соединение перезапускается для подписки на данные нового тикера
4. Индикатор получает данные без необходимости ручной настройки

## Использование в TradingView

1. Создайте вебхук в TradingView Pro с URL:
   ```
   https://your-server-url.com/tv_data?symbol={{ticker}}
   ```

2. Используйте индикатор с файла `tradingview_indicator.pine`

3. Добавьте индикатор на график, и он автоматически будет показывать изменения открытого интереса

## Настройка индикатора TradingView

В настройках индикатора можно выбрать:
- Использовать текущий символ графика или кастомный
- Частоту обновления данных
- Отображение меток ошибок 