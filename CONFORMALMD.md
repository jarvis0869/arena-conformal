# Pingash Outreach Bot

WhatsApp → Claude → Email. Finds founders, drafts messages, asks you before sending.

## Architecture

```
You (WhatsApp)
    ↓
Twilio ($0/month for sandbox)
    ↓
FastAPI on Railway (free tier)
    ↓
Claude Haiku  → intent parsing     (~$0.001/day)
Claude Sonnet → message generation (~$0.02/outreach)
    ↓
Hunter.io → find founder email (free: 25/month)
    ↓
Resend → send email (free: 3,000/month)
```

**Total cost per outreach: ~$0.02**

---

## Setup (30 minutes)

### 1. Get API Keys (all free tiers)

| Service | Get key at | Cost |
|---------|-----------|------|
| Anthropic | console.anthropic.com | ~$0.02/outreach |
| Twilio | twilio.com/try-twilio | Free sandbox |
| Hunter.io | hunter.io | 25 free searches/month |
| Resend | resend.com | 3,000 free emails/month |

### 2. Deploy to Railway (free)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
cd outreach-bot
railway init
railway up
```

Copy your Railway URL (e.g. `https://outreach-bot.railway.app`)

### 3. Set Environment Variables in Railway

Go to Railway dashboard → your project → Variables:

```
ANTHROPIC_API_KEY=sk-ant-...
HUNTER_API_KEY=your-hunter-key
RESEND_API_KEY=re_...
FROM_EMAIL=you@yourdomain.com
GITHUB_URL=https://github.com/yourusername
```

### 4. Set up Twilio WhatsApp Sandbox

1. Go to twilio.com → Messaging → Try WhatsApp
2. Follow sandbox instructions (send "join [word]" to their number)
3. Set webhook URL: `https://your-railway-url.railway.app/whatsapp`
4. Method: POST

### 5. Test it

Text your Twilio sandbox number:
```
Novoflow
```

Bot responds with founder info + draft message. Reply YES to send.

---

## Usage

```
You:  Novoflow
Bot:  👤 Georges Casassovici — Co-founder @ Novoflow
      📧 georges@novoflow.io (87% confidence)
      
      📩 Draft:
      Subject: teen founder → clinical AI co-op
      
      Georges — saw the Novoflow demo. EHR bridge problem 
      is exactly what we hit at Aeyron Health (KITE/UHN 
      clinical partnership, Google for Startups). Built 
      revenue-generating LLM SaaS (Filld). Want to build 
      with you this term. [GITHUB]
      
      Reply YES · NO · or give feedback

You:  make it shorter
Bot:  📝 Revised: [shorter version]

You:  YES
Bot:  ✅ Sent to Georges at georges@novoflow.io!
```

---

## Token Cost Breakdown

| Action | Model | Tokens | Cost |
|--------|-------|--------|------|
| Parse intent | Haiku | ~50 in, 20 out | $0.000015 |
| Find + generate | Sonnet | ~400 in, 150 out | $0.0018 |
| Revision | Sonnet | ~450 in, 150 out | $0.0019 |
| **Total per send** | | | **~$0.002** |

Running 30 outreaches costs ~$0.06 in Claude tokens.

---

## Using Claude Code Instead

If you want to build/modify this interactively:

```bash
# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Navigate to project
cd outreach-bot

# Start Claude Code
claude

# Then tell it what to add, e.g.:
# "Add Apollo.io integration to find emails"
# "Add a /status endpoint showing sent outreach count"
# "Store sent outreach in Supabase instead of memory"
```

---

## Upgrade Path

| When | Add |
|------|-----|
| Restart loses sessions | Supabase (free) for persistence |
| 25 Hunter searches/month not enough | Apollo.io Basic ($49/mo) |
| Want your own WhatsApp number | WhatsApp Business API via Twilio |
| Want to track open rates | Add tracking pixel to emails |
