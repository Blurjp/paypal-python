# Google Docs OAuth2 Integration - Setup Guide

VoiceBrief now supports **OAuth2 user authentication** for Google Docs! This allows users to connect their personal Google account once and create voice briefings from any of their Google Docs - just like modern apps integrate with Google.

## 🎯 How It Works

### User Experience

1. User types `/voicebrief-google` in Slack
2. Clicks "Connect Google Account" button
3. Gets redirected to Google to authorize access
4. Returns to Slack with account connected ✅
5. Can now create briefings from any Google Doc they have access to!

### No More Manual Sharing!

Unlike service accounts that require sharing each document, OAuth2 users can:
- Access **any** Google Doc they own or have permission to view
- No need to share individual documents
- No service account email to remember
- Works just like Google Drive, Gmail, or other Google integrations

---

## 🔧 Setup Instructions

### 1. Create Google Cloud Project OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create or select your project
3. Navigate to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth client ID**
5. If prompted, configure the OAuth consent screen:
   - User Type: **External** (for general users) or **Internal** (for Google Workspace domain)
   - App name: `VoiceBrief`
   - Support email: Your email
   - Scopes: Add these scopes:
     - `.../auth/documents.readonly` (View your Google Docs)
     - `.../auth/userinfo.email` (See your email address)
     - `openid`
   - Authorized domains: Add your domain (e.g., `voicebrief.app`)
   - Developer contact: Your email

6. Back in Credentials, select application type: **Web application**
7. Name: `VoiceBrief Web Client`
8. Authorized redirect URIs: Add your callback URL:
   ```
   https://your-domain.com/auth/google/callback
   ```
9. Click **Create**
10. **Save the Client ID and Client Secret** - you'll need these!

### 2. Enable Required APIs

1. Go to **APIs & Services** → **Library**
2. Search and enable:
   - **Google Docs API**
   - **Google OAuth2 API** (should be enabled by default)

### 3. Configure Environment Variables

Add these to your `.env` file:

```bash
# Google OAuth2 Configuration
GOOGLE_CLIENT_ID=123456789-abc123.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123xyz...
GOOGLE_OAUTH_REDIRECT_URI=https://your-domain.com/auth/google/callback

# Make sure APP_BASE_URL matches your deployment
APP_BASE_URL=https://your-domain.com
```

### 4. Update Supabase Database

Run this SQL in your Supabase SQL editor:

```sql
-- Create table for storing user OAuth tokens
CREATE TABLE IF NOT EXISTS google_oauth_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL UNIQUE, -- Slack user ID
    user_email VARCHAR(255),
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expiry TIMESTAMP WITH TIME ZONE,
    scopes TEXT[], -- Array of granted scopes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_google_oauth_tokens_user_id ON google_oauth_tokens(user_id);
```

### 5. Configure Slack Slash Command

1. Go to your Slack App settings at [api.slack.com/apps](https://api.slack.com/apps)
2. Navigate to **Slash Commands**
3. Click **Create New Command**
4. Configure:
   - Command: `/voicebrief-google`
   - Request URL: `https://your-domain.com/slack/commands/google`
   - Short Description: `Connect your Google account to VoiceBrief`
   - Usage Hint: `[connect|status|disconnect]`
5. Click **Save**

### 6. Deploy and Test

1. Deploy your updated VoiceBrief application
2. In Slack, type: `/voicebrief-google`
3. Click "Connect Google Account"
4. Authorize Google access
5. You should see "Connected Successfully!" ✅

---

## 📱 Usage

### Connecting Google Account

**Method 1: Slash Command**
```
/voicebrief-google
```

**Method 2: During Upload**
When uploading a Google Docs URL without being connected, users will be prompted to connect.

### Checking Connection Status

```
/voicebrief-google status
```

### Disconnecting

```
/voicebrief-google disconnect
```

### Creating Briefings from Google Docs

Once connected, users can create briefings just by pasting a Google Docs URL:

```bash
# Via API
curl -X POST https://your-domain.com/upload \
  -F "title=Q4 OKRs" \
  -F "url=https://docs.google.com/document/d/ABC123/edit" \
  -F "user_id=U12345"  # Slack user ID
```

Or through Slack upload interface (if implemented).

---

## 🔒 Security & Privacy

### What Access Do We Request?

- **documents.readonly**: Read-only access to Google Docs
- **userinfo.email**: User's email address (for identification)
- **openid**: Basic profile information

### Data Storage

- Access tokens are stored encrypted in Supabase
- Refresh tokens allow seamless re-authentication
- Tokens are user-specific (per Slack user ID)
- Users can disconnect anytime

### Token Refresh

- Access tokens automatically refresh when expired
- No user intervention required
- Refresh tokens are long-lived (6 months+)

---

## 🔄 Architecture Flow

```
┌─────────────────────────────────────────┐
│ User in Slack                           │
│  Types: /voicebrief-google              │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Slack Command Handler                   │
│  Generates OAuth URL with state         │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Google OAuth Consent Screen             │
│  User authorizes access                 │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ OAuth Callback Handler                  │
│  Exchanges code for tokens              │
│  Stores in database (Supabase)          │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Success Page                            │
│  "Connected Successfully!" ✅           │
└─────────────────────────────────────────┘
```

**When Creating Briefing:**

```
┌─────────────────────────────────────────┐
│ User pastes Google Docs URL             │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ File Processor                          │
│  Detects Google Docs URL                │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Google Docs Service                     │
│  Fetches user tokens from DB            │
│  Refreshes if expired                   │
│  Calls Google Docs API                  │
│  Returns document text                  │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ VoiceBrief Processing Pipeline          │
│  OpenAI → ElevenLabs → Supabase → Slack│
└─────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### "Redirect URI mismatch" error

- Make sure your `GOOGLE_OAUTH_REDIRECT_URI` in `.env` **exactly** matches what you configured in Google Cloud Console
- Check for `http` vs `https`, trailing slashes, etc.

### "Access denied" error

- Make sure the Google Docs API is enabled in your project
- Check that your OAuth consent screen is published (if using External user type)
- Verify the scopes are correctly configured

### User sees "Not connected" after connecting

- Check database to verify tokens were saved
- Check logs for any errors during callback
- Verify Slack user_id is being passed correctly

### Token refresh fails

- Ensure you requested `access_type='offline'` during OAuth (already configured)
- Check that refresh_token was saved in database
- Verify Google OAuth credentials haven't been revoked

---

## 🚀 Next Steps

Now that OAuth2 is set up, you can:

1. **Add Google Docs picker UI**: Let users browse and select their Google Docs
2. **Batch processing**: Allow users to convert multiple Google Docs at once
3. **Scheduled briefings**: Auto-create briefings from specific Google Docs on schedule
4. **Google Drive integration**: Extend to Google Slides, Sheets, etc.

---

## 📊 Comparison: Service Account vs OAuth2

| Feature | Service Account | OAuth2 (Recommended) |
|---------|----------------|----------------------|
| **Setup** | Create SA key, download JSON | Create OAuth client ID |
| **User Experience** | Must share each document | Works with all user's docs |
| **Access Control** | Server has access | User controls access |
| **Sharing Required** | ✅ Yes, every document | ❌ No |
| **Suitable For** | Server automation | User-driven actions |
| **Like Other Apps** | ❌ No | ✅ Yes (Gmail, Drive, etc.) |

---

**✨ Congratulations!** Your VoiceBrief now has modern, user-friendly Google Docs integration!

Users can connect once and instantly create voice briefings from any of their Google Docs - no manual sharing required.
