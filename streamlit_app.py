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
        """Fetch current BTC price"""
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
        """
        Fetch the close price for the exact candle ending at target_datetime (UTC)
        """
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
        page_title="BTC Price Tracker - Historical Times",
        page_icon="₿",
        layout="wide"
    )
    
    st.title("₿ Bitcoin Price Tracker (Exact Historical Times)")
    
    debug_mode = st.checkbox("Enable Debug Mode", value=False)
    tracker = BTCPriceTracker(debug=debug_mode)
    
    with st.spinner("Fetching current BTC price..."):
        current_price = tracker.get_current_price()
    
    if current_price:
        st.metric("Current BTC Price", f"${current_price:,.2f}")
    else:
        st.stop()
    
    # Convert 5:29:59 IST & 5:29:59 PM IST to UTC
    today = datetime.now()
    am_time_utc = datetime(today.year, today.month, today.day, 5, 29, 0) - timedelta(hours=5, minutes=30)
    pm_time_utc = datetime(today.year, today.month, today.day, 17, 29, 0) - timedelta(hours=5, minutes=30)
    
    # Fetch exact close prices
    with st.spinner("Fetching 5:29 AM close price..."):
        am_price = tracker.get_exact_candle_close(am_time_utc)
    if am_price:
        st.success(f"✅ 5:29 AM Close Price (Delta API): ${am_price:,.2f}")
    
    with st.spinner("Fetching 5:29 PM close price..."):
        pm_price = tracker.get_exact_candle_close(pm_time_utc)
    if pm_price:
        st.success(f"✅ 5:29 PM Close Price (Delta API): ${pm_price:,.2f}")
    
    # Show % change
    col1, col2 = st.columns(2)
    
    with col1:
        if am_price:
            am_change = tracker.calculate_percentage_change(am_price, current_price)
            st.metric(
                "vs 5:29 AM",
                f"${am_price:,.2f}",
                delta=f"{am_change:+.2f}%" if am_change is not None else "N/A"
            )
    
    with col2:
        if pm_price:
            pm_change = tracker.calculate_percentage_change(pm_price, current_price)
            st.metric(
                "vs 5:29 PM",
                f"${pm_price:,.2f}",
                delta=f"{pm_change:+.2f}%" if pm_change is not None else "N/A"
            )

if __name__ == "__main__":
    main()
