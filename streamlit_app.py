import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import hmac
import hashlib
import json
from urllib.parse import urlencode

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
    
    def generate_signature(self, method, endpoint, payload=""):
        """Generate HMAC signature for Delta Exchange API"""
        timestamp = str(int(time.time() * 1000))
        message = method + timestamp + endpoint + payload
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature, timestamp
    
    def make_authenticated_request(self, method, endpoint, params=None, data=None):
        """Make authenticated request to Delta Exchange API"""
        url = f"{self.base_url}{endpoint}"
        
        # Prepare payload
        payload = ""
        if method == "GET" and params:
            payload = urlencode(params)
            url += f"?{payload}"
        elif method == "POST" and data:
            payload = json.dumps(data)
        
        # Generate signature
        signature, timestamp = self.generate_signature(method, endpoint, payload)
        
        # Headers
        headers = {
            'api-key': self.api_key,
            'timestamp': timestamp,
            'signature': signature,
            'Content-Type': 'application/json'
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, data=payload, timeout=10)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            st.error(f"API Request failed: {e}")
            return None
    
    def get_current_price(self):
        """Fetch current BTC price using authenticated API"""
        try:
            # Use public endpoint for current price (no auth needed)
            url = f"{self.base_url}/v2/tickers/{self.symbol}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success') and data.get('result'):
                return float(data['result']['close'])
            else:
                st.error("Failed to fetch current price from public endpoint")
                return None
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching current price: {e}")
            return None
    
    def get_historical_candles(self, symbol, resolution="1", start_time=None, end_time=None):
        """Fetch historical candle data using authenticated API"""
        endpoint = "/v2/history/candles"
        
        params = {
            'symbol': symbol,
            'resolution': resolution
        }
        
        if start_time:
            params['start'] = start_time
        if end_time:
            params['end'] = end_time
            
        return self.make_authenticated_request("GET", endpoint, params)
    
    def get_historical_price(self, target_time):
        """Get historical BTC price at specific time"""
        try:
            # Parse target time
            today = datetime.now().date()
            target_datetime = datetime.combine(today, datetime.strptime(target_time, "%H:%M:%S").time())
            
            # If target time is in future today, use yesterday
            if target_datetime > datetime.now():
                target_datetime = target_datetime - timedelta(days=1)
            
            # Convert to Unix timestamp (milliseconds)
            timestamp = int(target_datetime.timestamp() * 1000)
            
            # Get candles around target time (±5 minutes)
            start_time = timestamp - 300000  # 5 minutes before
            end_time = timestamp + 300000    # 5 minutes after
            
            data = self.get_historical_candles(
                self.symbol, 
                resolution="1",  # 1 minute candles
                start_time=start_time,
                end_time=end_time
            )
            
            if data and data.get('success') and data.get('result'):
                candles = data['result']
                if candles:
                    # Find closest candle to target time
                    closest_candle = min(candles, key=lambda x: abs(x['time'] - timestamp))
                    return float(closest_candle['close'])
            
            # Fallback: try to get daily candle
            daily_data = self.get_historical_candles(
                self.symbol,
                resolution="1D",
                start_time=timestamp - 86400000,  # 1 day before
                end_time=timestamp + 86400000     # 1 day after
            )
            
            if daily_data and daily_data.get('success') and daily_data.get('result'):
                candles = daily_data['result']
                if candles:
                    return float(candles[0]['close'])
            
            st.warning(f"No historical data found for {target_time}")
            return None
            
        except Exception as e:
            st.error(f"Error fetching historical price for {target_time}: {e}")
            return None
    
    def get_account_info(self):
        """Get account information to verify API connection"""
        endpoint = "/v2/profile"
        return self.make_authenticated_request("GET", endpoint)
    
    def calculate_percentage_change(self, old_price, new_price):
        """Calculate percentage change between two prices"""
        if old_price is None or new_price is None:
            return None
        return ((new_price - old_price) / old_price) * 100

def main():
    st.set_page_config(
        page_title="BTC Price Tracker - Delta Exchange",
        page_icon="₿",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("₿ Bitcoin Price Tracker")
    st.markdown("**Authenticated Delta Exchange API Integration**")
    
    # Initialize tracker
    try:
        tracker = BTCPriceTracker()
    except:
        st.error("Failed to initialize tracker. Please check your API credentials.")
        return
    
    # Sidebar with API info
    with st.sidebar:
        st.header("🔧 API Status")
        
        # Test API connection
        with st.spinner("Testing API connection..."):
            account_info = tracker.get_account_info()
            
        if account_info and account_info.get('success'):
            st.success("✅ API Connection Active")
            if 'result' in account_info:
                user_data = account_info['result']
                st.info(f"**User ID:** {user_data.get('id', 'N/A')}")
                st.info(f"**Email:** {user_data.get('email', 'N/A')}")
        else:
            st.error("❌ API Connection Failed")
            st.warning("Check your API credentials")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col2:
        # Controls
        st.subheader("Controls")
        
        if st.button("🔄 Refresh All Data", type="primary"):
            st.rerun()
        
        auto_refresh = st.checkbox("Auto-refresh (30s)")
        if auto_refresh:
            time.sleep(30)
            st.rerun()
        
        # Custom time inputs
        st.subheader("Custom Times")
        morning_time = st.time_input("Morning Time", value=datetime.strptime("05:29:59", "%H:%M:%S").time())
        evening_time = st.time_input("Evening Time", value=datetime.strptime("17:29:59", "%H:%M:%S").time())
    
    with col1:
        # Price data
        st.subheader("📊 Price Analysis")
        
        with st.spinner("Fetching BTC prices..."):
            # Get current price
            current_price = tracker.get_current_price()
            
            # Get historical prices
            morning_time_str = morning_time.strftime("%H:%M:%S")
            evening_time_str = evening_time.strftime("%H:%M:%S")
            
            morning_price = tracker.get_historical_price(morning_time_str)
            evening_price = tracker.get_historical_price(evening_time_str)
        
        # Display metrics
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.metric(
                label="Current Price",
                value=f"${current_price:,.2f}" if current_price else "N/A",
                delta=None
            )
            st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        
        with metric_col2:
            if morning_price and current_price:
                morning_change = tracker.calculate_percentage_change(morning_price, current_price)
                st.metric(
                    label=f"vs {morning_time_str}",
                    value=f"${morning_price:,.2f}",
                    delta=f"{morning_change:+.2f}%" if morning_change else "N/A"
                )
            else:
                st.metric(label=f"vs {morning_time_str}", value="N/A", delta="N/A")
        
        with metric_col3:
            if evening_price and current_price:
                evening_change = tracker.calculate_percentage_change(evening_price, current_price)
                st.metric(
                    label=f"vs {evening_time_str}",
                    value=f"${evening_price:,.2f}",
                    delta=f"{evening_change:+.2f}%" if evening_change else "N/A"
                )
            else:
                st.metric(label=f"vs {evening_time_str}", value="N/A", delta="N/A")
        
        # Detailed analysis
        if all([current_price, morning_price, evening_price]):
            st.subheader("📈 Detailed Analysis")
            
            # Price comparison table
            analysis_data = {
                'Time Period': [morning_time_str, evening_time_str, 'Current'],
                'Price ($)': [
                    f"{morning_price:,.2f}",
                    f"{evening_price:,.2f}", 
                    f"{current_price:,.2f}"
                ],
                'Change from Current (%)': [
                    f"{tracker.calculate_percentage_change(current_price, morning_price):+.2f}%",
                    f"{tracker.calculate_percentage_change(current_price, evening_price):+.2f}%",
                    "0.00%"
                ],
                'Absolute Difference ($)': [
                    f"{current_price - morning_price:+,.2f}",
                    f"{current_price - evening_price:+,.2f}",
                    "0.00"
                ]
            }
            
            df = pd.DataFrame(analysis_data)
            st.dataframe(df, use_container_width=True)
            
            # Summary insights
            morning_change = tracker.calculate_percentage_change(morning_price, current_price)
            evening_change = tracker.calculate_percentage_change(evening_price, current_price)
            
            st.subheader("💡 Summary")
            
            insight_col1, insight_col2 = st.columns(2)
            
            with insight_col1:
                trend_morning = "📈 Higher" if morning_change > 0 else "📉 Lower" if morning_change < 0 else "➡️ Same"
                st.info(f"**Since {morning_time_str}:** {trend_morning} by {abs(morning_change):.2f}%")
            
            with insight_col2:
                trend_evening = "📈 Higher" if evening_change > 0 else "📉 Lower" if evening_change < 0 else "➡️ Same"
                st.info(f"**Since {evening_time_str}:** {trend_evening} by {abs(evening_change):.2f}%")
        
        else:
            st.warning("⚠️ Some price data is unavailable. This might be due to:")
            st.markdown("""
            - Weekend/holiday when markets are less active
            - API rate limits
            - Network connectivity issues
            - Historical data not available for the requested time
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("*Powered by Delta Exchange Authenticated API*")
    st.markdown("⚠️ **Disclaimer:** For informational purposes only. Not financial advice.")

if __name__ == "__main__":
    main()
