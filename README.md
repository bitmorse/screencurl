:::thinking
Let me create an improved README that offers the best quickstart developer experience. I'll focus on:

1. Clear, concise steps
2. Visual aids (emoji/formatting) to improve readability
3. Getting developers up and running as quickly as possible
4. Providing all essential information without overwhelming
5. Examples that work out of the box
6. Troubleshooting tips for common issues

This should make it extremely easy for developers to get started with screencurl.
:::
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

### curl Command

```bash
curl -o screenshot.png "http://localhost:9898/screenshot?url=https://example.com"
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Port to run the service on | `9898` |
| `BROWSERLESS_URL` | URL of the Browserless service | `http://localhost:9897` |

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