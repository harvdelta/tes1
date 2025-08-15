import streamlit as st
import requests
import time
import hmac
import hashlib

class BTCPriceTracker:
    def __init__(self):
        self.base_url = "https://api.delta.exchange"
        self.symbol = "BTCUSDT"
        
        # Get API credentials from Streamlit secrets
        try:
            self.api_key = st.secrets["DELTA_API_KEY"]
            self.api_secret = st.secrets["DELTA_API_SECRET"]
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
            if data.get('success') and data.get('result'):
                return float(data['result']['close'])
            else:
                st.error("Failed to fetch current price")
                return None
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching current price: {e}")
            return None
    
    def calculate_percentage_change(self, old_price, new_price):
        if old_price is None or new_price is None:
            return None
        return ((new_price - old_price) / old_price) * 100

def main():
    st.set_page_config(
        page_title="BTC Price Tracker - Delta Exchange",
        page_icon="₿",
        layout="wide"
    )
    
    st.title("₿ Bitcoin Price Tracker")
    st.markdown("**Delta Exchange API Integration**")
    
    tracker = BTCPriceTracker()
    
    # API connection test
    st.subheader("🔧 API Connection Test")
    if st.button("Test API Connection"):
        with st.spinner("Testing API connection..."):
            result = tracker.make_authenticated_request("GET", "/v2/profile")
        if result:
            if result.get('success'):
                st.success("✅ API Connection Successful!")
                st.json(result.get('result', {}))
            else:
                st.error("❌ API returned unsuccessful response")
                st.json(result)
        else:
            st.error("❌ API Connection Failed")
    
    # Current price
    st.subheader("📊 Current BTC Price")
    with st.spinner("Fetching current price..."):
        current_price = tracker.get_current_price()
    
    if current_price:
        st.metric("Current BTC Price", f"${current_price:,.2f}")
    else:
        st.error("Failed to fetch current price")
    
    # Manual input for historical prices
    st.subheader("✏️ Enter Historical BTC Prices")
    morning_price = st.number_input(
        "BTC price at 5:29:59 AM",
        min_value=0.0, format="%.2f", step=0.01
    )
    evening_price = st.number_input(
        "BTC price at 5:29:59 PM",
        min_value=0.0, format="%.2f", step=0.01
    )
    
    # Calculate percentage changes
    if current_price and (morning_price > 0 or evening_price > 0):
        col1, col2 = st.columns(2)
        
        with col1:
            if morning_price > 0:
                morning_change = tracker.calculate_percentage_change(morning_price, current_price)
                st.metric(
                    "vs 5:29:59 AM",
                    f"${morning_price:,.2f}",
                    delta=f"{morning_change:+.2f}%" if morning_change is not None else "N/A"
                )
        
        with col2:
            if evening_price > 0:
                evening_change = tracker.calculate_percentage_change(evening_price, current_price)
                st.metric(
                    "vs 5:29:59 PM",
                    f"${evening_price:,.2f}",
                    delta=f"{evening_change:+.2f}%" if evening_change is not None else "N/A"
                )
    
    # Debug
    st.subheader("🐛 Debug Information")
    if st.button("Show Debug Info"):
        st.write("**API Configuration:**")
        st.write(f"Base URL: {tracker.base_url}")
        st.write(f"Symbol: {tracker.symbol}")
        st.write(f"API Key present: {'Yes' if tracker.api_key else 'No'}")
        st.write(f"API Secret present: {'Yes' if tracker.api_secret else 'No'}")
        test_timestamp = str(int(time.time()))
        test_signature = tracker.generate_signature("GET", "/v2/profile", test_timestamp)
        st.write(f"Sample signature: {test_signature}")

if __name__ == "__main__":
    main()
