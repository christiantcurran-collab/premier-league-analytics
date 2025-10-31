# 🚀 Setup Instructions - Premier League Betting Advisor

## ⚡ Quick Setup (3 Steps)

### Step 1: Install Python Packages
Open **Command Prompt** in this folder and run:
```cmd
pip install -r requirements.txt
```
⏱️ Takes about 30 seconds

### Step 2: Generate Sample Data
```cmd
python sample_data.py
```
⏱️ Takes about 10 seconds - Creates 10 years of match data

### Step 3: Start the App
```cmd
python app.py
```
✅ App running! Open browser to `http://localhost:5000`

---

## 📱 Access from Your Phone

### Find Your PC's IP Address:
1. Open Command Prompt
2. Type: `ipconfig`
3. Look for **IPv4 Address** (e.g., `192.168.1.100`)

### On Your Phone:
1. Connect to **same WiFi** as your PC
2. Open browser
3. Go to: `http://YOUR-PC-IP:5000`
   - Replace `YOUR-PC-IP` with the address from step above
   - Example: `http://192.168.1.100:5000`

### Windows Firewall Fix (if phone can't connect):
1. Search "Windows Security" in Start menu
2. Go to **Firewall & network protection**
3. Click **Allow an app through firewall**
4. Click **Change settings**
5. Find **Python** in the list
6. Check both **Private** and **Public** boxes
7. Click **OK**

---

## 🎯 Using the Application

### Tab 1: This Weekend
- View upcoming Premier League fixtures
- Click any match card
- See instant predictions with probabilities and odds

### Tab 2: Custom Match
- Select home team from dropdown
- Select away team from dropdown
- Click "Get Predictions"
- View detailed analysis

### Tab 3: Team Stats
- Choose any Premier League team
- Select Home/Away/Both analysis
- Click "View Statistics"
- See historical averages and distributions

---

## 📊 Understanding Predictions

### Probability Percentage
- Shows likelihood based on historical data
- Example: **65.5%** = This happened in 655 out of 1000 similar matches

### Decimal Odds
- Calculated as `1 ÷ probability`
- **Lower odds** = More likely to happen
- **Higher odds** = Less likely to happen

### Example Comparison:
```
Your App Prediction:
  2+ goals: 65.5% probability = 1.53 odds

Betting App Offers:
  2+ goals: 1.80 odds

Analysis:
  1.80 > 1.53 = VALUE BET
  (Betting app thinks it's less likely than history suggests)
```

---

## 🔧 Troubleshooting

### ❌ "Python not recognized"
**Problem:** Python not installed or not in PATH

**Solution:**
1. Download Python from python.org
2. During installation, check "Add Python to PATH"
3. Restart Command Prompt

### ❌ "pip not recognized"
**Problem:** pip not installed

**Solution:**
```cmd
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### ❌ "Address already in use"
**Problem:** Port 5000 is being used

**Solution:**
Edit `app.py`, find the last line:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```
Change `5000` to `5001` or `8080`

### ❌ "No module named flask"
**Problem:** Flask not installed

**Solution:**
```cmd
pip install Flask
```

### ❌ Can't access from phone
**Problem:** Firewall or wrong IP

**Solution:**
1. Verify both devices on same WiFi network
2. Double-check IP address (use `ipconfig`)
3. Allow Python through Windows Firewall (see above)
4. Try accessing from PC browser first to confirm it works

### ❌ Database errors
**Problem:** Corrupted database

**Solution:**
```cmd
del premier_league.db
python sample_data.py
```

---

## 📁 Project Files Explained

```
PremierLeagueBetting/
│
├── app.py                   ← Main Flask application & API
├── schema.sql               ← Database table definitions
├── sample_data.py           ← Generates 10 years of match data
├── requirements.txt         ← Python packages needed
├── run.bat                  ← Quick start script (double-click)
│
├── templates/
│   └── index.html          ← Main webpage HTML
│
├── static/
│   ├── style.css           ← Mobile-responsive styling
│   └── app.js              ← Frontend JavaScript
│
├── README.md               ← Full documentation
├── QUICK_START.txt         ← Quick reference guide
└── SETUP_INSTRUCTIONS.md   ← This file
```

---

## 🎨 Customization Options

### Add Your Own Teams
Edit `sample_data.py`, modify the `TEAMS` list

### Change Colors
Edit `static/style.css`, look for `:root` section with color variables

### Adjust Prediction Algorithm
Edit `app.py`, modify the `BettingAnalyzer` class methods

### Add More Fixtures
Run SQL on the database:
```sql
INSERT INTO fixtures (match_date, match_time, home_team, away_team, venue, season)
VALUES ('2025-11-15', '15:00', 'Arsenal', 'Liverpool', 'Emirates', '2024/2025');
```

---

## 📈 What Data is Analyzed?

For each team, the app analyzes:
- ✅ Last 10 years of Premier League matches
- ✅ Home vs Away performance
- ✅ Goals scored per half
- ✅ Corners won per half
- ✅ Historical patterns and distributions

Sample Data Includes:
- ~3,800 matches per team over 10 years
- Realistic goal distributions
- Realistic corner statistics
- Home advantage factored in

---

## 🔐 Privacy & Security

- ✅ Runs **locally** on your PC
- ✅ No data sent to external servers
- ✅ No account required
- ✅ No tracking or analytics
- ✅ All calculations done on your machine

---

## ⚠️ Important Reminders

### Responsible Gambling
- This tool is for **research and information only**
- No prediction system is 100% accurate
- Never bet more than you can afford to lose
- Seek help if gambling becomes a problem
- Check your local laws regarding sports betting

### Data Limitations
- Sample data is simulated for testing
- Real matches affected by many factors:
  - Player injuries
  - Weather conditions
  - Team form changes
  - Managerial changes
  - Motivation levels

### Use Wisely
- Combine with other research
- Check team news before matches
- Compare odds across multiple bookmakers
- Keep records of predictions vs results
- Set betting budgets and stick to them

---

## 🆘 Need Help?

1. Check **QUICK_START.txt** for basic commands
2. Read **README.md** for detailed information
3. Check troubleshooting section above
4. Verify Python and packages are installed correctly

---

## 🎉 You're Ready!

Open Command Prompt in this folder and run:
```cmd
python app.py
```

Then visit: **http://localhost:5000**

**Enjoy data-driven betting insights! ⚽📊**

