"""
Vercel serverless function entry point for FastAPI backend.

This file is used when deploying the API to Vercel as a serverless function.
For standalone deployment (Railway, Render, etc.), use api/main.py directly.
"""

from api.main import app

# Vercel expects a variable named 'app' or 'handler'
# FastAPI app is already defined in api/main.py
handler = app
