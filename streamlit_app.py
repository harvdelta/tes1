import streamlit as st
import requests
import time
import hmac
import hashlib
from datetime import datetime, timedelta, timezone

class BTCPriceTracker:
    def __init__(self, debug=False):
        self.base_url = "https://api.delta.exchange"
        self.symbol = "BTCUSDT"
        self.debug = debug
        
        try:
            self.api_key = st.secrets["DELTA_API_KEY"]
            self.api_secret = st.secrets["DELTA_API_SECRET"]
            if self.debug:
                st.success("🔑 API credentials loaded successfully")
        except KeyError as e:
            st.error(f"❌ Missing API credential: {e}")
            st.stop()
    
    def generate_signature(self, method, path, timestamp, body=""):
        message = f"{method}{timestamp}{path}{body}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def get_current_price(self):
        """Fetch current BTC futures price"""
        try:
            url = f"{self.base_url}/v2/tickers/{self.symbol}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if self.debug:
                st.write("🔍 DEBUG: Current Price API Response", data)
            if data.get('success') and data.get('result'):
                return float(data['result']['close'])
            else:
                st.error("Failed to fetch current price")
                return None
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching current price: {e}")
            return None
    
    def get_exact_candle_close(self, target_datetime):
        """Fetch the close price for the exact candle ending at target_datetime (UTC)"""
        try:
            end_time = int(target_datetime.replace(tzinfo=timezone.utc).timestamp())
            start_time = end_time - 60  # 1-minute candle duration
            
            params = {
                "symbol": self.symbol,
                "resolution": "1m",
                "start": start_time,
                "end": end_time
            }
            
            url = f"{self.base_url}/v2/history/candles"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if self.debug:
                st.write(f"🔍 DEBUG: Fetching exact close for {target_datetime} UTC")
                st.write("🔍 DEBUG: API URL:", response.url)
                st.write("🔍 DEBUG: API Response:", data)
            
            if data.get("success") and "result" in data:
                candles = data["result"]
                if candles:
                    close_price = float(candles[-1]["close"])
                    return close_price
            return None
        
        except Exception as e:
            st.error(f"Error fetching historical price: {e}")
            return None
    
    def calculate_percentage_change(self, old_price, new_price):
        if old_price is None or new_price is None:
            return None
        return ((new_price - old_price) / old_price) * 100

def main():
    st.set_page_config(
        page_title="BTC Price Tracker - % Change from 5:29 AM",
        page_icon="₿",
        layout="wide"
    )
    
    st.title("₿ BTC Price Tracker – % Change from 5:29 AM IST")
    
    debug_mode = st.checkbox("Enable Debug Mode", value=False)
    tracker = BTCPriceTracker(debug=debug_mode)
    
    # Fetch current price
    with st.spinner("Fetching current BTC price..."):
        current_price = tracker.get_current_price()
    
    if not current_price:
        st.stop()
    
    # Fetch hidden AM price
    today = datetime.now()
    am_time_utc = datetime(today.year, today.month, today.day, 5, 29, 0) - timedelta(hours=5, minutes=30)
    with st.spinner("Fetching 5:29 AM price..."):
        am_price = tracker.get_exact_candle_close(am_time_utc)
    
    am_change = tracker.calculate_percentage_change(am_price, current_price) if am_price else None
    
    # Display only current price + % change
    if am_change is not None:
        st.metric("Current BTC Futures Price", f"${current_price:,.2f}", delta=f"{am_change:+.2f}%")
    else:
        st.metric("Current BTC Futures Price", f"${current_price:,.2f}", delta="N/A")

if __name__ == "__main__":
    main()
