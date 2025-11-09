# Telegram Bot Setup Guide for Family Assistant

This guide will walk you through setting up a Telegram bot to use with your Family Assistant multimodal platform.

## 🎯 Overview

The Family Assistant Telegram integration supports:
- **Text messages** - Standard chat interactions
- **Photos** - AI vision analysis and descriptions
- **Voice messages** - Speech transcription and processing
- **Documents** - Text extraction and analysis
- **Family member authentication** - Role-based access control
- **Privacy controls** - Content sharing based on family roles

## 📋 Prerequisites

- Family Assistant deployed and running
- Admin access to your homelab Kubernetes cluster
- Telegram account (for bot creation)
- Homelab external access (or Tailscale)

---

## 🤖 Step 1: Create Your Telegram Bot

### 1.1. Contact BotFather
1. Open Telegram and search for **@BotFather**
2. Start a chat with BotFather (it has a blue verified checkmark)

### 1.2. Create New Bot
1. Send the command: `/newbot`
2. BotFather will ask for a bot name (e.g., "Family Assistant")
3. BotFather will ask for a username (must end in `bot`, e.g., `family_assistant_bot`)

### 1.3. Get Your Bot Token
BotFather will provide you with a token like:
```
8583815346:AAFyvoLl0BE2iqaAUu81itFnmj3zuhRGWeQ
```
⚠️ **Keep this token secure!** Anyone with the token can control your bot.

### 1.4. Configure Bot Settings (Optional)
- `/setdescription` - Add a description for your bot
- `/setabouttext` - Set the "about" text
- `/setuserpic` - Set a profile picture
- `/setcommands` - Configure bot commands menu

---

## 🔧 Step 2: Configure Family Assistant

### 2.1. Add Bot Configuration to Environment

Create or update your Family Assistant configuration with the Telegram settings:

```yaml
# family-assistant-secret (Kubernetes Secret)
apiVersion: v1
kind: Secret
metadata:
  name: family-assistant-secret
  namespace: homelab
type: Opaque
stringData:
  # Add Telegram configuration
  TELEGRAM_BOT_TOKEN: "YOUR_BOT_TOKEN_HERE"
  TELEGRAM_WEBHOOK_SECRET: "your_webhook_secret_here"
  SECRET_KEY: "your_existing_secret_key"
  ENCRYPTION_KEY: "your_existing_encryption_key"
  POSTGRES_PASSWORD: "your_postgres_password"
```

### 2.2. Update ConfigMap

```yaml
# family-assistant-config (Kubernetes ConfigMap)
apiVersion: v1
kind: ConfigMap
metadata:
  name: family-assistant-config
  namespace: homelab
data:
  # Add Telegram settings
  TELEGRAM_BOT_ENABLED: "true"
  TELEGRAM_WEBHOOK_URL: "https://your-domain.com/telegram/webhook"
  TELEGRAM_MAX_FILE_SIZE_MB: "50"
  TELEGRAM_RATE_LIMIT_PER_MINUTE: "30"
  TELEGRAM_SUPPORTED_FORMATS: "jpg,png,gif,pdf,docx,txt,wav,ogg,m4a,mp3"

  # Existing configuration...
  API_HOST: "0.0.0.0"
  API_PORT: "8001"
  # ... other settings
```

### 2.3. Apply Configuration

```bash
kubectl apply -f family-assistant-secret.yaml -n homelab
kubectl apply -f family-assistant-config.yaml -n homelab
```

### 2.4. Restart Family Assistant

```bash
kubectl rollout restart deployment/family-assistant -n homelab
```

---

## 🌐 Step 3: Set Up Webhook (Production)

### 3.1. Option A: External Domain (Recommended)

If you have a domain pointing to your homelab:

```bash
# Set webhook using curl
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://your-domain.com/telegram/webhook",
       "secret_token": "your_webhook_secret_here",
       "max_connections": 40,
       "allowed_updates": ["message", "callback_query"]
     }'
```

### 3.2. Option B: Tailscale (Private Network)

If using Tailscale for private access:

1. **Set up a Tailscale HTTPS certificate:**
   ```bash
   # Install tailscale on your server if not already done
   sudo tailscale up

   # Enable HTTPS (requires premium Tailscale)
   sudo tailscale set --https=443
   ```

2. **Configure webhook with Tailscale URL:**
   ```bash
   curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
        -H "Content-Type: application/json" \
        -d '{
          "url": "https://your-tailscale-name.ts.net/telegram/webhook",
          "secret_token": "your_webhook_secret_here"
        }'
   ```

### 3.3. Option C: Ngrok (Development/Testing)

For quick testing without public domain:

```bash
# Install ngrok if not available
# On Ubuntu/Debian:
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Start ngrok tunnel to your Family Assistant
ngrok http 100.81.76.55:30801

# Use the ngrok URL (https://random-string.ngrok.io) for webhook
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://your-ngrok-url.ngrok.io/telegram/webhook"
     }'
```

---

## 👪 Step 4: Add Family Members

### 4.1. Get Family Member Telegram IDs

1. Each family member needs to send a message to your bot first
2. Check the logs to see their Telegram user IDs:

```bash
kubectl logs -n homelab deployment/family-assistant | grep "New user"
```

Or use a temporary bot to get user IDs:
```python
import telegram

# Create a simple bot that echoes user info
async def echo_user_info(update, context):
    user = update.effective_user
    await update.message.reply_text(
        f"Your info:\n"
        f"User ID: {user.id}\n"
        f"Username: @{user.username}\n"
        f"Name: {user.first_name} {user.last_name or ''}"
    )
```

### 4.2. Register Family Members in Database

Run the database migration to add family members:

```bash
# Connect to your PostgreSQL database
kubectl exec -it postgres-0 -n homelab -- psql -U homelab -d homelab

# Insert family members
INSERT INTO family_members (
    user_id, telegram_id, username, name, role, age,
    preferred_content_types, content_filters, language_preferences,
    vision_analysis_enabled, photo_privacy_level, auto_image_description,
    speech_recognition_enabled, preferred_audio_format, voice_privacy_level,
    document_extraction_enabled, auto_summarization,
    permissions, preferences, is_active
) VALUES
-- Parent 1
(
    'parent_01', 123456789, 'parent_username', 'Dad', 'parent', 40,
    ARRAY['text', 'image', 'audio', 'document'],
    ARRAY['violence', 'adult_content'],
    ARRAY['en'],
    true, 'family', true,
    true, 'ogg', 'family',
    true, false,
    '{"upload": true, "chat": true, "delete": true, "admin": true}',
    '{"theme": "light", "notifications": true}',
    true
),
-- Parent 2
(
    'parent_02', 987654321, 'mom_username', 'Mom', 'parent', 38,
    ARRAY['text', 'image', 'audio', 'document'],
    ARRAY['violence', 'adult_content'],
    ARRAY['en'],
    true, 'family', true,
    true, 'ogg', 'family',
    true, false,
    '{"upload": true, "chat": true, "delete": true, "admin": true}',
    '{"theme": "dark", "notifications": true}',
    true
),
-- Teenager
(
    'teen_01', 555666777, 'teen_username', 'Sarah', 'teenager', 16,
    ARRAY['text', 'image', 'audio'],
    ARRAY['adult_content'],
    ARRAY['en'],
    true, 'family', true,
    true, 'ogg', 'family',
    true, false,
    '{"upload": true, "chat": true, "delete": false, "admin": false}',
    '{"theme": "light", "notifications": false}',
    true
),
-- Child
(
    'child_01', 111222333, 'child_username', 'Timmy', 'child', 10,
    ARRAY['text', 'image'],
    ARRAY['violence', 'scary_content', 'adult_content'],
    ARRAY['en'],
    true, 'family', false,
    false, 'private', false,
    false, 'ogg', 'private',
    false, false,
    '{"upload": false, "chat": true, "delete": false, "admin": false}',
    '{"theme": "light", "notifications": false}',
    true
);
```

Replace the `telegram_id` values with the actual Telegram user IDs from your family members.

---

## 🎮 Step 5: Test Your Bot

### 5.1. Basic Functionality Test

1. **Start a chat** with your bot using its username
2. **Send a text message** - should get a response
3. **Send a photo** - should analyze and describe it
4. **Send a voice message** - should transcribe it
5. **Send a document** - should extract text

### 5.2. Family Authentication Test

- Verify each family member can use the bot
- Check that role-based permissions work
- Test content sharing between family members

### 5.3. Privacy Controls Test

- Send sensitive content as a parent
- Verify children can't access restricted content
- Test family vs private content sharing

---

## 📱 Step 6: Configure Bot Commands

Add helpful commands to your bot menu by sending to BotFather:

```
/setcommands
```

Then paste this list:

```
start - Start using the Family Assistant
help - Show available commands
upload - Upload and analyze content
family - See family members and status
privacy - Check your privacy settings
settings - Update your preferences
status - Check bot status and capabilities
```

---

## 🔍 Step 7: Monitoring and Troubleshooting

### 7.1. Check Bot Status

```bash
# Check webhook status
curl -X GET "https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo"

# Check Family Assistant logs
kubectl logs -n homelab deployment/family-assistant --tail=50 | grep -i telegram

# Check pod status
kubectl get pods -n homelab -l app=family-assistant
```

### 7.2. Common Issues

#### Bot Not Responding
- Check if the webhook is set correctly
- Verify your Family Assistant is running
- Check network connectivity

#### Authentication Issues
- Verify Telegram IDs are correct in database
- Check family member roles and permissions
- Ensure bot token is valid

#### File Upload Issues
- Check file size limits (default 50MB)
- Verify supported formats
- Check storage permissions

#### Privacy/Access Issues
- Review family member roles
- Check content filtering settings
- Verify privacy levels

### 7.3. Debug Mode

Enable debug logging for troubleshooting:

```yaml
# Update ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: family-assistant-config
  namespace: homelab
data:
  LOG_LEVEL: "debug"
  TELEGRAM_DEBUG: "true"
```

---

## 🚀 Advanced Features

### 1. Family Group Support

Create a family group chat and add the bot:

1. Create a Telegram group chat
2. Add your bot as an administrator
3. Configure group-specific privacy settings

### 2. Scheduled Reminders

Set up automated family reminders:

```python
# Example: Daily family check-in
@schedule(interval=datetime.timedelta(hours=24))
async def daily_family_checkin():
    for member in get_active_family_members():
        if member.preferences.get('daily_checkin', True):
            await bot.send_message(
                chat_id=member.telegram_id,
                text="Good morning! How is everyone doing today? 🌅"
            )
```

### 3. Content Sharing

Enable automatic family content sharing:

```python
# Configure auto-sharing for parents
parent_settings = {
    "auto_share_with_family": True,
    "share_types": ["photos", "documents"],
    "require_approval": False
}
```

### 4. Integration with N8n Workflows

Connect Telegram events to N8n workflows:

1. Use Telegram webhooks in N8n
2. Trigger family workflows from messages
3. Send notifications back through Telegram

---

## 🔒 Security Best Practices

### 1. Bot Token Security
- Never share your bot token publicly
- Use Kubernetes secrets for storage
- Rotate tokens periodically

### 2. Webhook Security
- Use secret tokens for webhook verification
- Validate incoming requests
- Monitor for suspicious activity

### 3. Family Data Protection
- Configure appropriate privacy levels
- Regular security audits
- Data retention policies

### 4. Access Control
- Implement role-based permissions
- Regular access reviews
- Secure admin controls

---

## 📞 Support and Help

If you encounter issues:

1. **Check logs**: `kubectl logs -n homelab deployment/family-assistant`
2. **Verify configuration**: Ensure all environment variables are set
3. **Test connectivity**: Check webhook URL accessibility
4. **Review family setup**: Verify member authentication

For additional help, refer to the Family Assistant documentation or create an issue in the GitHub repository.

---

## 🎉 You're All Set!

Your Family Assistant Telegram bot is now configured and ready to use! Family members can:

- Chat with the AI assistant
- Share photos for analysis
- Send voice messages for transcription
- Upload documents for processing
- Enjoy family-appropriate content filtering
- Maintain privacy with role-based access

Enjoy your enhanced family communication and AI assistance! 🏠✨