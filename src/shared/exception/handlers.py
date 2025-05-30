from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Any, Dict


async def global_validation_exception_handler(
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Global exception handler for request validation errors.
    """
    errors = [
        {
            "field": ".".join(map(str, error["loc"])),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]

    return JSONResponse(status_code=422, content={"detail": errors, "success": False})


def register_global_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers.
    """
    app.add_exception_handler(
        RequestValidationError, global_validation_exception_handler
    )
