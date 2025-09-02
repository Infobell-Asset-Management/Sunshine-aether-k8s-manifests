import logging
import sys
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add middleware for request logging
class LoggingMiddleware:
    async def __call__(self, request: Request, call_next):
        logger.info(f"Request: {request.method} {request.url}")
        logger.info(f"Headers: {dict(request.headers)}")
        
        try:
            response = await call_next(request)
            logger.info(f"Response status: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )

app = FastAPI(
    title="processor-service",
    version="1.0.0",
    debug=True
)

# Add middleware
app.middleware('http')(LoggingMiddleware())

# Test endpoint for debugging
@app.get("/test")
async def test_endpoint():
    logger.info("Test endpoint called")
    return {"status": "ok", "service": "processor"}

class Asset(BaseModel):
    id: str
    name: str
    type: str
    location: str
    status: str = "active"
    last_updated: datetime = datetime.utcnow()
    metadata: dict = {}

class AssetCreate(BaseModel):
    name: str
    type: str
    location: str
    metadata: Optional[dict] = None

assets_db = {}

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict] = None

@app.get("/assets", response_model=List[Asset])
async def list_assets(request: Request):
    logger.info(f"GET /assets called from {request.client.host}")
    logger.info(f"Current assets in DB: {len(assets_db)} items")
    return list(assets_db.values())

@app.post("/assets", response_model=Asset)
def create_asset(asset: AssetCreate):
    asset_id = str(uuid4())
    asset_data = asset.dict()
    # Ensure metadata is a dict, not None
    if asset_data.get('metadata') is None:
        asset_data['metadata'] = {}
    new_asset = Asset(id=asset_id, **asset_data)
    assets_db[asset_id] = new_asset
    logger.info(f"Created new asset: {new_asset}")
    return new_asset

@app.get("/assets/{asset_id}", response_model=Asset)
def get_asset(asset_id: str):
    asset = assets_db.get(asset_id)
    if not asset:
        logger.warning(f"Asset not found: {asset_id}")
        return JSONResponse(status_code=404, content={"detail": "Asset not found"})
    return asset

@app.put("/assets/{asset_id}", response_model=Asset)
def update_asset(asset_id: str, update: AssetUpdate):
    logger.info(f"PUT /assets/{asset_id} called")
    existing = assets_db.get(asset_id)
    if not existing:
        logger.warning(f"Asset not found: {asset_id}")
        return JSONResponse(status_code=404, content={"detail": "Asset not found"})
    update_data = update.dict(exclude_unset=True)
    updated = existing.copy(update=update_data)
    # bump last_updated
    updated.last_updated = datetime.utcnow()
    assets_db[asset_id] = updated
    logger.info(f"Asset updated: {asset_id}")
    return updated

@app.delete("/assets/{asset_id}")
def delete_asset(asset_id: str):
    logger.info(f"DELETE /assets/{asset_id} called")
    if asset_id not in assets_db:
        logger.warning(f"Asset not found: {asset_id}")
        return JSONResponse(status_code=404, content={"detail": "Asset not found"})
    del assets_db[asset_id]
    logger.info(f"Asset deleted: {asset_id}")
    return {"message": "Asset deleted successfully"}

@app.get("/healthz", response_class=PlainTextResponse)
async def healthz():
    logger.info("Health check called")
    try:
        # Test database connection if needed
        return "ok"
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return Response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content="service unavailable"
        )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting processor service...")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        reload=True
    )