# Dhan OI Server

Server for tracking and providing Open Interest data through the Dhan API.

## Installation

```
pip install -r requirements.txt
```

## Local Launch

```
python app.py
```

## Render Setup

1. Create a new web service
2. Specify the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
3. Configure environment variables:
   - `DHAN_TOKEN` - token for Dhan API access
   - `DHAN_CLIENT_ID` - Dhan client identifier
   - `DHAN_AUTH_TYPE` - authentication type (usually 2)
   - `DHAN_TICKERS` - list of tickers in format `SYMBOL:EXCHANGE:SECURITY_ID,SYMBOL2:EXCHANGE2:SECURITY_ID2`

## API

### Getting Open Interest Data

```
GET /get_oi?ticker=SYMBOL
```

Returns the current open interest for the specified ticker. 