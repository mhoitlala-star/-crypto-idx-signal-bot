
# Crypto IDX 1-Minute CALL/PUT Signal Bot

This project is an alert/signal bot. It does not place trades automatically.

## Important
The screenshot shows Binomo's "Crypto IDX", but Binomo may use a proprietary/internal price feed.
Therefore this bot cannot truthfully claim to read the exact Binomo Crypto IDX price unless you have
a legitimate data/API source for that exact instrument.

## Setup

1. Install Python 3.10+.
2. Install dependencies:
   pip install -r requirements.txt

3. Create a Telegram bot using Telegram's BotFather and obtain:
   TELEGRAM_BOT_TOKEN
   TELEGRAM_CHAT_ID

4. Set a candle data endpoint:
   DATA_URL

The endpoint must return JSON like:
[
  {"time": 1, "open": 641.8, "high": 642.0, "low": 641.6, "close": 641.9},
  ...
]

5. Run:
   python bot.py

## Signal logic
Uses:
- EMA 9 / EMA 21
- RSI 14
- MACD
- Closed-candle direction confirmation

It only alerts when multiple conditions agree. Otherwise it sends no trade signal.

## No 100% guarantee
A 1-minute market is noisy. Confidence is a heuristic score, not a probability of winning.
Do not use the confidence number as a guarantee.

## To connect the exact Binomo Crypto IDX
You need a lawful/official data source that provides OHLC candles for that exact instrument.
Do not scrape private endpoints, bypass authentication, or automate trades against platform rules.
