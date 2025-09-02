from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_service.log')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Asset API Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
# Use service names for container-to-container communication
PROCESSOR_SERVICE_URL = os.getenv("PROCESSOR_SERVICE_URL", "http://processor-service:8000")
COLLECTOR_SERVICE_URL = os.getenv("COLLECTOR_SERVICE_URL", "http://collector-service:8000")

def normalize_url(url: str, fallback: str) -> str:
    try:
        url = (url or "").strip()
        if not url:
            return fallback
        if not (url.startswith("http://") or url.startswith("https://")):
            return f"http://{url}"
        return url
    except Exception:
        return fallback

PROCESSOR_SERVICE_URL = normalize_url(PROCESSOR_SERVICE_URL, "http://127.0.0.1:8001")
COLLECTOR_SERVICE_URL = normalize_url(COLLECTOR_SERVICE_URL, "http://127.0.0.1:8002")

class Asset(BaseModel):
    id: str
    name: str
    type: str
    location: str
    status: str
    last_updated: datetime
    metadata: Dict[str, Any]

class AssetCreate(BaseModel):
    name: str
    type: str
    location: str
    metadata: Optional[Dict[str, Any]] = None

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, str]

@app.get("/", response_model=Dict[str, str])
async def root():
    return {"msg": "Hello from Asset API Service"}

@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check with downstream service status"""
    services = {}
    
    # Check processor service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PROCESSOR_SERVICE_URL}/healthz", timeout=5.0)
            services["processor"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        services["processor"] = "unreachable"
    
    # Check collector service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{COLLECTOR_SERVICE_URL}/healthz", timeout=5.0)
            services["collector"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        services["collector"] = "unreachable"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        services=services
    )

@app.get("/assets", response_model=List[Asset])
async def get_assets(
    skip: int = 0,
    limit: int = 100,
    asset_type: Optional[str] = None,
    status: Optional[str] = None
):
    """Get assets with optional filtering"""
    try:
        print(f"[DEBUG] Fetching assets from {PROCESSOR_SERVICE_URL}/assets")
        print(f"[DEBUG] Params: skip={skip}, limit={limit}, asset_type={asset_type}, status={status}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {"skip": skip, "limit": limit}
            if asset_type:
                params["asset_type"] = asset_type
            if status:
                params["status"] = status
            
            print(f"[DEBUG] Sending request to processor service...")
            response = await client.get(
                f"{PROCESSOR_SERVICE_URL}/assets",
                params=params,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"[DEBUG] Response status: {response.status_code}")
            print(f"[DEBUG] Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            data = response.json()
            print(f"[DEBUG] Received data: {data}")
            return data
            
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error from processor service: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(f"[ERROR] Response content: {e.response.text if hasattr(e, 'response') else 'No response'}")
        raise HTTPException(status_code=e.response.status_code, detail=error_msg)
    except httpx.RequestError as e:
        error_msg = f"Request to processor service failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        raise HTTPException(status_code=503, detail=error_msg)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/assets/{asset_id}", response_model=Asset)
async def get_asset(asset_id: str):
    """Get a specific asset by ID"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PROCESSOR_SERVICE_URL}/assets/{asset_id}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Asset not found")
        raise HTTPException(status_code=e.response.status_code, detail="Failed to fetch asset")
    except Exception as e:
        logger.error(f"Error fetching asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/assets", response_model=Asset)
async def create_asset(asset: AssetCreate):
    """Create a new asset"""
    logger.debug(f"[POST /assets] Creating new asset: {asset.dict()}")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.debug(f"[POST /assets] Sending request to {PROCESSOR_SERVICE_URL}/assets")
            logger.debug(f"[POST /assets] Request payload: {asset.dict()}")
            
            response = await client.post(
                f"{PROCESSOR_SERVICE_URL}/assets",
                json=asset.dict(),
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            
            logger.debug(f"[POST /assets] Response status: {response.status_code}")
            logger.debug(f"[POST /assets] Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"[POST /assets] Created asset: {data}")
            return data
            
    except httpx.HTTPStatusError as e:
        error_detail = str(e)
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json().get('detail', str(e))
                logger.error(f"[POST /assets] HTTP error response: {e.response.text}")
            except Exception as json_err:
                error_detail = e.response.text or str(e)
                logger.error(f"[POST /assets] Error parsing error response: {str(json_err)}")
        
        logger.error(f"[POST /assets] HTTP error: {error_detail}")
        raise HTTPException(
            status_code=e.response.status_code if hasattr(e, 'response') and e.response else 500,
            detail=error_detail
        )
    except Exception as e:
        logger.error(f"[POST /assets] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.put("/assets/{asset_id}", response_model=Asset)
async def update_asset(asset_id: str, asset: AssetUpdate):
    """Update an existing asset"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{PROCESSOR_SERVICE_URL}/assets/{asset_id}", json=asset.dict(exclude_unset=True))
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Asset not found")
        raise HTTPException(status_code=e.response.status_code, detail="Failed to update asset")
    except Exception as e:
        logger.error(f"Error updating asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/assets/{asset_id}")
async def delete_asset(asset_id: str):
    """Delete an asset"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{PROCESSOR_SERVICE_URL}/assets/{asset_id}")
            response.raise_for_status()
            return {"message": "Asset deleted successfully"}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Asset not found")
        raise HTTPException(status_code=e.response.status_code, detail="Failed to delete asset")
    except Exception as e:
        logger.error(f"Error deleting asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/events")
async def get_events(limit: int = 100):
    """Get recent events from collector service"""
    try:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{COLLECTOR_SERVICE_URL}/events", params={"limit": limit})
                response.raise_for_status()
                return response.json()
            except Exception:
                # Fallback to localhost collector
                response = await client.get("http://127.0.0.1:8002/events", params={"limit": limit})
                response.raise_for_status()
                return response.json()
    except Exception as e:
        # Fallback to empty list to keep UI functional when collector is down/unreachable
        logger.warning(f"Collector unreachable, returning empty events list. Error: {e}")
        return []

@app.get("/stats")
async def get_stats():
    """Get combined statistics from collector and processor services"""
    collector_stats = {
        "total_events_processed": 0,
        "events_by_type": {},
        "last_processed": None,
    }
    total_assets = 0
    active_assets = 0

    try:
        async with httpx.AsyncClient() as client:
            # Collector stats (optional)
            try:
                c_resp = await client.get(f"{COLLECTOR_SERVICE_URL}/stats")
                c_resp.raise_for_status()
                collector_stats = c_resp.json()
            except Exception as e:
                logger.warning(f"Collector stats unavailable, using defaults. Error: {e}")

            # Processor assets for asset counts
            try:
                p_resp = await client.get(f"{PROCESSOR_SERVICE_URL}/assets")
                p_resp.raise_for_status()
                assets = p_resp.json()
                total_assets = len(assets)
                active_assets = sum(1 for a in assets if str(a.get("status", "")).lower() == "active")
            except Exception as e:
                logger.warning(f"Processor assets unavailable, counts set to 0. Error: {e}")

    except Exception as e:
        logger.error(f"Error building stats: {e}")

    return {
        **collector_stats,
        "total_assets": total_assets,
        "active_assets": active_assets,
    }

@app.get("/system/metrics")
async def get_system_metrics():
    """Return a parsed summary of the latest system_metrics event from collector."""
    try:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{COLLECTOR_SERVICE_URL}/events", params={"limit": 100})
                resp.raise_for_status()
            except Exception:
                resp = await client.get("http://127.0.0.1:8002/events", params={"limit": 100})
            resp.raise_for_status()
            events = resp.json() or []
            sys_events = [e for e in events if str(e.get("event_type")) == "system_metrics"]
            if not sys_events:
                return {
                    "available": False,
                    "message": "No system metrics available",
                }
            # Pick the most recent by timestamp
            latest = max(sys_events, key=lambda e: e.get("timestamp", ""))
            data = latest.get("data", {}) or {}
            summary = {
                "node_id": latest.get("node_id"),
                "timestamp": latest.get("timestamp"),
                "uptime": data.get("uptime"),
                "loadavg": data.get("loadavg"),
                "disk": data.get("disk"),
                "network": data.get("network"),
                "os_kernel": data.get("os_kernel"),
                # Trim large blobs for UI quick view
                "cpu_mem": (data.get("cpu_mem") or "")[:800],
                "processes_top": (data.get("processes_top") or "")[:800],
                "users": data.get("users"),
            }
            return {"available": True, "summary": summary}
    except Exception as e:
        logger.error(f"Error fetching system metrics: {e}")
        return {"available": False, "message": "Failed to fetch system metrics"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return {
        "api_requests_total": 0,  # TODO: Implement counter
        "api_requests_by_endpoint": {},  # TODO: Implement counter
        "api_response_time_seconds": 0.0  # TODO: Implement histogram
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

