from fastapi import FastAPI, HTTPException, Response
import httpx
import time
from typing import Dict
import os
import uvicorn

app = FastAPI(title="screencurl")

# Simple cache to store the last screenshot time for each URL
screenshot_times: Dict[str, float] = {}
RATE_LIMIT_SECONDS = 10
BROWSERLESS_URL = os.getenv("BROWSERLESS_URL", "http://localhost:9897")

@app.get("/screenshot")
async def screenshot(url: str = None):
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")
    
    # Check rate limit
    now = time.time()
    last_screenshot_time = screenshot_times.get(url, 0)
    
    if now - last_screenshot_time < RATE_LIMIT_SECONDS:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a few seconds.")
    
    # Update last screenshot time
    screenshot_times[url] = now
    
    try:
        async with httpx.AsyncClient() as client:
            browserless_endpoint = f"{BROWSERLESS_URL}/chromium/screenshot"
            print(f"Sending request to: {browserless_endpoint}")
            
            response = await client.post(
                browserless_endpoint,
                json={"url": url},
                timeout=30.0
            )
            
            if response.status_code != 200:
                error_detail = response.text
                print(f"Browserless error: Status {response.status_code} - {error_detail}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Error from browserless service: {error_detail[:200]}"
                )
            
            return Response(
                content=response.content,
                media_type="image/png",
                headers={"Cache-Control": "public, max-age=10"}
            )
    except httpx.RequestError as e:
        error_msg = f"Request error: {str(e)}"
        print(f"Error taking screenshot: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = str(e)
        print(f"Error taking screenshot: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Error taking screenshot: {error_msg}")

@app.get("/")
async def root():
    return {"message": "Welcome to screencurl. Use /screenshot?url=https://example.com to get screenshots."}

if __name__ == "__main__":
    port = int(os.getenv("PORT", "9898"))
    print(f"screencurl service listening at http://localhost:{port}")
    print(f"Using Browserless at {BROWSERLESS_URL}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")