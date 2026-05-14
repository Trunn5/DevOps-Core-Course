# Lab 01 - DevOps Info Service

## Framework Choice: FastAPI

| Criteria | Flask | FastAPI | Django |
|----------|-------|---------|--------|
| Auto API Docs | ❌ | ✅ | ❌ |
| Async Support | ❌ | ✅ | ❌ |
| Performance | Good | Excellent | Good |
| Learning Curve | Easy | Easy | Hard |

**Why FastAPI:** Auto-generated Swagger docs (`/docs`), native async, type safety, high performance.

---

## Best Practices

1. **Environment Config** - `HOST`, `PORT`, `DEBUG` via `os.getenv()`
2. **Logging** - Structured logging with timestamps
3. **Error Handling** - Custom 404/500 JSON responses
4. **Clean Code** - PEP 8, docstrings, separated functions

---

## API Endpoints

### `GET /`
```bash
curl http://localhost:5000/
```
Returns: service info, system info, runtime, request details, endpoints list.

### `GET /health`
```bash
curl http://localhost:5000/health
```
Returns: `{"status": "healthy", "timestamp": "...", "uptime_seconds": 123}`

### Auto Docs
- Swagger: `http://localhost:5000/docs`
- ReDoc: `http://localhost:5000/redoc`

---

## Screenshots

1. `screenshots/01-main-endpoint.png` - Main endpoint response
2. `screenshots/02-health-check.png` - Health check response
3. `screenshots/03-formatted-output.png` - Pretty JSON / Swagger UI

---

## Challenges

| Problem | Solution |
|---------|----------|
| Timezone errors | Use `datetime.now(timezone.utc)` everywhere |
| Client IP access | `request.client.host` with null check |
