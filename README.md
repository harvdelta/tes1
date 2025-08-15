# Bitcoin Price Tracker 📈

A real-time Bitcoin price tracking application that compares current BTC prices with historical prices at 5:29:59 AM and 5:29:59 PM using the Delta Exchange API.

## Features

- 🔄 Real-time BTC price fetching
- 📊 Historical price comparison (5:29:59 AM & PM)
- 📈 Percentage change calculations
- 🎯 Clean, responsive Streamlit interface
- ⏰ Auto-refresh functionality
- 💾 Data from Delta Exchange API

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/btc-price-tracker.git
cd btc-price-tracker
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Local Development
Run the Streamlit app locally:
```bash
streamlit run app.py
```

### Deployment Options

#### Streamlit Community Cloud
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Deploy!

#### Other Platforms
- **Heroku**: Add `setup.sh` and `Procfile` for Heroku deployment
- **Railway**: Direct deployment from GitHub
- **Render**: Connect GitHub repo and deploy

## API Information

This application uses the Delta Exchange public API:
- **Base URL**: `https://api.delta.exchange`
- **Current Price Endpoint**: `/v2/tickers/{symbol}`
- **Historical Data Endpoint**: `/v2/history/candles`

No API key required for basic functionality.

## File Structure

```
btc-price-tracker/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── .gitignore         # Git ignore file
```

## Configuration

### Customization Options

You can modify the following in `app.py`:
- Trading pair symbol (default: `BTCUSDT`)
- Target times (default: `05:29:59` AM/PM)
- Auto-refresh interval (default: 30 seconds)
- Price precision and formatting

### Environment Variables

No environment variables needed for basic functionality.

## Features Breakdown

### Real-time Price Tracking
- Fetches current BTC price from Delta Exchange
- Updates with manual refresh or auto-refresh

### Historical Comparison
- Compares current price with 5:29:59 AM price
- Compares current price with 5:29:59 PM price
- Shows percentage changes and absolute differences

### User Interface
- Clean, modern Streamlit interface
- Responsive design with metrics cards
- Color-coded changes (green/red for positive/negative)
- Detailed analysis table

## Error Handling

The application includes comprehensive error handling for:
- API connection issues
- Missing historical data
- Invalid responses
- Network timeouts

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## Disclaimer

⚠️ **Important**: This application is for informational purposes only and should not be considered financial advice. Always conduct your own research before making any investment decisions.

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/yourusername/btc-price-tracker/issues) page
2. Create a new issue if your problem isn't already reported
3. Provide detailed information about the error and your environment

---

Made with ❤️ using Streamlit and Delta Exchange API
