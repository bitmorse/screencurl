# screencurl 📸

A dead-simple service that turns URLs into screenshots via GET requests, powered by Browserless with rate limiting.

## 🚀 Quick Start

### Option 1: One-Line Setup (Recommended)

```bash
git clone https://github.com/bitmorse/screencurl.git && cd screencurl && docker compose up -d
```

That's it! Now visit:
```
http://localhost:9898/screenshot?url=https://example.com
```

### Option 2: Step by Step

1. Clone the repository:
   ```bash
   git clone https://github.com/bitmorse/screencurl.git
   cd screencurl
   ```

2. Start the services:
   ```bash
   docker compose up -d
   ```

3. Test it out:
   ```bash
   curl -o screenshot.png "http://localhost:9898/screenshot?url=https://example.com"
   ```

## 📋 Features

- ✅ Simple GET API for screenshots built with FastAPI
- ✅ Rate limiting (max 1 request per URL every 10 seconds)
- ✅ Uses Browserless for reliable rendering
- ✅ Automatic documentation with Swagger UI

## 💻 Usage Examples

### Embedding in HTML

```html
<img src="http://localhost:9898/screenshot?url=https://example.com" alt="Website Screenshot" />
```

### Embedding in Grafana

Add the nocache parameter to prevent caching issues and ensure fresh screenshots when Grafana autoreloads:

```html
<img src="http://localhost:9898/screenshot?url=https://example.com&_nocache=${__from}" alt="Website Screenshot" />
```

### Device Emulation

Screencurl can emulate various devices for more realistic screenshots:

```bash
# Take a screenshot as if viewed on an iPhone 13
http://localhost:9898/screenshot?url=https://example.com&device=iphone13

# See all available devices
http://localhost:9898/devices
```

Available devices include:
- Apple devices: iphone5, iphone6, iphone13, iphone14pro, ipadmini, ipad, ipadpro
- Android devices: pixel2 through pixel7, samsungs8, samsungs20, galaxytabs7
- Desktop presets: desktop, desktop-hd, desktop-4k, macbook-air, macbook-pro, surface-book

Custom dimensions always override device presets:
```bash
# iPhone 13 aspect ratio but with custom width
http://localhost:9898/screenshot?url=https://example.com&device=iphone13&width=500
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Port to run the service on | `9898` |
| `BROWSERLESS_URL` | URL of the Browserless service | `http://localhost:9897` |

## 🔒 Authentication

screencurl supports token-based authentication to restrict access to the screenshot service.

### Enabling Authentication

Set the `TOKENS` environment variable with a comma-separated list of allowed tokens:

```bash
# Single token
TOKENS=your-secret-token

# Multiple tokens
TOKENS=token1,token2,token3
```

If `TOKENS` is not set or empty, authentication is disabled and the service is publicly accessible.

### Using Authentication

Once enabled, you can authenticate using one of these three methods:

**1. Query Parameter:**
```
http://localhost:9898/screenshot?url=https://example.com&token=your-secret-token
```

**2. Request Header:**
```bash
curl -H "X-API-Token: your-secret-token" "http://localhost:9898/screenshot?url=https://example.com"
```

**3. Cookie:**
```bash
curl -b "token=your-secret-token" "http://localhost:9898/screenshot?url=https://example.com"
```

### Docker Compose Configuration

```yaml
version: "3"
services:
  browserless:
    image: ghcr.io/browserless/chrome
    restart: always
    ports:
      - 3003:3000
    environment:
      - TZ=Europe/Berlin

screencurl:
    image: ghcr.io/bitmorse/screencurl
    restart: always
    ports:
      - 9898:9898
    environment:
      - TZ=Europe/Berlin
      - BROWSERLESS_URL=http://browserless:3000
      - TOKENS=your-token1,your-other-token2
      - DEFAULT_VIEWPORT_WIDTH=1920
      - DEFAULT_VIEWPORT_HEIGHT=1080
      - WAIT_FOR_LOAD=networkidle0 # Strictest option - waits until there are 0 network connections for 500ms
    depends_on:
      - browserless
networks: {}

```

## 📚 API Documentation

FastAPI automatically generates interactive API documentation:

- Swagger UI: http://localhost:9898/docs
- ReDoc: http://localhost:9898/redoc

## ❓ Troubleshooting

### Common Issues

- **404 Not Found**: Make sure the URL parameter is properly encoded
- **429 Too Many Requests**: Wait 10 seconds before requesting the same URL again
- **500 Server Error**: Check if Browserless is running correctly

### Logs

```bash
# View logs
docker compose logs -f
```


## 📄 License

MIT
