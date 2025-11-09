# 🎧 VoiceBrief - AI-Powered Audio Briefings for Slack

VoiceBrief is a B2B SaaS platform that automatically converts company updates, policies, and internal documents into short, listenable audio briefings delivered directly via Slack.

## 🚀 Features

- **AI-Powered Summarization**: Uses GPT-4o to create concise, engaging 400-500 word summaries
- **Natural Text-to-Speech**: Converts summaries to natural-sounding audio using ElevenLabs
- **Slack Integration**: Posts briefings directly to your team's Slack channels
- **Interactive Tracking**: Track who listened and who completed each briefing
- **Analytics Dashboard**: View completion rates and engagement metrics
- **Multiple Input Sources**: Support for text, PDFs, URLs, Google Docs, and Notion pages

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Slack App Setup](#slack-app-setup)
- [Supabase Setup](#supabase-setup)
- [Google Docs Setup](#google-docs-setup)
- [API Endpoints](#api-endpoints)
- [Deployment](#deployment)
- [Development](#development)

## 🏗️ Architecture

```
┌─────────────┐
│   Upload    │──┐
│ (Text/PDF)  │  │
└─────────────┘  │
                 ▼
         ┌───────────────┐
         │   FastAPI     │
         │   Backend     │
         └───────┬───────┘
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
    ┌──────┐ ┌──────┐ ┌──────┐
    │ GPT  │ │ 11Labs│ │Supabase│
    │ -4o  │ │  TTS  │ │   DB   │
    └──────┘ └──────┘ └──────┘
                 │
                 ▼
         ┌───────────────┐
         │  Slack Bot    │
         │   (Message)   │
         └───────────────┘
```

## ✅ Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- OpenAI API key
- ElevenLabs API key
- Supabase account
- Slack workspace with admin access

## 🚀 Quick Start

### 1. Clone and Navigate

```bash
cd voicebrief
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Set Up Supabase Database

```bash
# Run the schema in your Supabase SQL editor
cat supabase/schema.sql
```

### 5. Run the Application

**Option A: Using Docker**
```bash
docker-compose up
```

**Option B: Direct Python**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 6. Test with Demo

```bash
curl -X POST http://localhost:8000/demo
```

This will create a sample briefing and post it to your Slack channel.

## ⚙️ Configuration

Edit `.env` with your credentials:

```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# ElevenLabs
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL  # Rachel voice

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_BUCKET=voicebrief-audio

# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_DEFAULT_CHANNEL=#daily-briefings

# Google Docs (Optional - for Google Docs integration)
GOOGLE_CREDENTIALS_FILE=/path/to/service-account.json
# Or use JSON string: GOOGLE_CREDENTIALS_JSON='{"type": "service_account", ...}'

# Application
APP_BASE_URL=https://your-domain.com
```

## 🤖 Slack App Setup

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name it "VoiceBrief" and select your workspace

### 2. Configure OAuth Scopes

Under **OAuth & Permissions**, add these Bot Token Scopes:
- `chat:write`
- `chat:write.public`
- `users:read`
- `commands`

### 3. Enable Interactive Components

1. Go to **Interactivity & Shortcuts**
2. Turn on Interactivity
3. Set Request URL: `https://your-domain.com/slack/events`

### 4. Install to Workspace

1. Go to **Install App**
2. Click "Install to Workspace"
3. Copy the **Bot User OAuth Token** to your `.env` as `SLACK_BOT_TOKEN`

### 5. Get Signing Secret

1. Go to **Basic Information**
2. Copy the **Signing Secret** to your `.env` as `SLACK_SIGNING_SECRET`

## 🗄️ Supabase Setup

### 1. Create a Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Copy the URL and anon key to your `.env`

### 2. Run Database Schema

1. Open your Supabase project
2. Go to **SQL Editor**
3. Copy and paste the contents of `supabase/schema.sql`
4. Run the query

### 3. Create Storage Bucket

1. Go to **Storage**
2. Create a new bucket named `voicebrief-audio`
3. Set it to **Public**

### 4. Configure CORS (if needed)

If hosting on a different domain, configure CORS in Supabase settings.

## 📄 Google Docs Setup

Google Docs integration allows users to paste a Google Docs URL and automatically extract the content to create voice briefings. This is **optional** - VoiceBrief works without it.

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the **Google Docs API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Docs API"
   - Click "Enable"

### 2. Create a Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Name it "VoiceBrief Service Account"
4. Click "Create and Continue"
5. Skip optional steps and click "Done"

### 3. Generate Service Account Key

1. Click on the service account you just created
2. Go to the "Keys" tab
3. Click "Add Key" → "Create new key"
4. Select "JSON" format
5. Click "Create" - a JSON file will download

### 4. Configure VoiceBrief

**Option A: Using JSON file** (recommended for local development)

```bash
# Move the downloaded JSON file to your project
mv ~/Downloads/service-account-key.json /path/to/voicebrief/

# Update .env
GOOGLE_CREDENTIALS_FILE=/path/to/voicebrief/service-account-key.json
```

**Option B: Using JSON string** (recommended for cloud deployment)

```bash
# Copy the entire JSON file content and set as environment variable
GOOGLE_CREDENTIALS_JSON='{"type": "service_account", "project_id": "...", ...}'
```

### 5. Share Google Docs with Service Account

For each Google Doc you want to extract:

1. Open the Google Doc
2. Click "Share"
3. Add the service account email (found in the JSON file, looks like: `voicebrief-sa@your-project.iam.gserviceaccount.com`)
4. Give it "Viewer" permission
5. Click "Send"

**Alternative:** Make the Google Doc accessible to "Anyone with the link" (Viewer permission)

### 6. Test Google Docs Integration

```bash
# Upload a briefing from a Google Docs URL
curl -X POST http://localhost:8000/upload \
  -F "title=Test Google Doc Briefing" \
  -F "url=https://docs.google.com/document/d/YOUR_DOC_ID/edit"
```

### Troubleshooting Google Docs

**Error: "Access denied to Google Doc"**
- Make sure the document is shared with the service account email
- Or make the document public with "Anyone with the link" access

**Error: "Google Docs service not initialized"**
- Verify `GOOGLE_CREDENTIALS_FILE` or `GOOGLE_CREDENTIALS_JSON` is set correctly
- Check the JSON file is valid and contains all required fields

**Error: "Invalid Google Docs URL"**
- Ensure you're using the full URL from the browser (e.g., `https://docs.google.com/document/d/ABC123/edit`)
- Both `/document/d/` and `/file/d/` formats are supported

## 📡 API Endpoints

### Upload a Briefing

```bash
POST /upload
Content-Type: multipart/form-data

{
  "title": "Q4 Policy Update",
  "text": "Your content here...",
  "channel": "#announcements"  # optional
}
```

### List Briefings

```bash
GET /briefings?limit=50&offset=0
```

### Get Specific Briefing

```bash
GET /briefings/{briefing_id}
```

### Get Analytics

```bash
GET /stats
GET /stats/summary
```

### Listen to Briefing

```bash
GET /listen/{briefing_id}
```

Returns an HTML page with audio player.

### Demo Endpoint

```bash
POST /demo
```

Creates a sample briefing with HR policy content.

## 🚢 Deployment

### Deploy to Railway

1. Install Railway CLI:
```bash
npm i -g @railway/cli
```

2. Login and deploy:
```bash
railway login
railway init
railway up
```

3. Set environment variables in Railway dashboard

### Deploy to Render

1. Create a new Web Service
2. Connect your repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables

### Deploy to Fly.io

1. Install Fly CLI:
```bash
curl -L https://fly.io/install.sh | sh
```

2. Launch app:
```bash
fly launch
fly secrets set OPENAI_API_KEY=... ELEVENLABS_API_KEY=...
fly deploy
```

## 🛠️ Development

### Project Structure

```
voicebrief/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic models
│   ├── services/            # Business logic
│   │   ├── openai_service.py
│   │   ├── elevenlabs_service.py
│   │   ├── supabase_service.py
│   │   ├── slack_service.py
│   │   └── file_processor.py
│   ├── routes/              # API endpoints
│   │   ├── upload.py
│   │   ├── briefings.py
│   │   ├── slack.py
│   │   ├── stats.py
│   │   └── listen.py
│   └── templates/
│       └── listen.html      # Audio player page
├── supabase/
│   └── schema.sql           # Database schema
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Local Development

```bash
# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# View logs
tail -f logs/voicebrief.log
```

## 🔐 Security Notes

- Never commit `.env` files to version control
- Use environment-specific configurations
- Enable Slack request verification in production
- Use HTTPS for all external webhooks
- Regularly rotate API keys
- Implement rate limiting for production

## 📊 Analytics & Tracking

VoiceBrief automatically tracks:
- Who received each briefing
- Who clicked "Listen"
- Who marked briefings as complete
- Completion rates per briefing
- Overall engagement metrics

Access analytics via `/stats` endpoint or `/stats/summary`.

## 🧪 Testing the Flow

1. **Upload a briefing:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "title=Test Briefing" \
  -F "text=This is a test briefing to verify the system works."
```

2. **Check Slack:** A message should appear in your configured channel

3. **Click "Listen":** Opens the audio player page

4. **Click "Mark as Done":** Updates the database and sends confirmation DM

5. **View Analytics:**
```bash
curl http://localhost:8000/stats
```

## 🐛 Troubleshooting

### Slack messages not appearing
- Verify `SLACK_BOT_TOKEN` is correct
- Check bot has permission to post in the channel
- Ensure bot is invited to the channel (`/invite @VoiceBrief`)

### Audio generation fails
- Verify `ELEVENLABS_API_KEY` is valid
- Check API quota hasn't been exceeded
- Ensure voice ID is correct

### Supabase connection errors
- Verify `SUPABASE_URL` and `SUPABASE_KEY`
- Check database schema was created
- Ensure storage bucket exists and is public

### Background tasks not running
- Check Redis is running (`docker-compose ps`)
- Verify `REDIS_URL` is correct
- Check application logs for errors

## 📝 License

MIT License - feel free to use for commercial projects!

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

## 📧 Support

For questions or issues, please open a GitHub issue or contact support.

---

**Built with:** FastAPI, OpenAI GPT-4o, ElevenLabs, Supabase, Slack SDK

**Perfect for:** HR teams, Internal Communications, Compliance, Operations
