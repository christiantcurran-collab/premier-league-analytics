@echo off
echo ========================================
echo  Premier League Betting Advisor
echo ========================================
echo.

REM Check if database exists
if not exist premier_league.db (
    echo Database not found. Creating sample data...
    python sample_data.py
    echo.
)

echo Starting application...
echo.
echo Access the app at: http://localhost:5000
echo Or from your phone: http://YOUR-PC-IP:5000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python app.py

pause

