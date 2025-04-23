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
version: '3'
services:
  browserless:
    image: ghcr.io/browserless/chrome
    restart: always
  
  screencurl:
    image: ghcr.io/bitmorse/screencurl
    restart: always
    ports:
      - "9898:9898"
    environment:
      - BROWSERLESS_URL=http://browserless:3000
      - TOKENS=secret-token-1,secret-token-2
    depends_on:
      - browserless
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