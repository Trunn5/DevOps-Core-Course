"""
DevOps Info Service
Main application module providing system information and health status.
"""
import os
import socket
import platform
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DevOps Info Service",
    description="DevOps course info service providing system information and health status",
    version="1.0.0"
)

# Configuration from environment variables
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application start time for uptime calculation
START_TIME = datetime.now(timezone.utc)

# Service metadata
SERVICE_INFO = {
    'name': 'devops-info-service',
    'version': '1.0.0',
    'description': 'DevOps course info service',
    'framework': 'FastAPI'
}


def get_uptime():
    """Calculate application uptime since start."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    
    # Build human-readable string
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if remaining_seconds > 0 or not parts:
        parts.append(f"{remaining_seconds} second{'s' if remaining_seconds != 1 else ''}")
    
    return {
        'seconds': seconds,
        'human': ', '.join(parts)
    }


def get_system_info():
    """Collect system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.platform(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }


def get_request_info(request: Request):
    """Extract request information."""
    return {
        'client_ip': request.client.host if request.client else 'unknown',
        'user_agent': request.headers.get('user-agent', 'Unknown'),
        'method': request.method,
        'path': request.url.path
    }


def get_endpoints():
    """List available API endpoints."""
    return [
        {'path': '/', 'method': 'GET', 'description': 'Service information'},
        {'path': '/health', 'method': 'GET', 'description': 'Health check'}
    ]


@app.get('/')
async def index(request: Request):
    """Main endpoint - returns service and system information."""
    logger.info(f'Request: {request.method} {request.url.path} from {request.client.host if request.client else "unknown"}')
    
    uptime = get_uptime()
    
    return {
        'service': SERVICE_INFO,
        'system': get_system_info(),
        'runtime': {
            'uptime_seconds': uptime['seconds'],
            'uptime_human': uptime['human'],
            'current_time': datetime.now(timezone.utc).isoformat(),
            'timezone': 'UTC'
        },
        'request': get_request_info(request),
        'endpoints': get_endpoints()
    }


@app.get('/health')
async def health():
    """Health check endpoint for monitoring and orchestration."""
    logger.debug('Health check requested')
    
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 Not Found errors."""
    logger.warning(f'404 Not Found: {request.url.path}')
    return JSONResponse(
        status_code=404,
        content={
            'error': 'Not Found',
            'message': 'Endpoint does not exist',
            'path': request.url.path
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 Internal Server errors."""
    logger.error(f'500 Internal Server Error: {exc}')
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }
    )


if __name__ == '__main__':
    logger.info(f'Starting DevOps Info Service on {HOST}:{PORT}')
    logger.info(f'Debug mode: {DEBUG}')
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)
