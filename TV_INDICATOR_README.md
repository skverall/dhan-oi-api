# NIFTY OI Indicator for TradingView

This indicator displays Open Interest change data across various time intervals for the NIFTY symbol. The indicator is displayed as an overlay on your chart.

## Setup

### 1. Server-side Update (Render)

You have already deployed the server-side on Render. Make sure the API is accessible at:
```
https://dhan-oi-api.onrender.com/tv_data?symbol=NIFTY
```

### 2. Setting up the Indicator in TradingView

1. Open TradingView and log into your account
2. Open a NIFTY chart or any other symbol you want to use the indicator for
3. Click "Pine Editor" at the bottom of the screen
4. Paste the code from the `tradingview_indicator.pine` file into the editor
5. Click "Save" and name the indicator, for example "NIFTY OI Changes"
6. Click "Add to Chart" to add the indicator to your chart

### 3. Limitations and Features

#### Please note:
- TradingView does not allow making HTTP requests directly from Pine Script
- To get data from external sources, you need to use one of these methods:

#### Option 1: Manual Updates (without TradingView Pro account)
1. Periodically check the data from the API manually
2. Update the values in the indicator settings

#### Option 2: Using TradingView Pro (recommended)
1. Set up a Webhook using an intermediary service (e.g., Zapier, Integromat)
2. Create an integration that will fetch data from our API and pass it to TradingView
3. Update the URL in the indicator settings to your webhook URL

## Data Interpretation

The indicator displays a table with the following data:
- **TF**: time frame (15min, 45min, 75min, 2hours, 4hours)
- **Change in price**: price change in percentage
- **Change in OI**: open interest change in percentage
- **Rvol**: relative volume
- **Relationship**: color coding of the relationship between price and OI changes

### Color Coding:
- **Green**: positive OI change (increasing interest)
- **Red**: negative OI change (decreasing interest)

### Trading Strategy:
1. **Price increase + OI increase (green)** = strong bullish trend
2. **Price increase + OI decrease (red)** = weak bullish trend, possible reversal
3. **Price decrease + OI increase (green)** = strong bearish trend
4. **Price decrease + OI decrease (red)** = weak bearish trend, possible reversal 