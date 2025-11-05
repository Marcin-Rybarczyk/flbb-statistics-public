# HTTPS Quick Reference Guide

Quick reference for enabling HTTPS and accessing HTTP-only pages.

> **📖 Complete Guide:** See [HTTPS_SETUP.md](HTTPS_SETUP.md) for comprehensive documentation.

## ✅ Enable HTTPS (Production)

### Platform-Specific Setup

| Platform | HTTPS Setup | Custom Domain |
|----------|-------------|---------------|
| **MyDevil.net** | ✅ Automatic (Let's Encrypt) | Automatic SSL for custom domains |
| **Render.com** | ✅ Automatic (Free) | Add domain in dashboard → SSL auto-provisioned |
| **Railway.app** | ✅ Automatic (Free) | Add domain in settings → SSL auto-provisioned |
| **GitHub Pages** | ✅ Automatic | Enable "Enforce HTTPS" in settings |
| **Custom VPS** | 🔧 Use Certbot | `sudo certbot --nginx -d yourdomain.com` |

**Quick Command for Custom VPS:**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com
```

## 🔓 Access HTTP-Only Pages (Development/Testing)

### Browser Workarounds

#### Chrome
1. **Click** the "Not Secure" icon in address bar
2. **Select** "Site settings"
3. **Change** "Insecure content" to **"Allow"**
4. **Reload** the page

**Or type:** `thisisunsafe` on the warning page (undocumented feature)

#### Firefox
1. **Click** "Advanced" on warning page
2. **Click** "Accept the Risk and Continue"

#### Edge
1. **Click** the lock icon with warning
2. **Select** "Site permissions"
3. **Set** "Insecure content" to **"Allow"**

#### Safari
1. **Click** "Show Details" on warning
2. **Click** "visit this website"

### Command Line Access (Chrome)

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

## 🔐 Local Development with HTTPS

### Option 1: mkcert (Recommended)

```bash
# Install mkcert
brew install mkcert  # macOS
# or download from: https://github.com/FiloSottile/mkcert

# Create local CA
mkcert -install

# Generate certificate
mkdir -p certs
cd certs
mkcert localhost 127.0.0.1 ::1

# Run Flask with SSL
# In your Python code:
# app.run(ssl_context=('certs/localhost+2.pem', 'certs/localhost+2-key.pem'))
```

### Option 2: ngrok (Quick Testing)

```bash
# Start your Flask app
python3 tests/test_local_flask.py

# In another terminal, start ngrok
ngrok http 5000

# Access via provided HTTPS URL: https://abc123.ngrok.io
```

## ⚠️ Security Warning

**Important:** HTTP workarounds reduce browser security:

- ✅ **Only use for development/testing** on trusted networks
- ❌ **Never use on public Wi-Fi**
- ❌ **Don't enter sensitive data** on HTTP pages
- ✅ **Re-enable security settings** after testing
- ✅ **Always use HTTPS in production**

## 📚 Additional Resources

- **[Complete HTTPS Setup Guide](HTTPS_SETUP.md)** - Comprehensive documentation
- **[Deployment Guide](README_DEPLOYMENT.md)** - Platform deployment instructions
- **SSL Testing:** https://www.ssllabs.com/ssltest/
- **Let's Encrypt:** https://letsencrypt.org/

## 🆘 Common Issues

| Issue | Solution |
|-------|----------|
| Certificate not provisioning | Wait 15 minutes, check DNS propagation |
| Mixed content warnings | Update resources to use HTTPS or relative URLs |
| Certificate expired | Renew with `sudo certbot renew` |
| Port 443 in use | Stop conflicting service: `sudo lsof -i :443` |

## 📞 Support

- **GitHub Issues:** [Create an issue](https://github.com/Marcin-Rybarczyk/flbb-statistics-public/issues)
- **MyDevil Support:** https://www.mydevil.net/pomoc
- **Render Support:** https://render.com/docs
- **Railway Support:** https://docs.railway.app

---

**Remember:** Always prefer HTTPS in production. HTTP workarounds are for development only!
