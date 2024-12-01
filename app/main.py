from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.database import engine
from app.models import SQLModel
from app.routers import books, users
import logging
import traceback

# Initialize logging
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more detailed logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Initialize app
app = FastAPI()


# Create database tables
try:
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created successfully.")
except Exception as e:
    logger.critical(
        f"Error while creating database tables: {e}", exc_info=True)
    raise e


# Include routers
app.include_router(users.router)
app.include_router(books.router)


@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        # Capture the exception and its traceback
        tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        
        # Log the detailed error with traceback
        logger.error(f"Unhandled Exception: {exc}\nTraceback:\n{tb_str}")

        # Return a generic error response
        return JSONResponse(
            status_code=500,
            content={
                "message": "An internal server error occurred. Please check logs.",
                "error": str(exc),  # Optionally include this for debugging
            },
        )


# Attach token blacklist to app state
@app.on_event("startup")
async def startup_event():
    app.state.revoked_tokens = {}


@app.on_event("shutdown")
async def shutdown_event():
    app.state.revoked_tokens.clear()


@app.get("/")
def root():
    logger.info("Root endpoint accessed.")
    return {"message": "Welcome to BookStore API"}
