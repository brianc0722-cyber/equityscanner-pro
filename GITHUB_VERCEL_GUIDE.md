# EquityScanner Pro - GitHub + Vercel Deployment Guide

## STEP 1: Prepare Your Project (Do This First)

Open your terminal and run:

```bash
cd /home/user/stock_scanner

# Make sure all changes are committed
git status
git add -A
git commit -m "Prepare for GitHub and deployment" || echo "No new changes to commit"

# Verify important files exist
ls -1 README.md run_all.py dashboard/app.py api/main.py cli.py docker-compose.yml Dockerfile
```

---

## STEP 2: Upload to GitHub (Detailed)

### 2.1 Create a New Repository on GitHub

1. Go to this link: **https://github.com/new**
2. Fill out the form:
   - **Repository name**: `equityscanner-pro`
   - **Description**: `Real-time stock scanner with pre-market predictive analytics engine`
   - Visibility: **Public**
   - **Uncheck** all three boxes:
     - Add a README file
     - Add .gitignore
     - Choose a license
3. Click **Create repository**

### 2.2 Connect and Push Your Code

Copy and run these commands one by one (replace `YOUR_USERNAME` with your actual GitHub username):

```bash
cd /home/user/stock_scanner

# Add your GitHub repository as the remote
git remote add origin https://github.com/YOUR_USERNAME/equityscanner-pro.git

# Rename branch to main
git branch -M main

# Push all code to GitHub
git push -u origin main
```

**If you get an authentication error**, do this instead:

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token"
3. Give it a name and select the `repo` scope
4. Generate and copy the token
5. When Git asks for password, paste the token instead of your GitHub password

### 2.3 Verify Upload

After pushing:
1. Go to your GitHub repo page
2. You should see all your files
3. Click on `README.md` to check it renders nicely

### 2.4 Polish Your GitHub Page (Strongly Recommended)

On your repo page:
- Click the **⚙️ gear** next to "About"
- Add description
- Add these topics:
  - `python`
  - `streamlit`
  - `fastapi`
  - `finance`
  - `machine-learning`
  - `quant`
  - `backtesting`

---

## STEP 3: Deploy to Vercel (With Important Warnings)

### 3.1 Honest Warning First

**Vercel is NOT the best platform** for this project because:
- It runs **two servers** (FastAPI + Streamlit)
- Streamlit does not work well on Vercel
- Vercel is designed for serverless functions and frontend apps

**You will most likely only be able to deploy the FastAPI backend**, not the full dashboard.

### 3.2 Deploy Only the FastAPI Backend (Most Realistic Option)

#### Step-by-step:

1. Install Vercel CLI (if you haven't):
   ```bash
   npm install -g vercel
   ```

2. Login to Vercel:
   ```bash
   vercel login
   ```

3. Create a file called `vercel.json` in the root of the project with this content:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/main.py"
    }
  ]
}
```

4. Deploy:
   ```bash
   cd /home/user/stock_scanner
   vercel
   ```

5. Answer the prompts:
   - Set up and deploy? → **Y**
   - Which scope? → Choose your account
   - Link to existing project? → **N**
   - Project name? → `equityscanner-api` (or any name)
   - Directory? → Press Enter

6. After deployment, Vercel will give you a URL like:
   `https://equityscanner-api-xxx.vercel.app`

7. Test it:
   ```
   https://your-url.vercel.app/health
   https://your-url.vercel.app/premarket/predict/AAPL
   ```

### 3.3 Add Environment Variables (Optional)

If you want to use real API keys:

1. Go to your project on Vercel
2. Click **Settings** → **Environment Variables**
3. Add keys like:
   - `ALPACA_API_KEY`
   - `ALPACA_API_SECRET`
   - etc.

---

## Better Alternatives Than Vercel

If you want to deploy the **full app** (FastAPI + Streamlit dashboard), use one of these instead:

### Recommended: Railway (Best Choice)

1. Go to https://railway.app
2. Sign in with GitHub
3. New Project → Deploy from GitHub Repo
4. Select your repo
5. Add environment variables
6. Deploy

### Other Good Options
- **Render.com**
- **Fly.io**
- **Hugging Face Spaces** (great for Streamlit demos)

---

## Final Tips

- Always push to GitHub **first**
- Add screenshots to your README before sharing
- Use Railway if you want both API and dashboard working

You now have everything you need!
