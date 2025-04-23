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

# Standard device presets from Puppeteer/Chrome DevTools Protocol
# Source: https://github.com/puppeteer/puppeteer/blob/main/packages/puppeteer-core/src/common/DeviceDescriptors.ts
DEVICES = {
    # Apple Devices
    "iphone5": {"viewport": {"width": 320, "height": 568, "deviceScaleFactor": 2, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1"},
    "iphone6": {"viewport": {"width": 375, "height": 667, "deviceScaleFactor": 2, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"},
    "iphone6plus": {"viewport": {"width": 414, "height": 736, "deviceScaleFactor": 3, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"},
    "iphonex": {"viewport": {"width": 375, "height": 812, "deviceScaleFactor": 3, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"},
    "iphone12": {"viewport": {"width": 390, "height": 844, "deviceScaleFactor": 3, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"},
    "iphone13": {"viewport": {"width": 390, "height": 844, "deviceScaleFactor": 3, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"},
    "iphone13mini": {"viewport": {"width": 375, "height": 812, "deviceScaleFactor": 3, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"},
    "iphone13pro": {"viewport": {"width": 390, "height": 844, "deviceScaleFactor": 3, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"},
    "iphone13promax": {"viewport": {"width": 428, "height": 926, "deviceScaleFactor": 3, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"},
    "iphone14": {"viewport": {"width": 390, "height": 844, "deviceScaleFactor": 3, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"},
    "iphone14pro": {"viewport": {"width": 393, "height": 852, "deviceScaleFactor": 3, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"},
    "iphone14promax": {"viewport": {"width": 430, "height": 932, "deviceScaleFactor": 3, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"},
    "ipadmini": {"viewport": {"width": 768, "height": 1024, "deviceScaleFactor": 2, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1"},
    "ipad": {"viewport": {"width": 810, "height": 1080, "deviceScaleFactor": 2, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1"},
    "ipadpro": {"viewport": {"width": 1024, "height": 1366, "deviceScaleFactor": 2, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1"},
    
    # Android Devices
    "pixel2": {"viewport": {"width": 411, "height": 731, "deviceScaleFactor": 2.625, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3765.0 Mobile Safari/537.36"},
    "pixel3": {"viewport": {"width": 393, "height": 786, "deviceScaleFactor": 2.75, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (Linux; Android 9; Pixel 3 Build/PQ1A.181105.017.A1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.158 Mobile Safari/537.36"},
    "pixel4": {"viewport": {"width": 393, "height": 830, "deviceScaleFactor": 2.75, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (Linux; Android 10; Pixel 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Mobile Safari/537.36"},
    "pixel5": {"viewport": {"width": 393, "height": 851, "deviceScaleFactor": 2.75, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36"},
    "pixel6": {"viewport": {"width": 393, "height": 851, "deviceScaleFactor": 2.8, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.104 Mobile Safari/537.36"},
    "pixel7": {"viewport": {"width": 412, "height": 915, "deviceScaleFactor": 2.8, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36"},
    "samsungs8": {"viewport": {"width": 360, "height": 740, "deviceScaleFactor": 3, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (Linux; Android 8.0.0; SM-G950U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.111 Mobile Safari/537.36"},
    "samsungs9": {"viewport": {"width": 360, "height": 740, "deviceScaleFactor": 3, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (Linux; Android 8.0.0; SM-G960U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.111 Mobile Safari/537.36"},
    "samsungs20": {"viewport": {"width": 360, "height": 800, "deviceScaleFactor": 3, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (Linux; Android 10; SM-G980F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Mobile Safari/537.36"},
    "galaxytabs7": {"viewport": {"width": 753, "height": 1193, "deviceScaleFactor": 3, "isMobile": True, "hasTouch": True}, "userAgent": "Mozilla/5.0 (Linux; Android 10; SM-T870) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.62 Safari/537.36"},
    
    # Desktop presets
    "desktop": {"viewport": {"width": 1280, "height": 800, "deviceScaleFactor": 1, "isMobile": False, "hasTouch": False}},
    "desktop-hd": {"viewport": {"width": 1920, "height": 1080, "deviceScaleFactor": 1, "isMobile": False, "hasTouch": False}},
    "desktop-4k": {"viewport": {"width": 3840, "height": 2160, "deviceScaleFactor": 2, "isMobile": False, "hasTouch": False}},
    "macbook-air": {"viewport": {"width": 1280, "height": 800, "deviceScaleFactor": 2, "isMobile": False, "hasTouch": False}},
    "macbook-pro": {"viewport": {"width": 1440, "height": 900, "deviceScaleFactor": 2, "isMobile": False, "hasTouch": False}},
    "macbook-pro-16": {"viewport": {"width": 1536, "height": 960, "deviceScaleFactor": 2, "isMobile": False, "hasTouch": False}},
    "surface-book": {"viewport": {"width": 1500, "height": 1000, "deviceScaleFactor": 2, "isMobile": False, "hasTouch": True}}
}

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
    device: Optional[str] = None,
    token: str = Depends(get_api_key)
):
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")
    
    # Initialize viewport with defaults
    viewport = {
        "width": DEFAULT_VIEWPORT_WIDTH,
        "height": DEFAULT_VIEWPORT_HEIGHT,
        "deviceScaleFactor": 1,
        "isMobile": False,
        "hasTouch": False
    }
    
    # Override with device preset if specified
    user_agent = None
    device_info = ""
    if device:
        device = device.lower()  # Normalize device name
        if device in DEVICES:
            viewport.update(DEVICES[device]["viewport"])
            if "userAgent" in DEVICES[device]:
                user_agent = DEVICES[device]["userAgent"]
            device_info = f" using device preset: {device}"
        else:
            available_devices = ", ".join(DEVICES.keys())
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown device: {device}. Available devices: {available_devices}"
            )
    
    # Override with custom dimensions if specified
    if width:
        viewport["width"] = width
    if height:
        viewport["height"] = height
    
    # Get client information for logging
    client_ip = request.client.host
    client_user_agent = request.headers.get("user-agent", "Unknown")
    referer = request.headers.get("referer", "Unknown")
    current_time = get_current_time()
    
    # Increment screenshot count for this IP
    screenshots_per_ip[client_ip] += 1
    total_screenshots = screenshots_per_ip[client_ip]
    
    # Log the screenshot request with detailed information
    print(f"[SCREENSHOT] Time: {current_time} | IP: {client_ip} | Total: {total_screenshots} | User-Agent: {client_user_agent} | Referer: {referer} | URL: {url} | Resolution: {viewport['width']}x{viewport['height']}{device_info}")
    
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
            
            # Build request JSON
            request_data = {
                "url": url,
                "options": {
                    "fullPage": True,
                    "type": "png"
                },
                "gotoOptions": {
                    "waitUntil": WAIT_FOR_LOAD,
                    "timeout": 25000  # 25 seconds timeout for page load
                },
                "viewport": viewport
            }
            
            # Add user agent as a top-level property, not in viewport
            if user_agent:
                request_data["userAgent"] = user_agent
                
            response = await client.post(
                browserless_endpoint,
                json=request_data,
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

@app.get("/devices")
async def list_devices():
    """Return a list of all available device presets"""
    result = {}
    for device_name, specs in DEVICES.items():
        result[device_name] = {
            "width": specs["viewport"]["width"],
            "height": specs["viewport"]["height"],
            "deviceScaleFactor": specs["viewport"]["deviceScaleFactor"],
            "isMobile": specs["viewport"]["isMobile"],
            "hasTouch": specs["viewport"]["hasTouch"]
        }
        if "userAgent" in specs:
            result[device_name]["userAgent"] = specs["userAgent"]
    return result

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
            "wait_strategy": WAIT_FOR_LOAD,
            "device_emulation": "Use /screenshot?url=example.com&device=iphone13 to emulate specific devices",
            "available_devices": "View all available devices at /devices"
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "9898"))
    print(f"screencurl service listening at http://localhost:{port}")
    print(f"Using Browserless at {BROWSERLESS_URL}")
    print(f"Authentication {'enabled with ' + str(len(TOKENS)) + ' tokens' if TOKENS else 'disabled'}")
    print(f"Default screenshot resolution: {DEFAULT_VIEWPORT_WIDTH}x{DEFAULT_VIEWPORT_HEIGHT}")
    print(f"Page load wait strategy: {WAIT_FOR_LOAD}")
    print(f"Available device presets: {len(DEVICES)}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")