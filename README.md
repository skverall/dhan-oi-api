<<<<<<< HEAD
# Dhan OI Server

Сервер для отслеживания и предоставления данных по открытому интересу (Open Interest) через API Dhan.

## Установка

```
pip install -r requirements.txt
```

## Запуск локально

```
python app.py
```

## Настройка на Render

1. Создайте новый веб-сервис
2. Укажите следующие настройки:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
3. Настройте переменные окружения:
   - `DHAN_TOKEN` - токен для доступа к API Dhan
   - `DHAN_CLIENT_ID` - идентификатор клиента Dhan
   - `DHAN_AUTH_TYPE` - тип аутентификации (обычно 2)
   - `DHAN_TICKERS` - список тикеров в формате `SYMBOL:EXCHANGE:SECURITY_ID,SYMBOL2:EXCHANGE2:SECURITY_ID2`

## API

### Получение данных по открытому интересу

```
GET /get_oi?ticker=SYMBOL
```

=======
# Dhan OI Server

Сервер для отслеживания и предоставления данных по открытому интересу (Open Interest) через API Dhan.

## Установка

```
pip install -r requirements.txt
```

## Запуск локально

```
python app.py
```

## Настройка на Render

1. Создайте новый веб-сервис
2. Укажите следующие настройки:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
3. Настройте переменные окружения:
   - `DHAN_TOKEN` - токен для доступа к API Dhan
   - `DHAN_CLIENT_ID` - идентификатор клиента Dhan
   - `DHAN_AUTH_TYPE` - тип аутентификации (обычно 2)
   - `DHAN_TICKERS` - список тикеров в формате `SYMBOL:EXCHANGE:SECURITY_ID,SYMBOL2:EXCHANGE2:SECURITY_ID2`

## API

### Получение данных по открытому интересу

```
GET /get_oi?ticker=SYMBOL
```

>>>>>>> e05c2fa (Initial commit)
Возвращает текущий открытый интерес для указанного тикера. 