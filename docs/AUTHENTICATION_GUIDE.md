# Adding Authentication to Financial Analysis App

## 🎯 **Goal**
Add simple email-based authentication to collect user data (not for charging).

**Recommended Approach:** Supabase with Magic Link authentication

---

## 📋 **Overview**

### **What You'll Get:**
- ✅ User sign-in via email (magic link)
- ✅ User database (email, preferences)
- ✅ Session management
- ✅ Free tier (50,000 users)
- ✅ Easy to add payments later

### **Time Required:** 2-3 hours

### **Components:**
1. Supabase project setup (15 min)
2. Gradio UI integration (1 hour)
3. Modal deployment integration (1 hour)
4. User data storage (30 min)

---

## 🚀 **Step 1: Supabase Setup (15 min)**

### **1.1 Create Supabase Account**
```bash
# Go to https://supabase.com
# Click "Start your project"
# Sign up with GitHub (easiest)
```

### **1.2 Create New Project**
```
Project name: financial-analysis-app
Database password: [generate strong password]
Region: [closest to your users]
Pricing: Free
```

### **1.3 Get API Keys**
```
# In Supabase Dashboard:
# Settings → API

# You'll need:
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### **1.4 Enable Authentication**
```
# In Supabase Dashboard:
# Authentication → Settings

# Enable:
☑ Email/Password
☑ Magic Link (email-only sign in)

# Email templates are pre-configured!
```

---

## 💻 **Step 2: Install Dependencies**

```bash
cd ~/projects/financial_analysis

# Install Supabase client
pip install supabase

# Add to requirements.txt
echo "supabase>=2.0.0" >> requirements.txt
```

---

## 🔧 **Step 3: Create Auth Module**

### **Create: `financial_research_agent/auth/supabase_auth.py`**

```python
"""
Supabase authentication integration.
Handles user sign-in, session management, and user data.
"""

import os
from typing import Optional, Dict
from supabase import create_client, Client
from datetime import datetime


class SupabaseAuth:
    """Handle user authentication with Supabase."""
    
    def __init__(self):
        """Initialize Supabase client."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise ValueError(
                "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_ANON_KEY"
            )
        
        self.client: Client = create_client(url, key)
    
    def send_magic_link(self, email: str) -> Dict[str, any]:
        """
        Send magic link to user's email.
        
        Args:
            email: User's email address
            
        Returns:
            Dict with success status and message
        """
        try:
            response = self.client.auth.sign_in_with_otp({
                "email": email,
                "options": {
                    "email_redirect_to": os.getenv("AUTH_REDIRECT_URL", "http://localhost:7860/auth/callback")
                }
            })
            
            return {
                "success": True,
                "message": f"Magic link sent to {email}. Check your inbox!"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify magic link token.
        
        Args:
            token: Token from magic link URL
            
        Returns:
            User data if valid, None otherwise
        """
        try:
            response = self.client.auth.verify_otp({
                "token": token,
                "type": "magiclink"
            })
            return response.user
        except Exception as e:
            print(f"Token verification failed: {e}")
            return None
    
    def get_user(self, access_token: str) -> Optional[Dict]:
        """
        Get current user from access token.
        
        Args:
            access_token: User's session token
            
        Returns:
            User data if valid session
        """
        try:
            response = self.client.auth.get_user(access_token)
            return response.user
        except Exception as e:
            print(f"Failed to get user: {e}")
            return None
    
    def sign_out(self, access_token: str) -> bool:
        """
        Sign out user.
        
        Args:
            access_token: User's session token
            
        Returns:
            True if successful
        """
        try:
            self.client.auth.sign_out()
            return True
        except Exception as e:
            print(f"Sign out failed: {e}")
            return False
    
    def save_user_metadata(self, user_id: str, metadata: Dict) -> bool:
        """
        Save user preferences/metadata.
        
        Args:
            user_id: User's ID
            metadata: Dict of preferences (e.g., favorite tickers)
            
        Returns:
            True if successful
        """
        try:
            # Create users table if needed (see migration below)
            self.client.table("users").upsert({
                "id": user_id,
                "metadata": metadata,
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            return True
        except Exception as e:
            print(f"Failed to save metadata: {e}")
            return False
    
    def get_user_metadata(self, user_id: str) -> Optional[Dict]:
        """
        Get user preferences/metadata.
        
        Args:
            user_id: User's ID
            
        Returns:
            User metadata dict or None
        """
        try:
            response = self.client.table("users").select("*").eq("id", user_id).execute()
            if response.data:
                return response.data[0].get("metadata", {})
            return None
        except Exception as e:
            print(f"Failed to get metadata: {e}")
            return None
```

---

## 🎨 **Step 4: Update Gradio UI**

### **Create: `financial_research_agent/ui/auth_ui.py`**

```python
"""
Gradio authentication UI components.
"""

import gradio as gr
from financial_research_agent.auth.supabase_auth import SupabaseAuth


class AuthUI:
    """Authentication UI for Gradio."""
    
    def __init__(self):
        self.auth = SupabaseAuth()
        self.current_user = None
    
    def create_auth_interface(self):
        """Create authentication UI components."""
        
        with gr.Blocks() as auth_interface:
            gr.Markdown("# 🔐 Sign In")
            gr.Markdown("Enter your email to receive a magic link")
            
            with gr.Row():
                email_input = gr.Textbox(
                    label="Email",
                    placeholder="your@email.com",
                    type="email"
                )
            
            sign_in_btn = gr.Button("Send Magic Link", variant="primary")
            status_msg = gr.Markdown("")
            
            def handle_sign_in(email):
                if not email or "@" not in email:
                    return "❌ Please enter a valid email address"
                
                result = self.auth.send_magic_link(email)
                
                if result["success"]:
                    return f"✅ {result['message']}"
                else:
                    return f"❌ {result['message']}"
            
            sign_in_btn.click(
                fn=handle_sign_in,
                inputs=[email_input],
                outputs=[status_msg]
            )
        
        return auth_interface
    
    def create_user_panel(self, user_email: str):
        """Create panel showing logged-in user."""
        
        with gr.Blocks() as user_panel:
            gr.Markdown(f"## 👤 Signed in as: {user_email}")
            sign_out_btn = gr.Button("Sign Out")
            
            def handle_sign_out():
                self.current_user = None
                return "Signed out successfully"
            
            sign_out_btn.click(
                fn=handle_sign_out,
                outputs=[gr.Markdown()]
            )
        
        return user_panel
```

---

## 🔄 **Step 5: Update Main Gradio App**

### **Update: `launch_web_app.py`**

```python
import gradio as gr
from financial_research_agent.ui.auth_ui import AuthUI

# Initialize auth
auth_ui = AuthUI()

# Create main interface
with gr.Blocks(title="Financial Analysis") as app:
    
    # State to track user
    user_state = gr.State(None)
    
    with gr.Tabs() as tabs:
        # Auth Tab
        with gr.Tab("Sign In"):
            auth_interface = auth_ui.create_auth_interface()
        
        # Analysis Tab (requires auth)
        with gr.Tab("Run Analysis"):
            gr.Markdown("## 📊 Financial Analysis")
            
            # Check if user is signed in
            @gr.render(inputs=[user_state])
            def show_analysis_ui(user):
                if not user:
                    gr.Markdown("⚠️ Please sign in to use this feature")
                    return
                
                # Your existing analysis UI here
                ticker_input = gr.Textbox(label="Ticker Symbol")
                analyze_btn = gr.Button("Analyze", variant="primary")
                # ... rest of your UI
        
        # History Tab (requires auth)
        with gr.Tab("My Analyses"):
            @gr.render(inputs=[user_state])
            def show_history(user):
                if not user:
                    gr.Markdown("⚠️ Please sign in to view history")
                    return
                
                gr.Markdown(f"## Analysis history for {user['email']}")
                # Load user's past analyses from database

# Launch
app.launch(server_name="0.0.0.0", server_port=7860)
```

---

## 🗄️ **Step 6: Create Users Table**

### **In Supabase Dashboard → SQL Editor:**

```sql
-- Enable UUID extension (required for uuid_generate_v4)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table for metadata
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create analyses table to track user analyses
CREATE TABLE IF NOT EXISTS analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    report_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Store summary for quick access
    executive_summary TEXT,
    key_metrics JSONB
);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own data"
    ON users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own data"
    ON users FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can view own analyses"
    ON analyses FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own analyses"
    ON analyses FOR INSERT
    WITH CHECK (auth.uid() = user_id);
```

---

## 🚀 **Step 7: Modal Integration**

### **Update: `modal_app.py`**

```python
import modal
from financial_research_agent.auth.supabase_auth import SupabaseAuth

# Add Supabase secrets
app = modal.App("financial-research-agent")

# Add to your existing image
image = modal.Image.debian_slim().pip_install(
    "supabase>=2.0.0",
    # ... your other packages
)

@stub.function(
    secrets=[
        modal.Secret.from_name("openai-secret"),
        modal.Secret.from_name("supabase-secret"),  # NEW!
    ]
)
def run_analysis_with_auth(ticker: str, user_id: str):
    """Run analysis and save to user's history."""
    
    # Run analysis (your existing code)
    result = run_financial_analysis(ticker)
    
    # Save to user's history
    auth = SupabaseAuth()
    auth.client.table("analyses").insert({
        "user_id": user_id,
        "ticker": ticker,
        "executive_summary": result.get("executive_summary"),
        "report_path": result.get("report_path"),
        "key_metrics": result.get("key_metrics")
    }).execute()
    
    return result
```

---

## 🔐 **Step 8: Environment Variables**

### **Update: `.env`**

```bash
# Existing
OPENAI_API_KEY=sk-proj-...
BRAVE_API_KEY=BSA...

# NEW - Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Auth redirect URL (use your production URL when deployed)
AUTH_REDIRECT_URL=http://localhost:7860/auth/callback
```

### **Modal Secrets:**

```bash
# Create Supabase secret in Modal
modal secret create supabase-secret \
    SUPABASE_URL=https://xxxxx.supabase.co \
    SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 🧪 **Step 9: Test Authentication**

### **Test Script: `test_auth.py`**

```python
from financial_research_agent.auth.supabase_auth import SupabaseAuth

auth = SupabaseAuth()

# Test 1: Send magic link
result = auth.send_magic_link("your@email.com")
print(f"Magic link: {result}")

# Check your email, click the link

# Test 2: Verify you can get user
# (After clicking magic link, you'll have a token)
user = auth.get_user("token_from_url")
print(f"User: {user}")

# Test 3: Save metadata
auth.save_user_metadata(user['id'], {
    "favorite_tickers": ["AAPL", "MSFT", "GOOGL"],
    "analysis_count": 5
})

# Test 4: Get metadata
metadata = auth.get_user_metadata(user['id'])
print(f"Metadata: {metadata}")
```

---

## 📊 **Step 10: Track User Activity**

### **Create: `financial_research_agent/analytics/user_analytics.py`**

```python
"""Track user activity for analytics (not charging, just metrics)."""

from supabase import Client
from datetime import datetime


class UserAnalytics:
    """Track user activity."""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
    
    def track_analysis(self, user_id: str, ticker: str):
        """Track when user runs an analysis."""
        self.client.table("user_activity").insert({
            "user_id": user_id,
            "action": "run_analysis",
            "ticker": ticker,
            "timestamp": datetime.utcnow().isoformat()
        }).execute()
    
    def get_user_stats(self, user_id: str) -> dict:
        """Get user's usage statistics."""
        # Count analyses
        analyses = self.client.table("analyses")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .execute()
        
        # Get most analyzed tickers
        top_tickers = self.client.table("analyses")\
            .select("ticker")\
            .eq("user_id", user_id)\
            .limit(5)\
            .execute()
        
        return {
            "total_analyses": analyses.count,
            "top_tickers": [r["ticker"] for r in top_tickers.data],
            "member_since": "2025-01-15"  # Get from users table
        }
```

---

## 🎯 **What You Get**

### **User Features:**
- ✅ Email-based sign-in (no password needed)
- ✅ Session persistence
- ✅ Analysis history
- ✅ Usage statistics
- ✅ Personalized experience

### **You Get:**
- ✅ User email addresses
- ✅ Usage analytics
- ✅ User preferences
- ✅ Activity tracking
- ✅ Foundation for future features (payments, teams, etc.)

---

## 💰 **Cost**

**Supabase Free Tier:**
- 50,000 monthly active users
- 500 MB database storage
- 1 GB file storage
- Unlimited API requests

**When you exceed free tier:**
- Pro: $25/month (100,000 MAU)
- Team: $599/month (unlimited)

**For your stage:** Free tier is perfect!

---

## 🚀 **Deployment Checklist**

- [ ] Create Supabase project
- [ ] Get API keys
- [ ] Install dependencies
- [ ] Create auth module
- [ ] Update Gradio UI
- [ ] Create database tables
- [ ] Add Modal secrets
- [ ] Test authentication flow
- [ ] Test analysis with auth
- [ ] Deploy to Modal

**Time: 2-3 hours total** ⏱️

---

## 📚 **Next Steps (Optional Enhancements)**

### **Phase 2: Enhanced Features**
- User profiles
- Favorite tickers
- Email notifications
- Export reports

### **Phase 3: Teams (if needed)**
- Organization accounts
- Team sharing
- Role-based access

### **Phase 4: Monetization (if needed)**
- Stripe integration
- Usage tiers
- Subscription management

---

## 🆘 **Troubleshooting**

### **"Magic link not received"**
- Check spam folder
- Verify Supabase email settings
- Check Supabase logs

### **"Token verification failed"**
- Check token expiration (1 hour default)
- Verify redirect URL matches
- Extract token from URL query params (see callback handling below)

### **Handling OAuth Callback in Gradio**
Gradio doesn't natively handle URL query parameters. For the magic link callback:
```python
# Option 1: Use a separate FastAPI endpoint
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

fastapi_app = FastAPI()

@fastapi_app.get("/auth/callback")
async def auth_callback(request: Request):
    # Extract tokens from URL fragment or query params
    token = request.query_params.get("access_token")
    # Verify and create session
    # Redirect to Gradio app with session cookie
    return RedirectResponse(url="/?authenticated=true")

# Mount Gradio app
app = gr.mount_gradio_app(fastapi_app, gradio_app, path="/")
```

### **"Database permission denied"**
- Check Row Level Security policies
- Verify user is authenticated

---

## ✅ **Summary**

**Difficulty:** Easy (2-3 hours)  
**Cost:** Free (Supabase free tier)  
**Benefit:** Collect user emails, track usage, foundation for growth  

**This is definitely worth doing!** Even if you're not charging now, having user data from the start is valuable for:
- Understanding usage patterns
- Building features users want
- Easy to add payments later
- Professional experience

**Ready to implement?** Start with Step 1 (Supabase setup)!
