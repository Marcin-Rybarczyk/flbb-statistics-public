#!/usr/bin/env python3
"""
Production Flask Application Entry Point - Root Level

This file is required to be in the root directory for deployment platforms
like Render, Railway, Heroku, etc. It imports the actual application from
the src directory.
"""

from src.wsgi import application

# Make the application available at module level for deployment platforms
app = application

if __name__ == "__main__":
    application.run()