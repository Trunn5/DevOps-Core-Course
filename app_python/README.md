# DevOps Info Service

![CI](https://github.com/dmitry567/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)

A Python web service that provides detailed information about itself and its runtime environment. Built as part of the DevOps course curriculum.

## Overview

The DevOps Info Service is a modern FastAPI-based web application that exposes system information, runtime metrics, and health status through a REST API. This service serves as a foundation for learning DevOps practices including containerization, CI/CD, monitoring, and Kubernetes deployment.

## Prerequisites

- **Python**: 3.11 or higher
- **pip**: Python package manager
- **Virtual environment** (recommended)

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd app_python
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Development Mode

```bash
python app.py
```

The service will start on `http://0.0.0.0:5000` by default.

### Custom Configuration

```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode (auto-reload)
DEBUG=true python app.py
```

### Using Uvicorn Directly

```bash
uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

## API Endpoints

FastAPI provides automatic interactive API documentation at:
- **Swagger UI**: `http://localhost:5000/docs`
- **ReDoc**: `http://localhost:5000/redoc`

### `GET /` - Service Information

Returns comprehensive service and system information.

**Request:**
```bash
curl http://localhost:5000/
```

**Response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "Darwin",
    "platform_version": "macOS-14.0-arm64-arm-64bit",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.11.0"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-01-28T14:30:00.000000+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### `GET /health` - Health Check

Returns the health status of the service. Used for monitoring and orchestration (e.g., Kubernetes probes).

**Request:**
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T14:30:00.000000+00:00",
  "uptime_seconds": 3600
}
```

**HTTP Status Codes:**
- `200 OK` - Service is healthy

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind to |
| `PORT` | `5000` | Port number to listen on |
| `DEBUG` | `False` | Enable uvicorn reload mode |

## Docker

### Build Image
```bash
docker build -t devops-info-service .
```

### Run Container
```bash
docker run -p 5000:5000 devops-info-service
```

### Pull from Docker Hub
```bash
docker pull dmitry567/devops-info-service:latest
docker run -p 5000:5000 dmitry567/devops-info-service:latest
```

## Project Structure

```
app_python/
├── app.py                    # Main application
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── tests/                   # Unit tests
│   └── __init__.py
└── docs/                    # Documentation
    ├── LAB01.md            # Lab submission
    └── screenshots/        # Evidence screenshots
```

## Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=. --cov-report=term

# Lint
ruff check .
```

## Development

### Code Style

This project follows [PEP 8](https://pep8.org/) style guidelines. Key practices:

- Clear, descriptive function names
- Docstrings for all functions
- Proper import grouping (standard library, third-party, local)
- Async/await for endpoint handlers

### Logging

The application uses Python's built-in logging module with INFO level by default:

```
2026-01-28 14:30:00,000 - app - INFO - Starting DevOps Info Service on 0.0.0.0:5000
2026-01-28 14:30:05,123 - app - INFO - Request: GET / from 127.0.0.1
```

## Future Enhancements

This service will evolve throughout the DevOps course:

- **Lab 2**: Docker containerization
- **Lab 3**: Unit tests and CI/CD pipeline
- **Lab 8**: Prometheus metrics endpoint (`/metrics`)
- **Lab 9**: Kubernetes deployment with health probes
- **Lab 12**: Visit counter with file persistence (`/visits`)

## License

This project is part of the DevOps course curriculum.
