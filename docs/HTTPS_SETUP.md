# HTTPS Setup Guide for Flask Application

This guide provides comprehensive instructions for enabling HTTPS (SSL/TLS) on the FLBB Statistics Flask application across different hosting platforms, as well as workarounds for accessing HTTP-only pages during development.

> **⚡ Quick Reference:** For a condensed version with the most common commands and solutions, see **[HTTPS_QUICK_REFERENCE.md](HTTPS_QUICK_REFERENCE.md)**.

## 📋 Table of Contents

- [Overview](#overview)
- [Platform-Specific HTTPS Setup](#platform-specific-https-setup)
  - [MyDevil.net](#1-mydevilnet)
  - [Render.com](#2-rendercom)
  - [Railway.app](#3-railwayapp)
  - [GitHub Pages](#4-github-pages)
  - [Custom VPS/Server](#5-custom-vpsserver)
- [Local Development with HTTPS](#local-development-with-https)
- [Browser Workarounds for HTTP Pages](#browser-workarounds-for-http-pages)
- [Testing HTTPS Configuration](#testing-https-configuration)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)

## Overview

HTTPS (Hypertext Transfer Protocol Secure) is essential for:
- 🔒 **Encrypting data** in transit between users and your server
- ✅ **Preventing man-in-the-middle attacks**
- 🌐 **Improving SEO rankings** (Google favors HTTPS sites)
- 🎯 **Enabling modern web features** (geolocation, push notifications, etc.)
- 🛡️ **Building user trust** with the padlock icon in browsers

Modern web browsers increasingly require HTTPS, and many features are disabled on HTTP-only sites.

## Platform-Specific HTTPS Setup

### 1. MyDevil.net

MyDevil.net hosting provides **automatic free SSL certificates** via Let's Encrypt for all Python applications.

#### Automatic HTTPS (Recommended)

**By default, MyDevil.net automatically provisions SSL certificates for all websites.** No manual configuration needed!

1. **Deploy your Flask application** following the [deployment guide](README_DEPLOYMENT.md#4-mydevilnet)

2. **Access via HTTPS:**
   ```
   https://yourapp.YOURUSERNAME.mydevil.net
   ```

3. **Verify SSL certificate:**
   - Visit your site in a browser
   - Click the padlock icon in the address bar
   - Certificate should show: "Let's Encrypt Authority X3"

#### Custom Domain with HTTPS

If using a custom domain (e.g., `flbb.example.com`):

1. **Add domain in MyDevil panel:**
   ```bash
   devil www add flbb.example.com python3.11 ~/path/to/passenger_wsgi.py
   ```

2. **Configure DNS records:**
   - Point your domain's A record to MyDevil's IP
   - Or use CNAME record to point to your `.mydevil.net` subdomain

3. **Wait for SSL provisioning:**
   - SSL certificates are automatically generated within 5-15 minutes
   - Check panel: WWW → SSL Certificates

4. **Force HTTPS redirect** (optional):
   
   Create/edit `.htaccess` in your domain's root directory:
   ```apache
   # Force HTTPS
   RewriteEngine On
   RewriteCond %{HTTPS} off
   RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
   ```

#### Manual SSL Certificate Installation (Advanced)

For custom SSL certificates (e.g., purchased or corporate):

1. **Via MyDevil Panel:**
   - Go to: WWW → SSL Certificates
   - Click "Add certificate"
   - Paste your certificate, private key, and chain

2. **Via SSH:**
   ```bash
   devil ssl add example.com --cert /path/to/cert.crt --key /path/to/private.key
   ```

#### Troubleshooting MyDevil HTTPS

**Problem: Certificate not provisioning**
- Solution: Wait 15 minutes after domain creation
- Check DNS propagation: `nslookup yourdomain.com`
- Contact support if issues persist: https://www.mydevil.net/pomoc

**Problem: Mixed content warnings**
- Solution: Ensure all assets (images, CSS, JS) use HTTPS or relative URLs
- Check browser console for blocked resources

### 2. Render.com

Render.com provides **automatic free SSL certificates** for all web services.

#### Automatic HTTPS (Default)

1. **Deploy your Flask app** to Render.com following [deployment guide](README_DEPLOYMENT.md#1-rendercom)

2. **HTTPS is enabled by default:**
   - Render automatically provisions SSL certificates
   - Available at: `https://your-app-name.onrender.com`

3. **No configuration needed!** Render handles:
   - Certificate provisioning
   - Automatic renewal
   - HTTP to HTTPS redirect

#### Custom Domain with HTTPS

1. **Add custom domain in Render dashboard:**
   - Go to your service → Settings → Custom Domains
   - Click "Add Custom Domain"
   - Enter your domain (e.g., `flbb.example.com`)

2. **Configure DNS:**
   - Add CNAME record pointing to: `your-app.onrender.com`
   - Or use A record with IP provided by Render

3. **SSL certificate is automatic:**
   - Provisioned within minutes
   - Auto-renewed every 90 days
   - Fully managed by Render

#### Force HTTPS Redirect in Flask

Add to your `src/app.py` (optional, Render does this automatically):

```python
from flask import Flask, redirect, request
import os

app = Flask(__name__)

@app.before_request
def force_https():
    """Force HTTPS in production"""
    # Check if running in production and request is not secure
    if os.environ.get('FLASK_ENV') == 'production' and not request.is_secure:
        # Check X-Forwarded-Proto header (set by most reverse proxies)
        if request.headers.get('X-Forwarded-Proto', 'http') != 'https':
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)
```

### 3. Railway.app

Railway.app provides **automatic HTTPS** for all deployments.

#### Automatic HTTPS (Default)

1. **Deploy to Railway.app** following [deployment guide](README_DEPLOYMENT.md#2-railwayapp)

2. **Access via HTTPS:**
   ```
   https://your-app-name.up.railway.app
   ```

3. **Automatic features:**
   - Free SSL certificates
   - Auto-renewal
   - HTTP → HTTPS redirect

#### Custom Domain with HTTPS

1. **Add domain in Railway:**
   - Project Settings → Domains
   - Click "Add Domain"
   - Enter your custom domain

2. **Update DNS:**
   - Add CNAME record: `your-domain.com` → `your-app.up.railway.app`

3. **SSL provisioning:**
   - Automatic via Let's Encrypt
   - Takes 1-2 minutes
   - Check status in Railway dashboard

### 4. GitHub Pages

GitHub Pages provides **automatic HTTPS** for all sites.

#### Automatic HTTPS

1. **Deploy static site:**
   ```bash
   python3 deployment/deploy_flask.py github
   ```

2. **Enable HTTPS in repository settings:**
   - Go to: Settings → Pages
   - Check: "Enforce HTTPS"

3. **Access via HTTPS:**
   ```
   https://yourusername.github.io/flbb-statistics-public/
   ```

#### Custom Domain with HTTPS

1. **Add custom domain:**
   - Repository Settings → Pages → Custom domain
   - Enter: `flbb.example.com`

2. **Configure DNS:**
   ```
   A Record: flbb.example.com → 185.199.108.153
   A Record: flbb.example.com → 185.199.109.153
   A Record: flbb.example.com → 185.199.110.153
   A Record: flbb.example.com → 185.199.111.153
   ```

3. **SSL certificate:**
   - Automatically provisioned by GitHub
   - Takes up to 24 hours
   - Check "Enforce HTTPS" after provisioning

### 5. Custom VPS/Server

For custom servers (Ubuntu, Debian, CentOS), use **Let's Encrypt** with **Certbot**.

#### Using Certbot (Recommended)

**Prerequisites:**
- Domain name pointing to your server
- Flask app running on port 5000 (or configured port)
- Nginx or Apache as reverse proxy

**Installation (Ubuntu/Debian):**

```bash
# Install Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# For Apache instead of Nginx:
# sudo apt install certbot python3-certbot-apache
```

**Configure Nginx:**

1. **Create Nginx configuration:**
   ```bash
   sudo nano /etc/nginx/sites-available/flbb-stats
   ```

2. **Add configuration:**
   ```nginx
   server {
       listen 80;
       server_name flbb.example.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **Enable site:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/flbb-stats /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

**Obtain SSL Certificate:**

```bash
# Run Certbot
sudo certbot --nginx -d flbb.example.com

# Follow prompts:
# - Enter email address
# - Agree to Terms of Service
# - Choose whether to redirect HTTP to HTTPS (recommended: Yes)
```

**Auto-renewal:**

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically sets up cron job for renewal
# Verify: 
sudo systemctl status certbot.timer
```

**Manual Nginx HTTPS configuration (if not using Certbot auto-config):**

```nginx
server {
    listen 443 ssl http2;
    server_name flbb.example.com;

    ssl_certificate /etc/letsencrypt/live/flbb.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/flbb.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name flbb.example.com;
    return 301 https://$server_name$request_uri;
}
```

#### Using Gunicorn with SSL (Development Only)

⚠️ **Not recommended for production** - use Nginx/Apache + Let's Encrypt instead.

```bash
# Install with SSL support
pip install gunicorn[gevent]

# Generate self-signed certificate (for testing only)
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout key.pem -out cert.pem -days 365

# Run Gunicorn with SSL
gunicorn --certfile=cert.pem --keyfile=key.pem \
  --bind 0.0.0.0:443 wsgi:application
```

## Local Development with HTTPS

For testing HTTPS locally:

### Option 1: Self-Signed Certificate

1. **Generate certificate:**
   ```bash
   # Create certificates directory
   mkdir -p certs
   cd certs

   # Generate self-signed certificate
   openssl req -x509 -newkey rsa:4096 -nodes \
     -keyout localhost-key.pem \
     -out localhost-cert.pem \
     -days 365 \
     -subj "/CN=localhost"
   ```

2. **Run Flask with SSL:**
   ```python
   # In test_local_flask.py or app.py
   if __name__ == '__main__':
       app.run(
           debug=True,
           port=5000,
           ssl_context=('certs/localhost-cert.pem', 'certs/localhost-key.pem')
       )
   ```

3. **Access:**
   - Visit: `https://localhost:5000`
   - Browser will show security warning (expected with self-signed certs)
   - Click "Advanced" → "Proceed to localhost (unsafe)"

### Option 2: mkcert (Recommended for Local Development)

**mkcert** creates locally-trusted development certificates.

1. **Install mkcert:**
   ```bash
   # macOS
   brew install mkcert
   brew install nss # for Firefox

   # Linux (recommended: use package manager if available)
   # Option 1: From package manager (Debian/Ubuntu 23.04+)
   sudo apt install mkcert
   
   # Option 2: Manual installation with checksum verification
   sudo apt install libnss3-tools
   wget https://github.com/FiloSottile/mkcert/releases/download/v1.4.4/mkcert-v1.4.4-linux-amd64
   # Verify checksum (optional but recommended)
   # sha256sum mkcert-v1.4.4-linux-amd64
   # Compare with official release checksums at https://github.com/FiloSottile/mkcert/releases
   chmod +x mkcert-v1.4.4-linux-amd64
   sudo mv mkcert-v1.4.4-linux-amd64 /usr/local/bin/mkcert

   # Windows
   choco install mkcert
   ```

2. **Create local CA:**
   ```bash
   mkcert -install
   ```

3. **Generate certificate:**
   ```bash
   mkdir -p certs
   cd certs
   mkcert localhost 127.0.0.1 ::1
   ```

4. **Run Flask:**
   ```python
   app.run(
       debug=True,
       ssl_context=('certs/localhost+2.pem', 'certs/localhost+2-key.pem')
   )
   ```

5. **Access without warnings:**
   - Visit: `https://localhost:5000`
   - No security warnings! ✅

### Option 3: ngrok (Quick Testing)

**ngrok** creates a secure tunnel to your localhost with HTTPS.

1. **Install ngrok:**
   - Download from: https://ngrok.com/download
   - Sign up for free account

2. **Run your Flask app:**
   ```bash
   python3 tests/test_local_flask.py
   ```

3. **Start ngrok tunnel:**
   ```bash
   ngrok http 5000
   ```

4. **Access via HTTPS:**
   - ngrok provides HTTPS URL: `https://abc123.ngrok.io`
   - Shares your local app with real HTTPS certificate

## Browser Workarounds for HTTP Pages

Sometimes you need to access HTTP-only pages during development or when HTTPS is not yet configured. Here are browser-specific workarounds:

### Google Chrome

#### Method 1: Allow Insecure Content for Specific Site

1. **Visit the HTTP page** (you'll see a warning)
2. **Click the "Not Secure" icon** in the address bar
3. **Click "Site settings"**
4. **Find "Insecure content"** and change to **"Allow"**
5. **Reload the page**

#### Method 2: Chrome Flags (Allow All Insecure Content)

⚠️ **Use with caution** - reduces security.

1. **Open Chrome flags:**
   ```
   chrome://flags/#allow-insecure-localhost
   ```

2. **Enable:** "Allow invalid certificates for resources loaded from localhost"

3. **Relaunch Chrome**

#### Method 3: Command Line Flag

**macOS:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --ignore-certificate-errors \
  --unsafely-treat-insecure-origin-as-secure="http://flbb.ryba.usermd.net"
```

**Windows:**
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --ignore-certificate-errors ^
  --unsafely-treat-insecure-origin-as-secure="http://flbb.ryba.usermd.net"
```

**Linux:**
```bash
google-chrome \
  --ignore-certificate-errors \
  --unsafely-treat-insecure-origin-as-secure="http://flbb.ryba.usermd.net"
```

#### Method 4: Type "thisisunsafe" (Emergency Bypass)

1. **When you see the warning page**, click anywhere on the page
2. **Type (don't paste):** `thisisunsafe`
3. **Page will load** (this is an undocumented Chrome feature)

### Mozilla Firefox

#### Method 1: Add Security Exception

1. **Visit the HTTP page**
2. **Click "Advanced"** on the warning page
3. **Click "Accept the Risk and Continue"**
4. **Certificate exception added** for this site

#### Method 2: Firefox Config (Disable Mixed Content Blocking)

⚠️ **Use with caution** - reduces security.

1. **Open Firefox config:**
   ```
   about:config
   ```

2. **Accept the risk** (click "Accept the Risk and Continue")

3. **Search for:** `security.mixed_content.block_active_content`

4. **Toggle to:** `false`

5. **Reload the page**

#### Method 3: Command Line Flag

**macOS:**
```bash
/Applications/Firefox.app/Contents/MacOS/firefox \
  -new-instance -profile $(mktemp -d)
```

**Windows:**
```cmd
"C:\Program Files\Mozilla Firefox\firefox.exe" -new-instance
```

**Linux:**
```bash
firefox -new-instance -profile $(mktemp -d)
```

### Microsoft Edge

#### Method 1: Allow Insecure Content

1. **Visit the HTTP page**
2. **Click the lock icon** with warning
3. **Click "Site permissions"**
4. **Find "Insecure content"** and set to **"Allow"**
5. **Reload the page**

#### Method 2: Edge Flags

1. **Open Edge flags:**
   ```
   edge://flags/#allow-insecure-localhost
   ```

2. **Enable:** "Allow invalid certificates for resources loaded from localhost"

3. **Relaunch Edge**

### Safari

#### Method 1: Show Certificate and Continue

1. **Visit the HTTP page**
2. **Click "Show Details"** on the warning
3. **Click "visit this website"**
4. **Enter macOS password** if prompted

#### Method 2: Disable Certificate Warnings (Not Recommended)

Safari doesn't have a built-in option to disable certificate warnings. Use other browsers for development/testing instead.

### Important Security Notes for HTTP Workarounds

⚠️ **Warning:** These workarounds reduce your browser's security:

- **Only use for development/testing** on trusted networks
- **Never use on public Wi-Fi** or untrusted networks
- **Don't enter sensitive information** (passwords, credit cards) on HTTP pages
- **Re-enable security settings** after testing
- **Better solution:** Set up proper HTTPS instead of using workarounds

## Testing HTTPS Configuration

### 1. SSL Labs Test (Comprehensive)

Test your HTTPS configuration quality:

1. Visit: https://www.ssllabs.com/ssltest/
2. Enter your domain: `flbb.example.com`
3. Click "Submit"
4. Wait for analysis (2-3 minutes)
5. Review grade (A+ is best)

### 2. Command Line Tests

**Check certificate:**
```bash
# OpenSSL
openssl s_client -connect flbb.example.com:443 -servername flbb.example.com

# Or use curl
curl -vI https://flbb.example.com
```

**Check HTTPS redirect:**
```bash
curl -I http://flbb.example.com
# Should return: HTTP/1.1 301 Moved Permanently
# Location: https://flbb.example.com/
```

### 3. Browser Developer Tools

1. **Open browser DevTools** (F12)
2. **Go to Security tab**
3. **Visit your HTTPS site**
4. **Check:**
   - Certificate validity
   - Protocol version (TLS 1.2 or 1.3)
   - Cipher strength
   - Mixed content warnings

### 4. Python Test Script

Create `test_https.py`:

```python
import requests
import ssl
from urllib3 import PoolManager

def test_https(url):
    """Test HTTPS configuration"""
    print(f"Testing: {url}")
    
    try:
        # Test HTTP redirect
        http_response = requests.get(url.replace('https://', 'http://'), allow_redirects=False)
        print(f"HTTP Response: {http_response.status_code}")
        if http_response.status_code in [301, 302]:
            print(f"✅ HTTP redirects to HTTPS")
        
        # Test HTTPS connection
        https_response = requests.get(url, timeout=10)
        print(f"HTTPS Response: {https_response.status_code}")
        
        # Check certificate
        if https_response.url.startswith('https://'):
            print(f"✅ HTTPS connection successful")
            # Note: TLS version checking requires deeper socket access
            # Use OpenSSL command line for detailed TLS info:
            # openssl s_client -connect domain:443 -servername domain
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_https("https://flbb.ryba.usermd.net")
```

Run:
```bash
python3 test_https.py
```

## Troubleshooting

### Common HTTPS Issues

#### Issue: "NET::ERR_CERT_AUTHORITY_INVALID"

**Cause:** Certificate not trusted by browser

**Solutions:**
- **Production:** Wait for Let's Encrypt certificate to provision (5-15 minutes)
- **Local dev:** Install root CA certificate from mkcert
- **Self-signed:** Add exception in browser (see workarounds above)

#### Issue: "Mixed Content" Warning

**Cause:** HTTPS page loading HTTP resources (images, CSS, JS)

**Solutions:**
1. **Check browser console** for blocked resources
2. **Update resources to HTTPS:**
   ```html
   <!-- Bad -->
   <img src="http://example.com/logo.png">
   
   <!-- Good -->
   <img src="https://example.com/logo.png">
   
   <!-- Best (protocol-relative) -->
   <img src="//example.com/logo.png">
   ```
3. **Use relative URLs:**
   ```html
   <img src="/logos/team.png">
   ```

#### Issue: Certificate Expired

**Cause:** SSL certificate renewal failed

**Solutions:**
- **Auto-managed platforms** (Render, Railway, MyDevil): Contact support
- **Let's Encrypt:** Check Certbot timer: `sudo systemctl status certbot.timer`
- **Manual renewal:** `sudo certbot renew`

#### Issue: "Your connection is not private"

**Cause:** Invalid or expired certificate

**Solutions:**
1. **Check certificate expiry:**
   ```bash
   echo | openssl s_client -servername flbb.example.com -connect flbb.example.com:443 2>/dev/null | openssl x509 -noout -dates
   ```
2. **Renew certificate** if expired
3. **Check DNS propagation** if recently deployed
4. **Clear browser cache** and retry

#### Issue: HTTPS Redirect Loop

**Cause:** Misconfigured proxy or redirect rules

**Solutions:**
1. **Check Flask app** - ensure it respects `X-Forwarded-Proto` header
2. **Check reverse proxy** (Nginx/Apache) configuration
3. **Disable force HTTPS** temporarily to diagnose
4. **Check CloudFlare** settings if using CDN

#### Issue: Port 443 Already in Use

**Cause:** Another service using HTTPS port

**Solutions:**
```bash
# Find process using port 443
sudo lsof -i :443

# Stop conflicting service
sudo systemctl stop apache2  # or nginx, or other service

# Or change Flask app port
gunicorn --bind 0.0.0.0:8443 wsgi:application
```

### Platform-Specific Issues

#### MyDevil.net

**Issue:** SSL certificate not provisioning
- **Wait:** 15 minutes after domain creation
- **Check:** DNS propagation with `nslookup yourdomain.com`
- **Contact:** MyDevil support via https://www.mydevil.net/pomoc

**Issue:** "Passenger Error" after enabling HTTPS
- **Check:** passenger_wsgi.py file permissions
- **Fix:** `chmod 644 passenger_wsgi.py`
- **Restart:** `touch tmp/restart.txt`

#### Render.com

**Issue:** Custom domain not getting certificate
- **Verify:** DNS records are correct (CNAME or A record)
- **Wait:** Up to 1 hour for DNS propagation
- **Check:** Render dashboard for certificate status

## Security Best Practices

### 1. Always Use HTTPS in Production

```python
# Force HTTPS in Flask app
from flask import Flask, redirect, request
import os

@app.before_request
def force_https():
    if not request.is_secure and os.environ.get('FLASK_ENV') == 'production':
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)
```

### 2. Use Strong SSL Configuration

**Nginx example:**
```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

### 3. Enable HSTS (HTTP Strict Transport Security)

```python
# In Flask app
@app.after_request
def set_security_headers(response):
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

**Or in Nginx:**
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### 4. Use Content Security Policy

```python
@app.after_request
def set_csp(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline'"
    return response
```

### 5. Regular Certificate Monitoring

- **Set up monitoring** for certificate expiry
- **Enable auto-renewal** (Let's Encrypt/Certbot)
- **Test renewal** regularly: `sudo certbot renew --dry-run`

### 6. Update Documentation

Update URLs in documentation to use HTTPS:

```bash
# Find and replace HTTP URLs
grep -r "http://flbb.ryba.usermd.net" .
# Replace with: https://flbb.ryba.usermd.net
```

## Additional Resources

### Documentation
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot User Guide](https://eff-certbot.readthedocs.io/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)

### Tools
- [SSL Labs SSL Test](https://www.ssllabs.com/ssltest/)
- [SSL Checker](https://www.sslshopper.com/ssl-checker.html)
- [Certificate Transparency Search](https://crt.sh/)
- [mkcert (Local Development)](https://github.com/FiloSottile/mkcert)

### Support
- **MyDevil.net:** https://www.mydevil.net/pomoc
- **Render.com:** https://render.com/docs
- **Railway.app:** https://docs.railway.app
- **GitHub Issues:** https://github.com/Marcin-Rybarczyk/flbb-statistics-public/issues

---

## Summary

### Quick Reference

**Production HTTPS Setup:**
- ✅ **MyDevil.net:** Automatic (free Let's Encrypt)
- ✅ **Render.com:** Automatic (free)
- ✅ **Railway.app:** Automatic (free)
- ✅ **GitHub Pages:** Enable in settings
- 🔧 **Custom VPS:** Use Certbot with Nginx/Apache

**Local Development:**
- 🔧 **mkcert:** Best for local HTTPS
- 🔧 **ngrok:** Quick HTTPS tunnel
- ⚠️ **Self-signed:** Works but shows warnings

**HTTP Workarounds:**
- 🌐 **Chrome:** Site settings → Allow insecure content
- 🦊 **Firefox:** Accept risk and continue
- 🔷 **Edge:** Site permissions → Allow insecure content
- 🧭 **Safari:** Show details → Visit website

**Remember:**
- Always use HTTPS in production
- HTTP workarounds only for development
- Test HTTPS configuration regularly
- Monitor certificate expiration

---

**Need help?** Check the [Deployment Guide](README_DEPLOYMENT.md) or create an issue on [GitHub](https://github.com/Marcin-Rybarczyk/flbb-statistics-public/issues).
