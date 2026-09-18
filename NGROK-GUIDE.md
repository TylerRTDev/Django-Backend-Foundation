# Using Ngrok with Django Backend App

This guide explains how to expose your Django app running in Docker to the internet via ngrok.

## Prerequisites

1. An ngrok account (sign up at [ngrok.com](https://ngrok.com))
2. Your ngrok authtoken (available from ngrok dashboard)

## Setup

### 1. Configure Environment

Edit the `.env` file in the project root and set:

```
NGROK_AUTHTOKEN=your_actual_authtoken_here
USE_NGROK=True   # Optional, enables static file serving via Django (whitenoise)
```

Also ensure `ALLOWED_HOSTS` already includes `.ngrok-free.dev` (already added).

### 2. Start with Ngrok

Run the provided script:

```bash
./start-ngrok.sh
```

This script will:
- Check for NGROK_AUTHTOKEN
- Set USE_NGROK=True (if not already)
- Start all Docker Compose services plus the ngrok tunnel

Alternatively, you can run manually:

```bash
docker compose --profile ngrok up
```

### 3. Access Your App

Once ngrok starts, it will output public URLs for both the web app and MinIO (static/media). Look for lines like:

```
Forwarding https://xxxx-xxxx-xxx.ngrok-free.dev -> http://web:8000
Forwarding https://yyyy-yyyy-yyy.ngrok-free.dev -> http://minio:9000
```

Open the web app URL in your browser.

### 4. Static & Media Files

When `USE_NGROK=True`, static files (CSS, JS) are served directly by Django via WhiteNoise, and media files are stored locally in the `media/` directory, ensuring they load correctly over the ngrok tunnel. This avoids the need to expose MinIO externally.

If you need to serve media files from MinIO externally, you can re-enable the MinIO tunnel in `ngrok-config.yml` and set `USE_NGROK=False`, but note that ngrok's free tier only provides one tunnel at a time (multiple tunnels may conflict).

### 5. Ngrok Web Interface

Ngrok provides a local web interface at http://localhost:4040 where you can inspect traffic and see tunnel details.

## Troubleshooting

- **Styling not loading**: Ensure `USE_NGROK=True` is set. This switches static storage to WhiteNoise. Also check that collectstatic has run (it runs automatically on container start).
- **Mixed content warnings**: Ngrok uses HTTPS, but Django may generate HTTP URLs for static/media. The configuration sets `CSRF_TRUSTED_ORIGINS` and `AWS_S3_USE_SSL=False`. If you encounter HTTPS issues, consider setting `AWS_S3_USE_SSL=True` and using a custom domain with ngrok.
- **Ngrok tunnel fails**: Verify your authtoken is correct. Check ngrok logs via the web interface.
- **502 Bad Gateway**: This often occurs when multiple tunnels conflict on the same domain (free tier) or when the backend service is not accessible. Ensure only one tunnel is active (web only) and that the web container is running and healthy.
- **URL shows MinIO instead of Django**: The ngrok free tier assigns the same domain to multiple tunnels. Disable the MinIO tunnel in `ngrok-config.yml` and restart ngrok.

## Advanced Configuration

If you want to expose only the web app (not MinIO), edit the `ngrok-config.yml` file and remove the `minio` tunnel section. Then restart.

To customize ngrok further, see [ngrok configuration docs](https://ngrok.com/docs/secure-tunnels/ngrok-agent/config/).

## Notes

- Ngrok free plan provides random subdomains that change each time you restart ngrok. For a stable domain, upgrade to a paid plan.
- This setup is intended for development/testing only. For production, use proper hosting and a domain.