# Supabase Authentication Setup Guide

This guide explains how to set up Supabase authentication for the A2Z DSA Sheet project.

## Prerequisites

- A Supabase account and project
- Access to the Supabase Dashboard

## Configuration Details

The project is configured with:
- **Supabase URL**: `https://bgfrokougjvzyvmehhsw.supabase.co`
- **Site URL**: `https://jrchintu.github.io/a2z/`

## Step 1: Configure Authentication Providers

### Email/Password Authentication
1. Go to **Authentication** > **Providers** in your Supabase Dashboard
2. Ensure **Email** provider is enabled
3. Configure email templates if desired

### Google OAuth (Optional)
1. Go to **Authentication** > **Providers** > **Google**
2. Create OAuth credentials in [Google Cloud Console](https://console.cloud.google.com/)
3. Add the Client ID and Client Secret
4. Add `https://bgfrokougjvzyvmehhsw.supabase.co/auth/v1/callback` as an authorized redirect URI in Google Console

### GitHub OAuth (Optional)
1. Go to **Authentication** > **Providers** > **GitHub**
2. Create OAuth app in [GitHub Developer Settings](https://github.com/settings/developers)
3. Set callback URL to `https://bgfrokougjvzyvmehhsw.supabase.co/auth/v1/callback`
4. Add the Client ID and Client Secret to Supabase

## Step 2: Configure URL Settings

1. Go to **Authentication** > **URL Configuration**
2. Set **Site URL** to: `https://jrchintu.github.io/a2z/`
3. Add to **Redirect URLs**:
   - `https://jrchintu.github.io/a2z/`
   - `https://jrchintu.github.io/a2z/index.html`
   - `https://jrchintu.github.io/a2z/login.html`
   - `https://jrchintu.github.io/a2z/reset-password.html`

## Step 3: Set Up Database

1. Go to **SQL Editor** in your Supabase Dashboard
2. Copy the contents of [`supabase/schema.sql`](./schema.sql)
3. Run the SQL to create the `user_progress` table with proper RLS policies

## Step 4: Verify CORS Settings

For GitHub Pages hosting, ensure your Supabase project allows requests from:
- `https://jrchintu.github.io`

This is typically handled automatically, but verify in **Settings** > **API** if you encounter CORS issues.

## Features

### Authentication Methods
- ✅ Email/Password sign up and sign in
- ✅ Password reset via email
- ✅ Google OAuth (if configured)
- ✅ GitHub OAuth (if configured)

### Progress Syncing
- User progress (completed topics) syncs to cloud
- Progress merges across devices (completed items are preserved)
- Works offline with localStorage fallback
- Real-time sync indicator shows when saving

## File Structure

```
public/
├── js/
│   └── supabase-config.js   # Supabase client configuration
├── login.html               # Login/signup page
├── reset-password.html      # Password reset page
└── index.html               # Main page with auth UI

templates/
└── template.html            # Article template with auth UI

supabase/
└── schema.sql               # Database schema
```

## Security Notes

1. The API key used is the **publishable/anon** key, which is safe to expose in client-side code
2. Row Level Security (RLS) is enabled on the `user_progress` table
3. Users can only access their own progress data
4. Never expose your service role key in client-side code

## Troubleshooting

### "Invalid login credentials"
- Verify email and password are correct
- Check if email confirmation is required

### OAuth redirect issues
- Ensure redirect URLs are properly configured in Supabase
- Check that OAuth providers have the correct callback URL

### Progress not syncing
- Check browser console for errors
- Verify RLS policies are correctly set up
- Ensure user is logged in

### CORS errors
- Verify Site URL configuration in Supabase
- Check that the request origin matches allowed URLs

## Local Development

For local testing, add these to your Supabase redirect URLs:
- `http://localhost:3000/`
- `http://127.0.0.1:5500/` (Live Server)
