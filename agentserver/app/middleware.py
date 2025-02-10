import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class LoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger_name = f"API {request.method.upper()} {request.url.path}"
        request.state.logger = logging.getLogger(logger_name)
        response = await call_next(request)
        return response
