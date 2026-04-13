# Render Deployment Guide for TransLingua

## Prerequisites

1. **Groq API Key** - Get one free at https://console.groq.com/keys
2. **GitHub Account** - Push your code to GitHub
3. **Render Account** - Sign up at https://render.com

## Step-by-Step Deployment

### 1. Prepare Your Repository

Remove the actual `.env` file from your repo (if accidentally committed):
```bash
git rm --cached .env
git add .gitignore
git commit -m "Remove .env with API keys"
```

The `.env` file should NEVER be committed. Use `.env.example` instead.

### 2. Push Code to GitHub

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 3. Connect GitHub to Render

1. Go to https://render.com/dashboard
2. Click **New +** → **Web Service**
3. Select **Deploy from a Git repository**
4. Connect your GitHub account
5. Select your `translingua` repository
6. Click **Connect**

### 4. Configure Render Service

Fill in the service settings:

| Setting | Value |
|---------|-------|
| **Name** | translingua |
| **Environment** | Docker |
| **Region** | Choose closest to users |
| **Branch** | main |
| **Plan** | Free (or upgrade as needed) |

### 5. Add Environment Variables

In the Render dashboard, go to **Environment**:

```
USE_LLM=true
LLM_API_KEY=<your_groq_api_key>
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.1-8b-instant
HOST=0.0.0.0
PORT=10000
TESSERACT_CMD=tesseract
```

⚠️ **IMPORTANT**: 
- Set `LLM_API_KEY` as a **Secret** (not public)
- Never put real API keys in render.yaml
- Click the eye icon to hide sensitive values

### 6. Deploy

1. Click **Create Web Service**
2. Render will automatically:
   - Build the Docker image
   - Install dependencies from requirements.txt
   - Download the translation model
   - Start the server

This typically takes **5-10 minutes** on the free tier.

### 7. Verify Deployment

Once deployed, you'll get a URL like: `https://translingua-xxx.onrender.com`

Test the API:
```bash
curl -X POST https://translingua-xxx.onrender.com/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "नेपाल एक देश हो।",
    "language": "nepali"
  }'
```

## Troubleshooting

### Build Fails
- Check the **Logs** tab in Render dashboard
- Common issues:
  - Missing Groq API key → Add to Environment variables
  - Dependency conflict → Run `pip install -r requirements.txt` locally
  - Model download timeout → Increase build timeout in render.yaml

### Runtime Errors
- Check **Logs** → **Runtime logs**
- Memory issues → Upgrade from free tier
- API key expired → Update `LLM_API_KEY` in Render dashboard

### Model Downloads
First time startup downloads the translation model (~1.5GB):
- This is normal and happens once
- Subsequent restarts are much faster
- The data persists in the ephemeral disk

## Upgrading Components

### Update Model
To use a different Groq model:
1. Go to Render dashboard
2. Click **Settings**
3. Find **Environment** → `LLM_MODEL`
4. Change value (e.g., `gemma-7b-it`)
5. Click **Update**
6. Service will restart automatically

### Update API Keys
1. Go to **Environment**
2. Click the **Secret** value for `LLM_API_KEY`
3. Paste the new key
4. Click **Save**
5. Service restarts

## Cost Optimization

- **Free tier**: 750 hours/month (enough for small projects)
- **Paid tiers**: Start at $7/month
- **Sleep behavior**: After 15 minutes idle, requests take ~10-30s to wake up
- To avoid sleep: Upgrade to **Starter** plan or higher

## Custom Domain

To use your own domain:
1. Render dashboard → **Settings** → **Custom Domain**
2. Enter your domain name
3. Add CNAME record to DNS:
   ```
   Name: your-domain.com
   Type: CNAME
   Value: translingua-xxx.onrender.com
   ```
4. Wait for DNS propagation (usually < 1 hour)

## Monitoring & Alerts

- **Logs**: Real-time output in Render dashboard
- **Metrics**: CPU, Memory, Request count (on paid plans)
- **Email alerts**: Set up for deployment failures (Premium)

## Cleanup / Deletion

To remove your service:
1. Render dashboard → Select service
2. **Settings** → Scroll to bottom → **Delete Web Service**
3. Confirm deletion

---

**Questions?** Check [Render Documentation](https://render.com/docs)
