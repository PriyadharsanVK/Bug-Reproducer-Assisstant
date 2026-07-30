import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.db.session import engine, Base
from apps.api.routes import issues, analysis, feedback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bug Reproducer Assistant API",
    description="University & Startup Grade AI Assistant converting bug reports into reproduction artifacts.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")

app.include_router(issues.router)
app.include_router(analysis.router)
app.include_router(feedback.router)

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "bug-reproducer-api",
        "primary_model": os.getenv("GROQ_MODEL_PRIMARY", "llama-3.3-70b-versatile"),
        "code_model": os.getenv("GROQ_MODEL_CODE", "deepseek-r1-distill-llama-70b")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=8000, reload=True)
