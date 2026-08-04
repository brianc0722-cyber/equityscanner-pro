# EquityScanner Pro — GitHub + Render Deployment Guide

This is the **recommended deployment path** for this project.

**Why Render instead of Vercel?**
- Render supports full Python web services (including Streamlit)
- Much better for long-running apps like FastAPI + Streamlit
- Easy to run both the API and Dashboard
- Good free tier for demos and small projects

---

## Pre-Upload Checklist (Run These First)

```bash
cd /home/user/stock_scanner

# 1. Commit latest changes
git status
git add -A
git commit -m "Prepare for GitHub + Render deployment" || echo "Nothing new to commit"

# 2. Verify key files
ls README.md run_all.py dashboard/app.py api/main.py cli.py docker-compose.yml Dockerfile

# 3. Check current branch
git branch --show-current
```

---

## Part 1: Upload to GitHub (Step-by-Step)

### Step 1: Create Repository on GitHub

1. Go to: [https://github.com/new](https://github.com/new)
2. Fill in:
   - **Repository name**: `equityscanner-pro`
   - **Description**: `Real-time stock scanner with pre-market predictive analytics (FastAPI + Streamlit)`
   - Visibility: **Public**
   - **Uncheck** "Add a README", ".gitignore", and license
3. Click **Create repository**

### Step 2: Push Your Code

Replace `YOUR_USERNAME` with your actual GitHub username:

```bash
cd /home/user/stock_scanner

git remote add origin https://github.com/YOUR_USERNAME/equityscanner-pro.git

git branch -M main

git push -u origin main
```

**Authentication tip**: If it asks for a password, use a **Personal Access Token** (repo scope) instead of your GitHub password.

### Step 3: Verify & Polish

1. Refresh your GitHub repo page
2. Make sure all files are visible
3. Add topics (recommended):
   - `python`
   - `streamlit`
   - `fastapi`
   - `finance`
   - `machine-learning`
   - `quant`
   - `backtesting`

---

## Part 2: Deploy to Render (Recommended)

Render is excellent for this type of application.

### Why Render Works Well Here
- Native support for Python web services
- Streamlit runs great on Render
- Easy to deploy both FastAPI and Streamlit
- Good free tier (sleeps after inactivity on free plan)

---

### Method A: Deploy Using Git (Easiest - Recommended)

This is the simplest way.

#### Step 1: Go to Render

1. Go to [https://render.com](https://render.com)
2. Sign in with your **GitHub** account

#### Step 2: Create the FastAPI Backend Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository (`equityscanner-pro`)
3. Fill in the settings:

   | Field                    | Value                                      |
   |--------------------------|--------------------------------------------|
   | **Name**                 | `equityscanner-api`                        |
   | **Environment**          | `Python 3`                                 |
   | **Build Command**        | `pip install -r requirements.txt`          |
   | **Start Command**        | `uvicorn api.main:app --host 0.0.0.0 --port $PORT` |
   | **Plan**                 | `Free`                                     |

4. Click **"Advanced"** and add these **Environment Variables** (optional for now):
   - `PYTHONPATH` = `.`

5. Click **"Create Web Service"**

Wait for it to deploy. You will get a URL like:
`https://equityscanner-api.onrender.com`

Test it:
- `https://your-api.onrender.com/health`

#### Step 3: Create the Streamlit Dashboard Service

1. Click **"New +"** → **"Web Service"** again
2. Select the **same** GitHub repository
3. Fill in:

   | Field                    | Value                                           |
   |--------------------------|-------------------------------------------------|
   | **Name**                 | `equityscanner-dashboard`                       |
   | **Environment**          | `Python 3`                                      |
   | **Build Command**        | `pip install -r requirements.txt`               |
   | **Start Command**        | `streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true` |
   | **Plan**                 | `Free`                                          |

4. Add this **Environment Variable**:
   - `PYTHONPATH` = `.`

5. Click **"Create Web Service"**

You will get a second URL like:
`https://equityscanner-dashboard.onrender.com`

---

### Method B: Deploy Using Docker (More Advanced but Cleaner)

If you prefer using your existing `Dockerfile`:

1. When creating a Web Service on Render:
   - Choose **"Docker"** as the environment instead of "Python 3"
   - Render will automatically use your `Dockerfile`
   - Set the **Start Command** to empty (Dockerfile handles it)

This method is cleaner if you want to run everything in one container later.

---

### Step 4: Add Environment Variables (Important)

After creating the services:

1. Go to each service → **Environment** tab
2. Add any real API keys you want to use:
   - `ALPACA_API_KEY`
   - `ALPACA_API_SECRET`
   - `POLYGON_API_KEY`
   - etc.

> On the free tier, services sleep after 15 minutes of inactivity.

---

### Step 5: Update Your GitHub README (Recommended)

Add your Render URLs to the README so people can try the live version:

```markdown
## Live Demo

- **API**: https://equityscanner-api.onrender.com
- **Dashboard**: https://equityscanner-dashboard.onrender.com
```

---

## Useful Render Tips

| Action                        | How to do it                              |
|-------------------------------|-------------------------------------------|
| Restart a service             | Dashboard → Service → "Manual Deploy" → "Deploy latest commit" |
| View logs                     | Click on the service → Logs tab           |
| Add custom domain             | Available on paid plans                   |
| Prevent sleeping              | Upgrade to a paid plan or use a cron job  |
| Deploy automatically on push  | Already enabled when connected to GitHub  |

---

## Summary

| Step                    | Action                              | Platform     |
|-------------------------|-------------------------------------|--------------|
| 1                       | Push code to GitHub                 | GitHub       |
| 2                       | Deploy FastAPI backend              | Render       |
| 3                       | Deploy Streamlit dashboard          | Render       |
| 4                       | Add environment variables           | Render       |
| 5 (Optional)            | Add live links to README            | GitHub       |

---

## Final Notes

- Render free tier is generous for demos and side projects.
- Both services will have separate URLs.
- You can later combine them into one service using a reverse proxy if desired.

Would you like me to also create a simple `render.yaml` file (for Blueprint / Infrastructure as Code) so you can deploy everything with one click in the future?

Just let me know!