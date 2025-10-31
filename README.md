# ⚽ Premier League Analytics Platform

Professional statistical analysis platform for Premier League data, featuring interactive CDF charts and comprehensive historical analysis.

![Premier League Analytics](https://img.shields.io/badge/Premier%20League-Analytics-003d71?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?style=for-the-badge&logo=flask)
![Chart.js](https://img.shields.io/badge/Chart.js-4.4-ff6384?style=for-the-badge&logo=chartdotjs)

## 🎯 Features

### 📊 Team Analytics
- **Interactive CDF Charts** for 20 Premier League teams
- **Three Chart Types**:
  - Goals Scored Distribution
  - Goals Conceded Distribution
  - Corners Distribution
- **Flexible Time Periods**:
  - Current Season
  - Last Season
  - Last 3 Seasons
  - Last 10 Seasons
- **Match Period Filters**: Full Match, 1st Half, 2nd Half

### 📈 Historical Data
- **12,000+ matches** from 1993 to 2025
- **32 seasons** of Premier League history
- **51 unique teams** across all seasons
- Data sourced from [football-data.co.uk](https://www.football-data.co.uk)

### 📋 Team Summary
- Comprehensive statistics for all teams
- Average goals scored/conceded per game
- Corner statistics (for/against)
- Goal difference rankings

## 🚀 Live Demo

[View Live Demo](https://your-app.onrender.com) *(Deploy first to get your URL)*

## 💻 Local Development

### Prerequisites
- Python 3.9 or higher
- Git (optional, for deployment)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/premier-league-analytics.git
   cd premier-league-analytics
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize database and import data**:
   ```bash
   python import_all_data.py
   ```
   *This will download 12,000+ matches from football-data.co.uk (takes 2-3 minutes)*

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Open in browser**:
   ```
   http://localhost:5000
   ```

## 🌐 Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for detailed deployment instructions to:
- ✅ Render.com (Recommended - Free)
- ✅ PythonAnywhere (Free with persistence)
- ✅ Railway (Free credits)

### Quick Deploy to Render

1. Push to GitHub
2. Go to [render.com](https://render.com)
3. Create New Web Service
4. Connect repository
5. Deploy!

Full instructions in [DEPLOYMENT.md](DEPLOYMENT.md)

## 🏗️ Tech Stack

### Backend
- **Flask** 3.0 - Web framework
- **SQLite** - Database
- **Python** 3.9+ - Server language

### Frontend
- **HTML5** - Structure
- **CSS3** - Moody's-inspired professional design
- **JavaScript** (ES6+) - Interactivity
- **Chart.js** 4.4 - Data visualization

### Data Source
- [football-data.co.uk](https://www.football-data.co.uk) - Historical match data

## 📊 Data Coverage

- **Time Period**: 1993/94 to 2025/26
- **Matches**: 12,034
- **Seasons**: 32
- **Teams**: 51 unique teams
- **Data Points**: Goals, Corners, Cards, Match results

## 🎨 Design

Professional corporate design inspired by Moody's Analytics:
- Clean, minimal interface
- Corporate blue color scheme (#003d71)
- Data-focused presentation
- Fully responsive (desktop, tablet, mobile)
- Accessible design (WCAG compliant)

## 📱 Browser Support

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers

## 🔧 Project Structure

```
premier-league-analytics/
├── app.py                  # Flask application
├── import_all_data.py      # Data import script
├── schema.sql              # Database schema
├── requirements.txt        # Python dependencies
├── build.sh               # Deployment build script
├── static/
│   ├── style.css          # Professional styles
│   └── app.js             # Frontend logic
├── templates/
│   └── index.html         # Main HTML template
└── README.md              # This file
```

## 📈 Features in Detail

### Cumulative Distribution Functions (CDF)
CDF charts show the probability that a value is less than or equal to a given number.

**Example**: If the CDF shows 70% at x=2 for goals scored:
→ There's a 70% probability the team scores 2 or fewer goals

This is invaluable for:
- Statistical betting analysis
- Performance prediction
- Historical pattern recognition

### Season Filtering
Analyze team performance across different time periods:
- **Current Season**: Latest form and statistics
- **Last Season**: Previous year's performance
- **Last 3 Seasons**: Recent trends
- **Last 10 Seasons**: Long-term historical patterns

## 🤝 Contributing

This is a personal analytics project. Feel free to fork and customize for your own use.

## 📄 License

This project is for educational and personal use. Data sourced from football-data.co.uk.

## ⚠️ Disclaimer

This tool provides statistical analysis for informational purposes only. Past performance does not guarantee future results. Please gamble responsibly.

## 🙏 Acknowledgments

- Data provided by [football-data.co.uk](https://www.football-data.co.uk)
- Design inspired by Moody's Analytics
- Built with Flask, Chart.js, and modern web technologies

## 📞 Support

For issues or questions, please open an issue on GitHub.

---

**Built with ⚽ and 📊 | Premier League Analytics Platform**
