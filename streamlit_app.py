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
    
    def make_authenticated_request(self, method, path, params=None):
        timestamp = str(int(time.time()))
        url = f"{self.base_url}{path}"
        
        if method == "GET" and params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            path_with_query = f"{path}?{query_string}"
            url = f"{self.base_url}{path_with_query}"
        else:
            path_with_query = path
        
        signature = self.generate_signature(method, path_with_query, timestamp)
        
        headers = {
            'api-key': self.api_key,
            'timestamp': timestamp,
            'signature': signature,
            'Content-Type': 'application/json',
            'User-Agent': 'BTC-Price-Tracker/1.0'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if self.debug:
                st.write(f"🔍 DEBUG: Request URL: {url}")
                st.write(f"🔍 DEBUG: Headers: {headers}")
                st.write(f"🔍 DEBUG: Status Code: {response.status_code}")
                st.write(f"🔍 DEBUG: Response: {response.text}")
            
            if response.status_code == 401:
                st.error("Authentication failed. Please check your API credentials.")
                return None
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
            return None
    
    def get_current_price(self):
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
    
    def get_price_at_time(self, target_datetime):
        """
        Fetch historical BTC price at a specific datetime (UTC) using /v2/history/candles endpoint
        """
        try:
            # Convert datetime to timestamp in seconds
            end_time = int(target_datetime.replace(tzinfo=timezone.utc).timestamp())
            start_time = end_time - 60  # 1-minute window before target time
            
            params = {
                "symbol": self.symbol,
                "resolution": "1M",  # 1-minute candles
                "start": start_time,
                "end": end_time
            }
            
            url = f"{self.base_url}/v2/history/candles"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if self.debug:
                st.write(f"🔍 DEBUG: Fetching price for {target_datetime} UTC")
                st.write("🔍 DEBUG: API URL:", response.url)
                st.write("🔍 DEBUG: API Response:", data)
            
            if data.get("success") and "result" in data:
                candles = data["result"]
                if candles:
                    # Use the close price of the last candle in range
                    return float(candles[-1]["close"])
            
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
    
    # Fetch current price
    with st.spinner("Fetching current BTC price..."):
        current_price = tracker.get_current_price()
    
    if current_price:
        st.metric("Current BTC Price", f"${current_price:,.2f}")
    else:
        st.stop()
    
    # Define target times (IST -> convert to UTC)
    today = datetime.now()
    am_time = datetime(today.year, today.month, today.day, 5, 29, 59) - timedelta(hours=5, minutes=30)
    pm_time = datetime(today.year, today.month, today.day, 17, 29, 59) - timedelta(hours=5, minutes=30)
    
    # Fetch historical prices
    with st.spinner("Fetching historical AM price..."):
        am_price = tracker.get_price_at_time(am_time)
    
    with st.spinner("Fetching historical PM price..."):
        pm_price = tracker.get_price_at_time(pm_time)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if am_price:
            am_change = tracker.calculate_percentage_change(am_price, current_price)
            st.metric(
                "vs 5:29:59 AM",
                f"${am_price:,.2f}",
                delta=f"{am_change:+.2f}%" if am_change is not None else "N/A"
            )
        else:
            st.error("Could not fetch AM price")
    
    with col2:
        if pm_price:
            pm_change = tracker.calculate_percentage_change(pm_price, current_price)
            st.metric(
                "vs 5:29:59 PM",
                f"${pm_price:,.2f}",
                delta=f"{pm_change:+.2f}%" if pm_change is not None else "N/A"
            )
        else:
            st.error("Could not fetch PM price")

if __name__ == "__main__":
    main()
