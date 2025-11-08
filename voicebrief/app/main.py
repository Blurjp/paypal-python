"""
VoiceBrief - Main FastAPI Application

A B2B SaaS platform that converts company updates into audio briefings
delivered via Slack.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
from contextlib import asynccontextmanager

from app.config import get_settings
from app.routes import upload, briefings, slack, stats, listen

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("🚀 VoiceBrief starting up...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Base URL: {settings.app_base_url}")
    yield
    logger.info("👋 VoiceBrief shutting down...")


# Create FastAPI app
app = FastAPI(
    title="VoiceBrief API",
    description="Convert company updates into audio briefings delivered via Slack",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(upload.router, tags=["Upload"])
app.include_router(briefings.router, tags=["Briefings"])
app.include_router(slack.router, tags=["Slack"])
app.include_router(stats.router, tags=["Analytics"])
app.include_router(listen.router, tags=["Listen"])


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "VoiceBrief API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "upload": "/upload",
            "list_briefings": "/briefings",
            "get_briefing": "/briefings/{id}",
            "slack_events": "/slack/events",
            "stats": "/stats",
            "listen": "/listen/{id}",
            "demo": "/demo"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment
    }


@app.post("/demo")
async def demo_briefing():
    """
    Create a demo briefing with sample HR policy text.
    Useful for testing the entire workflow.
    """
    from app.routes.upload import process_briefing_background
    from uuid import uuid4
    from app.services.supabase_service import supabase_service

    sample_content = """
    UPDATED DATA PRIVACY POLICY - EFFECTIVE IMMEDIATELY

    Dear Team,

    We are implementing important updates to our data privacy policy to ensure compliance
    with the latest GDPR and CCPA regulations. These changes affect how we collect, store,
    and process customer data.

    Key Changes:

    1. Enhanced Encryption: All customer data will now be encrypted at rest using AES-256
    encryption. This applies to both production and backup databases.

    2. Data Retention: We are reducing our data retention period from 7 years to 5 years
    for non-essential customer information. Essential records for compliance will still
    be retained for 7 years.

    3. Third-Party Sharing: We have revised our third-party data sharing agreements. Only
    vendors who have passed our new security audit will have access to customer data.

    4. Customer Rights: Customers now have enhanced rights to request data deletion within
    30 days instead of 90 days. Our customer service team has been trained on the new
    process.

    5. Breach Notification: We are implementing a 24-hour breach notification protocol.
    Any suspected data breach must be reported to the security team immediately.

    Action Required:

    - All team members must complete the updated data privacy training in the learning
      portal by end of month
    - Engineering teams should review and update data handling procedures
    - Customer-facing teams should familiarize themselves with the new customer rights
      processes

    These changes demonstrate our commitment to protecting customer privacy and maintaining
    the highest security standards. If you have questions, please contact the legal team
    or attend the Q&A session scheduled for next Tuesday at 2 PM.

    Thank you for your attention to this important matter.

    Best regards,
    Legal & Compliance Team
    """

    try:
        # Create demo briefing
        briefing = supabase_service.create_briefing(
            title="Data Privacy Policy Update - December 2024",
            summary_text="Processing...",
            original_content=sample_content,
            created_by="demo",
            source_type="text",
            metadata={"is_demo": True}
        )

        briefing_id = briefing["id"]

        # Process in background
        import asyncio
        asyncio.create_task(
            process_briefing_background(
                briefing_id=briefing_id,
                title="Data Privacy Policy Update - December 2024",
                content=sample_content,
                channel=None  # Will use default channel
            )
        )

        return {
            "status": "ok",
            "message": "Demo briefing is being processed and will be posted to Slack",
            "briefing_id": briefing_id,
            "listen_url": f"{settings.app_base_url}/listen/{briefing_id}"
        }

    except Exception as e:
        logger.error(f"Error creating demo briefing: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to create demo briefing"}
        )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.environment == "development"
    )
