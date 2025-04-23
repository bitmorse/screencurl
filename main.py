from fastapi import FastAPI, HTTPException, Response, Query, Depends, Security, Request
import httpx
import time
from typing import Dict, List, Optional
import os
import uvicorn
from fastapi.security.api_key import APIKeyQuery, APIKeyHeader, APIKeyCookie
from datetime import datetime
import pytz
from collections import defaultdict

app = FastAPI(title="screencurl")

# Simple cache to store the last screenshot time for each URL
screenshot_times: Dict[str, float] = {}
# Track screenshot counts per IP
screenshots_per_ip: Dict[str, int] = defaultdict(int)
RATE_LIMIT_SECONDS = 10
BROWSERLESS_URL = os.getenv("BROWSERLESS_URL", "http://localhost:9897")

# Screenshot settings with defaults
DEFAULT_VIEWPORT_WIDTH = int(os.getenv("DEFAULT_VIEWPORT_WIDTH", "1280"))
DEFAULT_VIEWPORT_HEIGHT = int(os.getenv("DEFAULT_VIEWPORT_HEIGHT", "800"))
WAIT_FOR_LOAD = os.getenv("WAIT_FOR_LOAD", "networkidle2")  # Other options: load, domcontentloaded, networkidle0

# Parse tokens from environment variable
TOKENS = os.getenv("TOKENS", "").split(",")
TOKENS = [token.strip() for token in TOKENS if token.strip()]  # Remove empty tokens

# Get timezone from environment variable or default to UTC
TIMEZONE = os.getenv("TIMEZONE", "UTC")
try:
    TIMEZONE_OBJ = pytz.timezone(TIMEZONE)
    print(f"Using timezone: {TIMEZONE}")
except pytz.exceptions.UnknownTimeZoneError:
    print(f"Unknown timezone: {TIMEZONE}, falling back to UTC")
    TIMEZONE_OBJ = pytz.UTC
    TIMEZONE = "UTC"

# API key security schemes
api_key_query = APIKeyQuery(name="token", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Token", auto_error=False)
api_key_cookie = APIKeyCookie(name="token", auto_error=False)

async def get_api_key(
    query_token: str = Security(api_key_query),
    header_token: str = Security(api_key_header),
    cookie_token: str = Security(api_key_cookie),
) -> str:
    # If no tokens are configured, authentication is disabled
    if not TOKENS:
        return None
    
    # Check if the token is in the configured tokens
    for token in [query_token, header_token, cookie_token]:
        if token and token in TOKENS:
            return token
    
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing API token",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_current_time():
    """Get current time in the configured timezone with timezone info"""
    return datetime.now(TIMEZONE_OBJ).strftime("%Y-%m-%d %H:%M:%S %Z")

@app.get("/screenshot")
async def screenshot(
    request: Request,
    url: str = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    token: str = Depends(get_api_key)
):
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")
    
    # Use provided dimensions or defaults
    viewport_width = width or DEFAULT_VIEWPORT_WIDTH
    viewport_height = height or DEFAULT_VIEWPORT_HEIGHT
    
    # Get client information for logging
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")
    referer = request.headers.get("referer", "Unknown")
    current_time = get_current_time()
    
    # Increment screenshot count for this IP
    screenshots_per_ip[client_ip] += 1
    total_screenshots = screenshots_per_ip[client_ip]
    
    # Log the screenshot request with detailed information
    print(f"[SCREENSHOT] Time: {current_time} | IP: {client_ip} | Total: {total_screenshots} | User-Agent: {user_agent} | Referer: {referer} | URL: {url} | Resolution: {viewport_width}x{viewport_height}")
    
    # Check rate limit
    now = time.time()
    last_screenshot_time = screenshot_times.get(url, 0)
    
    if now - last_screenshot_time < RATE_LIMIT_SECONDS:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a few seconds.")
    
    # Update last screenshot time
    screenshot_times[url] = now
    
    try:
        async with httpx.AsyncClient() as client:
            browserless_endpoint = f"{BROWSERLESS_URL}/chrome/screenshot"
            print(f"Sending request to: {browserless_endpoint}")
            
            # Enhanced request with viewport and waiting options
            response = await client.post(
                browserless_endpoint,
                json={
                    "url": url,
                    "options": {
                        "fullPage": True,
                        "type": "png"
                    },
                    "gotoOptions": {
                        "waitUntil": WAIT_FOR_LOAD,
                        "timeout": 25000  # 25 seconds timeout for page load
                    },
                    "viewport": {
                        "width": viewport_width,
                        "height": viewport_height,
                        "deviceScaleFactor": 1
                    }
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                error_detail = response.text
                print(f"Browserless error: Status {response.status_code} - {error_detail}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Error from browserless service: {error_detail[:200]}"
                )
            
            # Get content type from response header or default to image/png
            content_type = response.headers.get("content-type", "image/png")
            
            # Log successful screenshot
            print(f"[SUCCESS] Screenshot generated for {url} by {client_ip} | Size: {len(response.content)} bytes")
            
            return Response(
                content=response.content,
                media_type=content_type,
                headers={"Cache-Control": "public, max-age=10"}
            )
    except httpx.RequestError as e:
        error_msg = f"Request error: {str(e)}"
        print(f"[ERROR] {client_ip}: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] {client_ip}: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Error taking screenshot: {error_msg}")

@app.get("/")
async def root(request: Request):
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")
    print(f"[INFO] Home page visited by IP: {client_ip} | User-Agent: {user_agent}")
    
    if TOKENS:
        auth_note = " Authentication is required."
    else:
        auth_note = " No authentication required."
        
    return {
        "message": f"Welcome to screencurl. Use /screenshot?url=https://example.com to get screenshots.{auth_note}",
        "options": {
            "resolution": f"Default: {DEFAULT_VIEWPORT_WIDTH}x{DEFAULT_VIEWPORT_HEIGHT} (can be changed with width and height parameters)",
            "wait_strategy": WAIT_FOR_LOAD
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "9898"))
    print(f"screencurl service listening at http://localhost:{port}")
    print(f"Using Browserless at {BROWSERLESS_URL}")
    print(f"Authentication {'enabled with ' + str(len(TOKENS)) + ' tokens' if TOKENS else 'disabled'}")
    print(f"Default screenshot resolution: {DEFAULT_VIEWPORT_WIDTH}x{DEFAULT_VIEWPORT_HEIGHT}")
    print(f"Page load wait strategy: {WAIT_FOR_LOAD}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")