import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import hmac
import hashlib
import json
import base64

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
        """Generate signature for Delta Exchange API"""
        message = f"{method}{timestamp}{path}{body}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def make_authenticated_request(self, method, path, params=None):
        """Make authenticated request to Delta Exchange API"""
        timestamp = str(int(time.time()))
        url = f"{self.base_url}{path}"
        query_string = ""
        
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
            st.write(f"Debug - Status Code: {response.status_code}")
            st.write(f"Debug - URL: {url}")
            st.write(f"Debug - Headers sent: {dict(headers)}")
            
            if response.status_code == 401:
                st.error("Authentication failed. Please check your API credentials.")
                st.write("Response:", response.text)
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                st.write(f"Response content: {e.response.text}")
            return None
    
    def get_current_price(self):
        """Fetch current BTC price (using public endpoint)"""
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
    
    def get_historical_price_simple(self, target_time):
        """Estimate historical price based on target time"""
        try:
            url = f"{self.base_url}/v2/tickers/{self.symbol}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success') and data.get('result'):
                ticker = data['result']
                current_price = float(ticker['close'])
                change_24h = float(ticker.get('change_24h', 0))
                
                if "05:29:59" in target_time:
                    estimated_price = current_price - (change_24h * 0.3)
                elif "17:29:59" in target_time:
                    estimated_price = current_price - (change_24h * 0.1)
                else:
                    estimated_price = current_price
                
                return estimated_price
            
            return None
            
        except Exception as e:
            st.error(f"Error estimating historical price: {e}")
            return None
    
    def test_api_connection(self):
        """Test API connection"""
        try:
            data = self.make_authenticated_request("GET", "/v2/profile")
            return data
        except Exception as e:
            st.error(f"API test failed: {e}")
            return None
    
    def calculate_percentage_change(self, old_price, new_price):
        """Calculate percentage change"""
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
    
    st.subheader("🔧 API Connection Test")
    if st.button("Test API Connection"):
        with st.spinner("Testing API connection..."):
            result = tracker.test_api_connection()
        if result:
            if result.get('success'):
                st.success("✅ API Connection Successful!")
                if 'result' in result:
                    st.json(result['result'])
            else:
                st.error("❌ API returned unsuccessful response")
                st.json(result)
        else:
            st.error("❌ API Connection Failed")
    
    st.subheader("📊 Current BTC Price")
    with st.spinner("Fetching current price..."):
        current_price = tracker.get_current_price()
    
    if current_price:
        st.metric("Current BTC Price", f"${current_price:,.2f}")
    else:
        st.error("Failed to fetch current price")
    
    st.subheader("📈 Price Comparisons (Estimated)")
    st.info("Note: Using price estimation while fixing historical data API")
    
    if current_price:
        col1, col2 = st.columns(2)
        
        with col1:
            time1 = st.text_input("Enter first time (HH:MM:SS)", "05:29:59")
            estimate1 = tracker.get_historical_price_simple(time1)
            if estimate1:
                change1 = tracker.calculate_percentage_change(estimate1, current_price)
                st.metric(
                    f"vs {time1} (Est.)",
                    f"${estimate1:,.2f}",
                    delta=f"{change1:+.2f}%" if change1 else "N/A"
                )
        
        with col2:
            time2 = st.text_input("Enter second time (HH:MM:SS)", "17:29:59")
            estimate2 = tracker.get_historical_price_simple(time2)
            if estimate2:
                change2 = tracker.calculate_percentage_change(estimate2, current_price)
                st.metric(
                    f"vs {time2} (Est.)",
                    f"${estimate2:,.2f}",
                    delta=f"{change2:+.2f}%" if change2 else "N/A"
                )
    
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
    
    st.markdown("---")
    st.markdown("*Troubleshooting API authentication issues...*")

if __name__ == "__main__":
    main()
