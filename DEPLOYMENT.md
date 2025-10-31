# 🚀 Deployment Guide - Premier League Analytics

## Option 1: Deploy to Render.com (EASIEST - FREE)

Render.com offers a free tier and is the simplest way to deploy Flask apps.

### Prerequisites
1. A GitHub account
2. Git installed on your computer

---

### Step 1: Push to GitHub

1. **Install Git** (if not already installed):
   - Download from https://git-scm.com/downloads
   - Install with default settings

2. **Open PowerShell** in your project folder:
   ```powershell
   cd C:\Users\ccurr\Desktop\PremierLeagueBetting
   ```

3. **Initialize Git and push to GitHub**:
   ```powershell
   # Initialize git repository
   git init
   
   # Add all files
   git add .
   
   # Commit files
   git commit -m "Initial commit - Premier League Analytics"
   ```

4. **Create a new repository on GitHub**:
   - Go to https://github.com/new
   - Repository name: `premier-league-analytics`
   - Make it **Public**
   - Don't initialize with README (we already have files)
   - Click "Create repository"

5. **Push your code**:
   ```powershell
   # Replace YOUR_USERNAME with your GitHub username
   git remote add origin https://github.com/YOUR_USERNAME/premier-league-analytics.git
   git branch -M main
   git push -u origin main
   ```

---

### Step 2: Deploy to Render

1. **Go to Render.com**:
   - Visit https://render.com
   - Click "Get Started for Free"
   - Sign up with GitHub

2. **Create a New Web Service**:
   - Click "New +" button
   - Select "Web Service"
   - Connect your GitHub repository: `premier-league-analytics`

3. **Configure the Web Service**:
   ```
   Name: premier-league-analytics
   Region: Choose closest to you
   Branch: main
   Runtime: Python 3
   Build Command: chmod +x build.sh && ./build.sh
   Start Command: gunicorn app:app
   Instance Type: Free
   ```

4. **Add Environment Variables** (if needed):
   - Click "Advanced"
   - No environment variables needed for this app

5. **Create Web Service**:
   - Click "Create Web Service"
   - Wait 5-10 minutes for build and deployment
   - **NOTE**: Initial build will take time as it downloads 12,000+ matches

6. **Access Your App**:
   - Once deployed, you'll get a URL like: `https://premier-league-analytics.onrender.com`
   - Your app is now live! 🎉

---

### Important Notes for Render:

⚠️ **Free Tier Limitations**:
- App will "sleep" after 15 minutes of inactivity
- First request after sleep takes 30-60 seconds to wake up
- Database is stored in memory (resets on every deploy)

💡 **Database Persistence**:
The free tier doesn't persist the database. Each time the service restarts, it rebuilds from football-data.co.uk.

🔄 **Manual Redeploy**:
To update your app:
```powershell
git add .
git commit -m "Update description"
git push
```
Render will automatically redeploy.

---

## Option 2: Deploy to PythonAnywhere (FREE with persistence)

PythonAnywhere offers persistent storage on free tier.

### Step 1: Create Account
1. Go to https://www.pythonanywhere.com
2. Create a free "Beginner" account

### Step 2: Upload Files
1. Click "Files" tab
2. Create folder: `/home/yourusername/premier-league`
3. Upload all project files via web interface OR use Git

### Step 3: Setup Database
1. Click "Consoles" → "Bash"
2. Run:
   ```bash
   cd ~/premier-league
   python3 -m pip install --user -r requirements.txt
   python3 import_all_data.py
   ```

### Step 4: Configure Web App
1. Click "Web" tab
2. "Add a new web app"
3. Choose "Manual configuration"
4. Python 3.10
5. Set source code: `/home/yourusername/premier-league`
6. Edit WSGI file, replace content with:
   ```python
   import sys
   path = '/home/yourusername/premier-league'
   if path not in sys.path:
       sys.path.append(path)
   
   from app import app as application
   ```
7. Set static files:
   - URL: `/static/`
   - Directory: `/home/yourusername/premier-league/static`

8. Reload web app

Your app will be at: `https://yourusername.pythonanywhere.com`

---

## Option 3: Deploy to Railway (FREE credits)

Railway gives $5 free credits per month.

### Step 1: Push to GitHub
Follow Step 1 from Render instructions above.

### Step 2: Deploy to Railway
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Railway auto-detects Python
7. Add build command in settings:
   ```
   chmod +x build.sh && ./build.sh
   ```
8. Add start command:
   ```
   gunicorn app:app
   ```
9. Deploy will start automatically

Your app will be at: `https://your-app.up.railway.app`

---

## Testing Your Deployed App

After deployment, test these features:

✅ Homepage loads
✅ Click any team (e.g., Arsenal)
✅ Charts display correctly
✅ Season filter works
✅ Period filters (Full/1H/2H) work
✅ Data Summary tab loads
✅ Team Summary tab loads

---

## Troubleshooting

### Build Fails
- Check build logs for errors
- Ensure all files are committed to Git
- Verify requirements.txt is correct

### Database Empty
- Check build.sh executed successfully
- Verify import_all_data.py ran without errors
- Check logs for football-data.co.uk access issues

### App Won't Start
- Check start command is: `gunicorn app:app`
- Verify no port conflicts
- Check Python version is 3.9+

### Charts Not Loading
- Check browser console for JavaScript errors
- Verify static files are served correctly
- Check Chart.js CDN is accessible

---

## Cost Comparison

| Platform | Free Tier | Persistence | Auto-sleep | Custom Domain |
|----------|-----------|-------------|------------|---------------|
| **Render** | ✅ Yes | ❌ No | ✅ 15 min | ✅ Yes |
| **PythonAnywhere** | ✅ Yes | ✅ Yes | ❌ No | ❌ Paid |
| **Railway** | 💰 $5/mo credit | ✅ Yes | ❌ No | ✅ Yes |

---

## Recommended: Render.com

✅ **Why Render?**
- Easiest setup
- Automatic deployments from GitHub
- Free SSL certificates
- Good free tier
- Professional URLs

⚠️ **Note**: Database rebuilds on each restart (5-10 min)

---

## Need Help?

If you encounter issues:
1. Check deployment logs
2. Verify all files are pushed to GitHub
3. Ensure build.sh has execute permissions
4. Check football-data.co.uk is accessible

---

## Your App is Live! 🎉

Share your URL:
- Render: `https://premier-league-analytics.onrender.com`
- PythonAnywhere: `https://yourusername.pythonanywhere.com`
- Railway: `https://your-app.up.railway.app`

Enjoy your professional Premier League Analytics platform! ⚽📊

