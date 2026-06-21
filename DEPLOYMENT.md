# YTMusicAPI Cloud

This repo contains the original `ytmusicapi` package plus a deployable FastAPI HTTP wrapper.

## Local Run

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Open:

- Home page: http://127.0.0.1:8000
- OpenAPI docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## API Examples

```bash
curl "http://127.0.0.1:8000/api/search?q=Oasis%20Wonderwall&limit=5"
curl "http://127.0.0.1:8000/api/charts?country=US"
curl "http://127.0.0.1:8000/api/song/ZrOKjDZOtkA"
```

The API is read-only and unauthenticated. Private library, upload, and playlist mutation features from
`ytmusicapi` still require a user's YouTube Music authentication and are intentionally not exposed here.

## Render Deploy

The included `render.yaml` creates one free Python web service.

1. Push this repo to GitHub.
2. Open Render's Blueprint flow:
   `https://dashboard.render.com/blueprint/new?repo=<YOUR_GITHUB_REPO_URL>`
3. Apply the Blueprint.
4. Add a custom domain in the Render service settings after the first successful deploy.

