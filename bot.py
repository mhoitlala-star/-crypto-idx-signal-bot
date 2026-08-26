
import os, time, requests
import pandas as pd
import numpy as np
from datetime import datetime

# Crypto IDX 1-minute signal bot
# IMPORTANT:
# - This is a SIGNAL/ALERT bot, not an auto-trading bot.
# - Binomo's Crypto IDX feed may be proprietary, so this template expects
#   OHLC candles from a compatible data endpoint or CSV.
# - It does NOT guarantee profit or 100% accuracy.

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
DATA_URL = os.getenv("DATA_URL", "")  # Endpoint returning OHLC data
SYMBOL = os.getenv("SYMBOL", "CRYPTO_IDX")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "10"))

def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()

def rsi(s, n=14):
    d = s.diff()
    gain = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def macd(s):
    m12, m26 = ema(s,12), ema(s,26)
    line = m12 - m26
    signal = ema(line,9)
    return line, signal

def get_candles():
    if not DATA_URL:
        raise RuntimeError("DATA_URL is not configured.")
    r = requests.get(DATA_URL, timeout=10)
    r.raise_for_status()
    data = r.json()

    # Supported common format:
    # [{"time":..., "open":..., "high":..., "low":..., "close":...}, ...]
    df = pd.DataFrame(data)
    needed = ["open","high","low","close"]
    if not all(c in df.columns for c in needed):
        raise ValueError("DATA_URL must return OHLC fields: open, high, low, close")
    for c in needed:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna().reset_index(drop=True)

def make_signal(df):
    if len(df) < 50:
        return "NO SIGNAL", 0, "Not enough candles"

    close = df["close"]
    e9, e21 = ema(close,9), ema(close,21)
    r = rsi(close,14)
    m, ms = macd(close)

    # Last CLOSED candle
    i = -2
    score_call = 0
    score_put = 0
    reasons = []

    if e9.iloc[i] > e21.iloc[i]:
        score_call += 1
        reasons.append("EMA9>EMA21")
    elif e9.iloc[i] < e21.iloc[i]:
        score_put += 1
        reasons.append("EMA9<EMA21")

    if r.iloc[i] > 52 and r.iloc[i] < 70:
        score_call += 1
        reasons.append("RSI bullish")
    elif r.iloc[i] < 48 and r.iloc[i] > 30:
        score_put += 1
        reasons.append("RSI bearish")

    if m.iloc[i] > ms.iloc[i]:
        score_call += 1
        reasons.append("MACD bullish")
    elif m.iloc[i] < ms.iloc[i]:
        score_put += 1
        reasons.append("MACD bearish")

    # Candle direction confirmation
    if close.iloc[i] > df["open"].iloc[i]:
        score_call += 1
        reasons.append("bull candle")
    elif close.iloc[i] < df["open"].iloc[i]:
        score_put += 1
        reasons.append("bear candle")

    best = max(score_call, score_put)
    if best < 3 or score_call == score_put:
        return "NO SIGNAL", int(best * 25), ", ".join(reasons)

    direction = "CALL" if score_call > score_put else "PUT"
    confidence = int(min(95, 50 + best * 10 + abs(score_call-score_put)*5))
    return direction, confidence, ", ".join(reasons)

def telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(text)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)

def main():
    last_candle_marker = None
    print(f"Starting {SYMBOL} 1-minute signal bot...")
    while True:
        try:
            df = get_candles()

            # Avoid duplicate signals: use the second-last candle as closed candle.
            marker = len(df)
            if marker != last_candle_marker:
                signal, conf, reason = make_signal(df)
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if signal != "NO SIGNAL":
                    msg = (
                        f"📡 {SYMBOL}\n"
                        f"⏱️ 1 MIN\n"
                        f"Signal: {'🟢' if signal=='CALL' else '🔴'} {signal}\n"
                        f"Confidence: {conf}%\n"
                        f"Time: {now}\n"
                        f"Reason: {reason}\n\n"
                        f"⚠️ Signal only — no guaranteed accuracy."
                    )
                    telegram(msg)
                else:
                    print(f"{now} | NO SIGNAL | {reason}")
                last_candle_marker = marker

        except Exception as e:
            print("ERROR:", e)

        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()
