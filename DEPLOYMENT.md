# 🚀 Deployment Guide — HPC Stochastic Pricing Kernel

## Deploy to Streamlit Community Cloud (FREE, 5 minutes)

You will get a public URL like: `https://hpc-pricing-kernel.streamlit.app`
This is the link you put on your resume and LinkedIn.

---

## STEP 1 — Create a GitHub Account (if you don't have one)
Go to https://github.com and sign up. It's free.

---

## STEP 2 — Create a New GitHub Repository

1. Click the **+** icon (top right) → **New repository**
2. Name it: `hpc-pricing-kernel`
3. Set it to **Public**
4. Do NOT initialize with README (we already have one)
5. Click **Create repository**

---

## STEP 3 — Upload the Project Files to GitHub

### Option A: GitHub Web Interface (easiest, no git needed)

1. On your new repo page, click **uploading an existing file**
2. Drag and drop the ENTIRE contents of the `hpc_deploy/` folder:
   ```
   app.py
   requirements.txt
   README.md
   .gitignore
   python/          ← entire folder
   src/             ← entire folder
   tests/           ← entire folder
   .streamlit/      ← entire folder (with config.toml)
   ```
3. Scroll down, click **Commit changes**

### Option B: Git CLI (if you have git installed)

```bash
cd hpc_deploy/
git init
git add .
git commit -m "Initial commit: HPC Stochastic Pricing Kernel"
git remote add origin https://github.com/YOUR_USERNAME/hpc-pricing-kernel.git
git branch -M main
git push -u origin main
```
Replace `YOUR_USERNAME` with your GitHub username.

---

## STEP 4 — Deploy on Streamlit Community Cloud

1. Go to **https://share.streamlit.io**
2. Click **Sign in with GitHub** — authorize Streamlit
3. Click **Create app** (top right)
4. Fill in:
   - **Repository**: `YOUR_USERNAME/hpc-pricing-kernel`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL** (optional): choose a custom subdomain like `hpc-pricing-kernel`
5. Click **Deploy!**
6. Wait ~2-3 minutes while dependencies install

Your app is now LIVE at:
**https://hpc-pricing-kernel.streamlit.app**

---

## STEP 5 — Put It On Your Resume

Resume bullet point:
```
Live demo: https://hpc-pricing-kernel.streamlit.app
GitHub:    https://github.com/YOUR_USERNAME/hpc-pricing-kernel
```

LinkedIn:
- Add the Streamlit URL to your project portfolio
- Pin the GitHub repo on your profile

---

## Troubleshooting

**App won't start / import error:**
- Check Streamlit Cloud logs (click "Manage app" → "Logs")
- Make sure `requirements.txt` is in the root of the repo
- Make sure `app.py` is in the root (not inside a subfolder)

**Missing module error:**
- Add the missing package to `requirements.txt` and push to GitHub
- Streamlit Cloud will auto-redeploy

**App is slow on first load:**
- Normal — Streamlit Cloud spins down free apps after inactivity
- First visitor after sleep takes ~30 seconds to wake up

---

## File Structure (what your GitHub repo should look like)

```
hpc-pricing-kernel/          ← GitHub repo root
├── app.py                   ← MAIN FILE (Streamlit entry point)
├── requirements.txt         ← Python dependencies
├── README.md                ← Project documentation
├── .gitignore
├── .streamlit/
│   └── config.toml          ← Dark theme config
├── python/
│   ├── __init__.py
│   └── models/
│       ├── __init__.py
│       └── pricing_engine.py
├── src/
│   ├── engines/
│   │   ├── monte_carlo.hpp
│   │   ├── cos_engine.hpp
│   │   └── lsmc_engine.hpp
│   └── bindings/
│       └── bindings.cpp
└── tests/
    └── test_pricing_engines.py
```
