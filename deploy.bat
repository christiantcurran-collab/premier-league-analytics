@echo off
echo ========================================
echo  Premier League Analytics - Deployment
echo ========================================
echo.

echo This script will help you deploy to GitHub
echo.

pause

echo.
echo Step 1: Initializing Git repository...
git init
if errorlevel 1 (
    echo ERROR: Git not found. Please install Git from https://git-scm.com
    pause
    exit /b 1
)

echo.
echo Step 2: Adding files to Git...
git add .

echo.
echo Step 3: Creating initial commit...
git commit -m "Initial commit - Premier League Analytics"

echo.
echo ========================================
echo  Next Steps:
echo ========================================
echo.
echo 1. Go to https://github.com/new
echo 2. Create a new repository named: premier-league-analytics
echo 3. Make it PUBLIC
echo 4. Don't initialize with README
echo 5. Copy the repository URL
echo.
echo Then run this command (replace YOUR_USERNAME):
echo.
echo git remote add origin https://github.com/YOUR_USERNAME/premier-league-analytics.git
echo git branch -M main
echo git push -u origin main
echo.
echo After pushing to GitHub:
echo - Go to https://render.com
echo - Sign up with GitHub
echo - Create New Web Service
echo - Connect your repository
echo - Deploy!
echo.
echo Full instructions in DEPLOYMENT.md
echo.

pause

