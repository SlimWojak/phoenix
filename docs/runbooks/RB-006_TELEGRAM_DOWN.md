# RB-006: Telegram Down

**Severity:** WARNING (degrades to CRITICAL if prolonged)  
**Alert Source:** Notification daemon, Heartbeat  
**Time to Resolve Target:** < 30 minutes

---

## Symptoms

- Alerts not reaching phone/device
- Alert queue growing
- Notification daemon logs show send failures
- Heartbeat shows notification issues

---

## Immediate Actions

1. **CHECK TELEGRAM BOT STATUS**
   ```bash
   # Try sending test message
   ./phoenix telegram test
   ```

2. **CHECK ALERT QUEUE**
   ```bash
   ./phoenix alerts queue
   # Shows: pending alerts, oldest timestamp
   ```

3. **CHECK LOGS**
   ```bash
   tail -50 logs/notification.log | grep -i "telegram\|error"
   ```

---

## Investigation Steps

### Step 1: Identify Failure Type

| Symptom | Likely Cause |
|---------|--------------|
| "Connection timeout" | Network issue |
| "401 Unauthorized" | Invalid bot token |
| "400 Bad Request" | Invalid chat ID |
| "429 Too Many Requests" | Rate limited |

### Step 2: Check Configuration

```bash
# Verify environment variables
grep TELEGRAM .env
# Should show:
# TELEGRAM_BOT_TOKEN=<your token>
# TELEGRAM_CHAT_ID=<your chat id>
```

### Step 3: Check Telegram API Status

- Visit: https://downdetector.com/status/telegram/
- Or: https://status.telegram.org/

### Step 4: Test Bot Directly

```bash
# Manual curl test
curl -X POST \
  "https://api.telegram.org/bot<YOUR_TOKEN>/sendMessage" \
  -d "chat_id=<YOUR_CHAT_ID>&text=Test from Phoenix"
```

---

## Resolution

### Option A: Network Issue

1. **Check Internet Connectivity**
   ```bash
   ping api.telegram.org
   curl -I https://api.telegram.org
   ```

2. **Check DNS**
   ```bash
   nslookup api.telegram.org
   ```

3. **Wait and Retry**
   - Telegram API usually recovers quickly

### Option B: Invalid Credentials

1. **Regenerate Bot Token**
   - Message @BotFather on Telegram
   - `/revoke` old token
   - `/token` to get new one

2. **Update .env**
   ```bash
   # Edit .env
   TELEGRAM_BOT_TOKEN=<new_token>
   ```

3. **Restart Notification Daemon**
   ```bash
   ./phoenix restart --component=notification
   ```

### Option C: Rate Limited

1. **Check Rate Limit**
   - Telegram limit: 30 messages/second per bot
   - Group limit: 20 messages/minute

2. **Wait for Reset**
   - Usually clears in 60 seconds

3. **Increase Throttle**
   - Adjust `TELEGRAM_THROTTLE_SEC` in config

### Option D: Telegram Service Down

1. **Wait for Recovery**
   - Monitor status page

2. **Alerts Queue**
   - Phoenix queues alerts
   - Will send when service recovers

---

## Post-Incident

1. **Drain Alert Queue**
   ```bash
   ./phoenix alerts flush
   ```

2. **Check for Missed Critical Alerts**
   ```bash
   ./phoenix alerts history --level=CRITICAL --since="1 hour ago"
   ```

3. **Document Outage**
   - Duration
   - Root cause
   - Missed alerts

---

## Prevention

- Monitor Telegram health in heartbeat
- Set up backup notification channel (email?)
- Review throttle settings periodically

---

**Last Updated:** S33 (2026-01-27)  
**Owner:** Phoenix Ops
