# Enabling WWW Statistics in MyDevil Panel

This guide explains how to enable visitor statistics tracking for your Flask application when hosted on MyDevil.net.

## Overview

MyDevil.net hosting provides built-in website statistics tracking. The tracking code needs to be embedded in your website's HTML pages. This Flask application supports automatic insertion of the MyDevil statistics tracking code.

## How It Works

The application uses an environment variable (`MYDEVIL_STATS_CODE`) to store the tracking code snippet provided by MyDevil.net. When set, this code is automatically inserted before the closing `</body>` tag on all pages.

## Setup Instructions

### Step 1: Enable Statistics in MyDevil Panel

1. Log in to your MyDevil.net control panel at https://panel.mydevil.net
2. Navigate to **WWW → Statistics** (or **WWW → Statystyki** in Polish)
3. Find your website domain in the list
4. Click on **Enable Statistics** or similar button
5. The panel should provide you with a tracking code snippet (typically JavaScript)

### Step 2: Copy the Tracking Code

The MyDevil panel will display a code snippet that looks similar to:

```html
<script type="text/javascript">
  /* MyDevil statistics tracking code */
  (function() {
    // tracking code here
  })();
</script>
```

**Important:** Copy the **complete** code snippet including the `<script>` tags.

### Step 3: Set the Environment Variable

#### Option A: Using .env file (Recommended)

1. Create or edit the `.env` file in your project root:
   ```bash
   nano .env
   ```

2. Add the following line with your tracking code:
   ```bash
   MYDEVIL_STATS_CODE='<script type="text/javascript">/* paste your code here */</script>'
   ```

3. Make sure to enclose the code in single quotes and escape any internal quotes if necessary

#### Option B: Using MyDevil Panel

1. In MyDevil panel, go to your Python application settings
2. Find the environment variables section
3. Add a new variable:
   - **Name:** `MYDEVIL_STATS_CODE`
   - **Value:** Paste the complete tracking code

#### Option C: Via SSH

1. SSH into your MyDevil account:
   ```bash
   ssh yourlogin@server.mydevil.net
   ```

2. Edit your .env file:
   ```bash
   cd ~/path/to/your/app
   nano .env
   ```

3. Add the MYDEVIL_STATS_CODE variable

### Step 4: Restart Your Application

After setting the environment variable, restart your Flask application:

```bash
# Via SSH
touch ~/domains/yourapp.YOURUSERNAME.mydevil.net/tmp/restart.txt

# Or via MyDevil panel
# Go to your app settings and click "Restart"
```

## Verification

To verify that the tracking code is working:

1. Visit your website in a browser
2. View the page source (Right-click → View Page Source)
3. Search for your tracking code near the end of the HTML, just before `</body>`
4. After some time, check the statistics in your MyDevil panel

## Troubleshooting

### Tracking code not appearing

- **Check environment variable is set:**
  ```bash
  echo $MYDEVIL_STATS_CODE
  ```
  
- **Verify application restarted:**
  ```bash
  touch tmp/restart.txt
  ```

- **Check Flask logs** for any errors related to template rendering

### Statistics not updating in panel

- **Wait 24-48 hours** - Statistics may take time to appear
- **Verify tracking code is correct** - Compare with MyDevil panel documentation
- **Check browser console** for JavaScript errors
- **Ensure cookies are enabled** in your browser when testing

### Escaping issues with quotes

If your tracking code contains both single and double quotes:

```bash
# Use backslashes to escape quotes
MYDEVIL_STATS_CODE='<script>var x = "value"; alert(\'test\');</script>'

# Or use heredoc in shell scripts
cat << 'EOF' >> .env
MYDEVIL_STATS_CODE='<script>/* your code */</script>'
EOF
```

## Disabling Statistics

To disable statistics tracking:

1. Remove or comment out the `MYDEVIL_STATS_CODE` variable from your `.env` file:
   ```bash
   #MYDEVIL_STATS_CODE='...'
   ```

2. Restart your application:
   ```bash
   touch tmp/restart.txt
   ```

## Security Notes

- The tracking code is inserted using Flask's `safe` filter, which allows HTML/JavaScript to be rendered
- Only set `MYDEVIL_STATS_CODE` from trusted sources (your MyDevil panel)
- Never commit `.env` files with sensitive data to version control
- The `.env.example` file is provided as a template - copy and customize it

## Alternative: Manual Integration

If you prefer not to use environment variables, you can manually add the tracking code to `templates/base.html`:

1. Open `templates/base.html`
2. Find the line just before `</body>`
3. Paste your tracking code directly:
   ```html
   <!-- MyDevil.net statistics -->
   <script type="text/javascript">
     /* your tracking code */
   </script>
   </body>
   </html>
   ```

However, using the environment variable method is recommended as it keeps configuration separate from code.

## Related Documentation

- [MyDevil.net Documentation](https://www.mydevil.net/docs/)
- [Flask Environment Variables](https://flask.palletsprojects.com/en/3.0.x/config/)
- [Deployment Guide](README_DEPLOYMENT.md)

## Support

For MyDevil-specific issues:
- MyDevil support: https://www.mydevil.net/pomoc
- MyDevil forum: https://forum.mydevil.net/

For application issues:
- Check [GitHub Issues](https://github.com/Marcin-Rybarczyk/flbb-statistics-public/issues)
