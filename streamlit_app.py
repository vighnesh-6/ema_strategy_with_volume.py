import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import datetime

st.set_page_config(page_title="EMA + Volume Scanner", layout="wide")
st.title("📊 Multi-Stock EMA Trend & Volume Spike Scanner")

# --- User input ---
stocks_input = st.text_area("Enter Tickers (e.g. APOLLOMICRO.NS, IDEAFORGE.NS):",
                            value="IDEAFORGE.NS, APOLLOMICRO.NS, AVANTEL.NS")
stocks = [s.strip().upper() for s in stocks_input.split(",") if s.strip()]

start = datetime.datetime.today() - datetime.timedelta(days=180)
end = datetime.datetime.today()

for ticker in stocks:
    st.header(f"📌 {ticker}")
    try:
        data = yf.download(ticker, start=start, end=end, auto_adjust=True)

        if data.empty:
            st.warning(f"No data for {ticker}")
            continue

        # EMAs
        data['EMA20'] = data['Close'].ewm(span=20).mean()
        data['EMA50'] = data['Close'].ewm(span=50).mean()
        data['EMA200'] = data['Close'].ewm(span=200).mean()

        # Signals
        data['Signal'] = 0
        data.loc[(data['EMA20'] > data['EMA50']) & (data['EMA20'].shift(1) <= data['EMA50'].shift(1)), 'Signal'] = 1
        data.loc[(data['EMA20'] < data['EMA50']) & (data['EMA20'].shift(1) >= data['EMA50'].shift(1)), 'Signal'] = -1

        # Volume Spike (NO ALIGN ERROR HERE)
        data['Volume_MA20'] = data['Volume'].rolling(20).mean()
        data['VolumeSpike'] = False
        mask = data['Volume_MA20'].notna()
        data.loc[mask, 'VolumeSpike'] = data.loc[mask, 'Volume'] > 2 * data.loc[mask, 'Volume_MA20']

        # Summary
        latest = data.iloc[-1]
        st.markdown(f"**Latest Close:** ₹{round(latest['Close'], 2)}")

        if not data[data['Signal'] != 0].empty:
            last_signal = data[data['Signal'] != 0].iloc[-1]
            signal_type = "🟢 BUY" if last_signal['Signal'] == 1 else "🔴 SELL"
            st.markdown(f"**Last Signal:** {signal_type} on {last_signal.name.date()} @ ₹{round(last_signal['Close'], 2)}")
        else:
            st.markdown("No crossover signal found.")

        if not data[data['VolumeSpike']].empty:
            last_spike = data[data['VolumeSpike']].iloc[-1]
            st.markdown(f"**Volume Spike:** {last_spike.name.date()} | Volume: {int(last_spike['Volume'])}")
        else:
            st.markdown("No significant volume spike found.")

        # Plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
        ax1.plot(data['Close'], label='Close', color='black')
        ax1.plot(data['EMA20'], label='EMA20', linestyle='--')
        ax1.plot(data['EMA50'], label='EMA50', linestyle='--')
        ax1.plot(data['EMA200'], label='EMA200', linestyle='--')
        ax1.plot(data[data['Signal'] == 1].index, data[data['Signal'] == 1]['Close'], '^', color='green', label='Buy')
        ax1.plot(data[data['Signal'] == -1].index, data[data['Signal'] == -1]['Close'], 'v', color='red', label='Sell')
        ax1.set_title("Price & EMAs")
        ax1.legend(); ax1.grid(True)

        ax2.bar(data.index, data['Volume'], color='gray', label='Volume')
        ax2.bar(data[data['VolumeSpike']].index, data[data['VolumeSpike']]['Volume'], color='orange', label='Spike')
        ax2.plot(data['Volume_MA20'], color='blue', linestyle='--', label='Vol MA20')
        ax2.set_title("Volume & Spikes")
        ax2.legend(); ax2.grid(True)

        st.pyplot(fig)

    except Exception as e:
        st.error(f"❌ Error analyzing {ticker}: {e}")

      
      
      
