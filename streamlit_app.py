import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import json

class BTCPriceTracker:
    def __init__(self):
        self.base_url = "https://api.delta.exchange"
        self.symbol = "BTCUSDT"  # BTC/USDT trading pair
        
    def get_current_price(self):
        """Fetch current BTC price from Delta Exchange"""
        try:
            url = f"{self.base_url}/v2/tickers/{self.symbol}"
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                return float(data['result']['close'])
            else:
                st.error("Failed to fetch current price")
                return None
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching current price: {e}")
            return None
    
    def get_historical_price(self, target_time):
        """
        Fetch historical BTC price closest to the target time
        target_time should be in format "05:29:59" (24-hour format)
        """
        try:
            # Convert target time to timestamp
            today = datetime.now().date()
            target_datetime = datetime.combine(today, datetime.strptime(target_time, "%H:%M:%S").time())
            
            # If target time is in future today, use yesterday's data
            if target_datetime > datetime.now():
                target_datetime = target_datetime - timedelta(days=1)
            
            # Convert to Unix timestamp (milliseconds)
            timestamp = int(target_datetime.timestamp() * 1000)
            
            # Delta Exchange historical data endpoint
            url = f"{self.base_url}/v2/history/candles"
            params = {
                'symbol': self.symbol,
                'resolution': '1',  # 1 minute candles
                'start': timestamp - 300000,  # 5 minutes before
                'end': timestamp + 300000     # 5 minutes after
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success') and data.get('result'):
                candles = data['result']
                if candles:
                    # Find the candle closest to target time
                    closest_candle = min(candles, key=lambda x: abs(x['time'] - timestamp))
                    return float(closest_candle['close'])
            
            st.warning(f"No historical data found for {target_time}")
            return None
            
        except Exception as e:
            st.error(f"Error fetching historical price: {e}")
            return None
    
    def calculate_percentage_change(self, old_price, new_price):
        """Calculate percentage change between two prices"""
        if old_price is None or new_price is None:
            return None
        
        return ((new_price - old_price) / old_price) * 100

def main():
    st.set_page_config(
        page_title="BTC Price Tracker",
        page_icon="₿",
        layout="wide"
    )
    
    st.title("₿ Bitcoin Price Tracker")
    st.markdown("**Track BTC price changes from 5:29:59 AM to current time**")
    
    # Initialize tracker
    tracker = BTCPriceTracker()
    
    # Create columns for layout
    col1, col2, col3 = st.columns(3)
    
    # Add refresh button
    if st.button("🔄 Refresh Data", type="primary"):
        st.rerun()
    
    # Auto-refresh option
    auto_refresh = st.checkbox("Auto-refresh every 30 seconds")
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    with st.spinner("Fetching BTC prices..."):
        # Get current price
        current_price = tracker.get_current_price()
        
        # Get 5:29:59 AM price
        morning_price = tracker.get_historical_price("05:29:59")
        
        # Get 5:29:59 PM price (17:29:59 in 24-hour format)
        evening_price = tracker.get_historical_price("17:29:59")
    
    # Display current price
    with col1:
        st.metric(
            label="Current BTC Price",
            value=f"${current_price:,.2f}" if current_price else "N/A",
            delta=None
        )
        st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    # Display morning comparison
    with col2:
        if morning_price and current_price:
            morning_change = tracker.calculate_percentage_change(morning_price, current_price)
            st.metric(
                label="vs 5:29:59 AM",
                value=f"${morning_price:,.2f}",
                delta=f"{morning_change:+.2f}%" if morning_change else "N/A"
            )
        else:
            st.metric(
                label="vs 5:29:59 AM",
                value="N/A",
                delta="N/A"
            )
    
    # Display evening comparison
    with col3:
        if evening_price and current_price:
            evening_change = tracker.calculate_percentage_change(evening_price, current_price)
            st.metric(
                label="vs 5:29:59 PM",
                value=f"${evening_price:,.2f}",
                delta=f"{evening_change:+.2f}%" if evening_change else "N/A"
            )
        else:
            st.metric(
                label="vs 5:29:59 PM",
                value="N/A",
                delta="N/A"
            )
    
    # Detailed breakdown
    st.markdown("---")
    st.subheader("📊 Detailed Analysis")
    
    if all([current_price, morning_price, evening_price]):
        # Create comparison table
        data = {
            'Time': ['5:29:59 AM', '5:29:59 PM', 'Current'],
            'Price ($)': [f"{morning_price:,.2f}", f"{evening_price:,.2f}", f"{current_price:,.2f}"],
            'Change from Current (%)': [
                f"{tracker.calculate_percentage_change(current_price, morning_price):+.2f}%",
                f"{tracker.calculate_percentage_change(current_price, evening_price):+.2f}%",
                "0.00%"
            ]
        }
        
        df = pd.DataFrame(data)
        st.table(df)
        
        # Price difference calculations
        morning_diff = current_price - morning_price
        evening_diff = current_price - evening_price
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Morning to Now:** ${morning_diff:+,.2f} ({tracker.calculate_percentage_change(morning_price, current_price):+.2f}%)")
        
        with col2:
            st.info(f"**Evening to Now:** ${evening_diff:+,.2f} ({tracker.calculate_percentage_change(evening_price, current_price):+.2f}%)")
    
    else:
        st.warning("Some price data is unavailable. Please try refreshing or check your internet connection.")
    
    # Footer
    st.markdown("---")
    st.markdown("*Data provided by Delta Exchange API*")
    st.markdown("⚠️ **Disclaimer:** This is for informational purposes only and not financial advice.")

if __name__ == "__main__":
    main()
