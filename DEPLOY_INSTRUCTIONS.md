# EquityScanner Pro — Complete Deployment Guide

This guide gives you **copy-paste ready** step-by-step instructions for:

1. Uploading the project to **GitHub**
2. Deploying to **Vercel** (with honest limitations)

---

## Pre-Upload Checklist (Do This First)

Run these commands before starting:

```bash
cd /home/user/stock_scanner

# 1. Make sure everything is committed
git status
git add -A
git commit -m "Final preparation before GitHub upload" || echo "Nothing to commit"

# 2. Verify key files exist
ls README.md run_all.py dashboard/app.py api/main.py cli.py docker-compose.yml

# 3. Check current branch
git branch --show-current
```

---

## Part 1: Upload to GitHub (Detailed)

### Step 1: Create a New Repository on GitHub

1. Open this link in your browser: [https://github.com/new](https://github.com/new)
2. Fill in the form:
   - **Repository name**: `equityscanner-pro` (recommended) or any name you like
   - **Description**: `Real-time stock scanner with pre-market predictive analytics (FastAPI + Streamlit)`
   - Visibility: **Public** (recommended)
   - **Important**:
     - ❌ Do **NOT** check "Add a README file"
     - ❌ Do **NOT** add a `.gitignore`
     - ❌ Do **NOT** choose a license
3. Click the green **"Create repository"** button.

### Step 2: Connect Your Local Project to GitHub

After creating the repo, GitHub will show you two options. Use the **"...or push an existing repository from the command line"** section.

Replace `YOUR_USERNAME` with your actual GitHub username in the commands below:

```bash
cd /home/user/stock_scanner

# Add GitHub as the remote
git remote add origin https://github.com/YOUR_USERNAME/equityscanner-pro.git

# Rename the default branch to "main" (modern standard)
git branch -M main

# Push all your code
git push -u origin main
```

If you get an authentication error, use a **Personal Access Token** instead of your password:
- Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
- Generate a new token with `repo` scope
- Use the token when Git asks for password

### Step 3: Verify the Upload

1. Go to your repo on GitHub (refresh the page)
2. You should see:
   - `README.md` with nice formatting
   - `dashboard/`, `api/`, `tests/` folders
   - `run_all.py`, `cli.py`, `Dockerfile`, etc.
3. Click on the **README.md** to make sure it renders correctly

### Step 4: Improve Your GitHub Repo Page (Recommended)

On your GitHub repository page:

1. Click the **⚙️ gear icon** next to "About" (on the right side)
2. Add:
   - **Description**: `Real-time equity scanner with pre-market ML predictions`
   - **Website**: (leave empty for now)
   - **Topics**: Add these by clicking "Add topics":
     - `python`
     - `streamlit`
     - `fastapi`
     - `finance`
     - `machine-learning`
     - `quant`
     - `stock-market`
     - `backtesting`

This makes your project look much more professional.

---

## Part 2: Deploy to Vercel

**⚠️ CRITICAL WARNING**

This application is **not well suited** for Vercel.

### Why Vercel is a Poor Fit

- Your app runs **two servers** at the same time (FastAPI + Streamlit)
- Streamlit is a full web server — Vercel is designed for serverless functions
- Long-running processes and WebSockets don't work well on Vercel
- You will likely only be able to deploy the **FastAPI backend**, not the dashboard

### Realistic Options on Vercel

#### Option A: Deploy Only the FastAPI Backend (Most Realistic)

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Login:
   ```bash
   vercel login
   ```

3. Create a `vercel.json` file in the root of the project with this content:

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
    { "src": "/(.*)", "dest": "api/main.py" }
  ]
}
```

4. Deploy:
   ```bash
   cd /home/user/stock_scanner
   vercel
   ```

5. When asked:
   - "Set up and deploy" → Yes
   - "Which scope" → Your account
   - "Link to existing project?" → No
   - "What's your project's name?" → equityscanner-api (or anything)
   - "Directory" → `./`

6. After deployment, go to your Vercel project dashboard and add environment variables if needed.

**Result**: You will get a URL like `https://equityscanner-api.vercel.app` that serves the FastAPI backend.

#### Option B: Full App (Not Recommended)

Deploying both FastAPI + Streamlit on Vercel requires major changes (converting the dashboard to Next.js/React). This is usually not worth it.

---

## Much Better Deployment Alternatives (Recommended)

Instead of Vercel, use one of these platforms:

| Platform       | Best For                      | Free Tier Quality | Recommendation |
|----------------|-------------------------------|-------------------|----------------|
| **Railway**    | Full Python apps              | Very good         | ★★★★★ Best choice |
| **Render**     | APIs + Web services           | Very good         | ★★★★☆ Excellent |
| **Fly.io**     | Docker containers             | Limited           | ★★★★☆ Good |
| **Hugging Face Spaces** | Streamlit demos        | Free              | ★★★★☆ Great for demo |

### Quick Railway Deployment (Recommended)

1. Go to [https://railway.app](https://railway.app)
2. Sign in with GitHub
3. Click **"New Project"** → **"Deploy from GitHub Repo"**
4. Select your `equityscanner-pro` repository
5. Railway will detect the `Dockerfile` or you can use the `docker-compose.yml`
6. Add environment variables in the dashboard
7. Deploy

You will get public URLs for both the API and dashboard.

---

## Final Checklist Before Going Live

- [ ] Push latest code to GitHub
- [ ] Add at least 2-3 screenshots to the README
- [ ] Add a short demo GIF (highly recommended)
- [ ] Set repository topics on GitHub
- [ ] Test `python run_all.py` locally one more time
- [ ] Decide on deployment platform (Railway is strongly recommended over Vercel)

---

## Need Help After Uploading?

Once your code is on GitHub, share the link and I can help with:
- Specific Vercel troubleshooting
- Railway deployment steps
- Adding a proper domain
- Setting up CI/CD

Good luck!
ENDOFFILE
echo "DEPLOY_INSTRUCTIONS.md updated with detailed steps"