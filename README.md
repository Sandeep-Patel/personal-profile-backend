---
title: Personal Profile Backend
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# Personal Profile Backend

A FastAPI-based backend service that provides an AI-powered chat interface representing Sandeep Patel's professional profile.

## Features

- AI-powered chat using Google Gemini 2.0 Flash
- Professional profile information from LinkedIn PDF and summary
- Push notifications via Pushover
- Contact form handling with email collection
- Health check endpoint for monitoring

## Environment Variables

### Required
- `GOOGLE_API_KEY`: Your Google AI API key for Gemini access

### Optional
- `PUSHOVER_TOKEN`: Pushover app token for notifications
- `PUSHOVER_USER`: Pushover user key for notifications

## Setup

1. Copy the environment template:
   ```bash
   cp .env.template .env
   ```

2. Fill in your API keys in the `.env` file

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   uvicorn app:app --reload
   ```

## Hugging Face Deployment

This app is configured to run on Hugging Face Spaces using Docker.

### Setting Environment Variables on Hugging Face

1. Go to your Hugging Face Space settings
2. Navigate to "Variables and secrets"
3. Add the following secrets:
   - `GOOGLE_API_KEY`: Your Google AI API key

### Deployment Files

- `Dockerfile`: Configures the Docker container for Hugging Face Spaces
- `README.md`: Contains Hugging Face Space metadata in YAML frontmatter
- `.huggingface.yml`: Alternative configuration file (deprecated, using README frontmatter instead)

### Troubleshooting

If your app is failing on Hugging Face:

1. Check the health endpoint: `https://your-space.hf.space/health`
2. Verify environment variables are set correctly
3. Check the application logs in your Hugging Face Space
4. Ensure Docker builds successfully (check build logs)

## API Endpoints

- `GET /hi` - Simple greeting endpoint
- `GET /health` - Health check with configuration status
- `POST /ask` - Main chat interface
  ```json
  {
    "message": "Your question here",
    "history": []
  }
  ```

## Common Issues

1. **"SDK location not found"** - This error appears to be from a different Android project, not this FastAPI app
2. **No logs on Hugging Face** - Usually indicates the app is failing during startup due to missing environment variables
3. **Runtime errors** - Check the `/health` endpoint to see configuration status

## Files Structure

- `app.py` - Main FastAPI application
- `me/linkedin.pdf` - LinkedIn profile data
- `me/summary.txt` - Personal summary
- `requirements.txt` - Python dependencies
- `.huggingface.yml` - Hugging Face configuration
