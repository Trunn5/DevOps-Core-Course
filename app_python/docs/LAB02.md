# Lab 02 - Docker Containerization

## Best Practices Applied

| Practice | Why It Matters                                                             |
|----------|----------------------------------------------------------------------------|
| **Non-root user** | Security - limits damage if container has hacked                           |
| **python:3.13-slim** | Smaller image (~200MB vs ~1GB full)                                        |
| **Layer ordering** | Cache optimization - doesn't redownload the dependecies after code changed |
| **.dockerignore** | Keep only necessary, faster builds, smaller context, no secrets leaked     |

### Dockerfile Breakdown

```dockerfile
# Specific version, slim variant
FROM python:3.13-slim

# Security: non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Layer caching: dependencies first (rarely change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code (changes frequently)
COPY app.py .

# Switch to non-root
USER appuser

EXPOSE 5000
CMD ["python", "app.py"]
```

---

## Image Information

- **Base image**: `python:3.13-slim` — minimal Debian with Python, no extra packages
- **Final size**: ~267MB
- **Layers**: 7 (base → user → workdir → deps → code → user switch → cmd)

---

## Build & Run

```bash
# Build
docker build -t devops-info-service app_python

# Run
docker run -p 5000:5000 devops-info-service

# Test
curl http://localhost:5000/
curl http://localhost:5000/health
```

---

## Docker Hub

```bash
docker tag devops-info-service dmitry567/devops-info-service:1.0.0
docker push dmitry567/devops-info-service:1.0.0
```

**Repository**: `https://hub.docker.com/r/dmitry567/devops-info-service`

---

## Challenges

| Problem | Solution |
|---------|----------|
| Large image size | Used `slim` variant instead of full Python image |
| Slow rebuilds | Moved `COPY requirements.txt` before `COPY app.py` |

