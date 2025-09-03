import logging
import sys
import os
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime
import uvicorn
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor, Json

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

DATABASE_URL = os.getenv("DATABASE_URL", "")
db_pool: Optional[SimpleConnectionPool] = None

def initialize_database_pool() -> None:
    global db_pool
    if not DATABASE_URL:
        logger.warning("DATABASE_URL is not set. The processor will run without persistence.")
        return
    if db_pool is None:
        db_pool = SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=DATABASE_URL,
        )
        logger.info("Initialized PostgreSQL connection pool")

def with_connection():
    class _ConnCtx:
        def __enter__(self):
            if db_pool is None:
                return None
            self.conn = db_pool.getconn()
            return self.conn

        def __exit__(self, exc_type, exc, tb):
            if db_pool is not None:
                db_pool.putconn(self.conn)
    return _ConnCtx()

def ensure_schema() -> None:
    if db_pool is None:
        return
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS assets (
        id UUID PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        location TEXT NOT NULL,
        status TEXT NOT NULL,
        last_updated TIMESTAMPTZ NOT NULL,
        metadata JSONB NOT NULL DEFAULT '{}'::jsonb
    );
    """
    with with_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(create_table_sql)
            conn.commit()
    logger.info("Ensured assets table exists")

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict] = None

@app.get("/assets", response_model=List[Asset])
async def list_assets(request: Request):
    logger.info(f"GET /assets called from {request.client.host}")
    if db_pool is None:
        # fallback to transient empty list when DB not configured
        logger.warning("DATABASE_URL not set, returning in-memory empty list")
        return []
    with with_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id::text, name, type, location, status, last_updated, metadata FROM assets ORDER BY last_updated DESC")
            rows = cur.fetchall()
            # Convert to standard dict list
            return [
                {
                    **row,
                    "last_updated": row["last_updated"].isoformat().replace("+00:00", "Z") if row.get("last_updated") else datetime.utcnow().isoformat() + "Z",
                }
                for row in rows
            ]

@app.post("/assets", response_model=Asset)
def create_asset(asset: AssetCreate):
    asset_id = str(uuid4())
    asset_data = asset.dict()
    if asset_data.get('metadata') is None:
        asset_data['metadata'] = {}
    now = datetime.utcnow()
    if db_pool is None:
        # transient non-persistent fallback
        created = Asset(id=asset_id, last_updated=now, status="active", **asset_data)
        logger.info("Created asset without persistence (no DATABASE_URL)")
        return created
    with with_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO assets (id, name, type, location, status, last_updated, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    asset_id,
                    asset_data["name"],
                    asset_data["type"],
                    asset_data["location"],
                    "active",
                    now,
                    Json(asset_data["metadata"]),
                ),
            )
            conn.commit()
    created = Asset(id=asset_id, last_updated=now, status="active", **asset_data)
    logger.info(f"Created new asset: {created}")
    return created

@app.get("/assets/{asset_id}", response_model=Asset)
def get_asset(asset_id: str):
    if db_pool is None:
        logger.warning("DATABASE_URL not set; cannot retrieve specific asset")
        return JSONResponse(status_code=404, content={"detail": "Asset not found"})
    with with_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id::text, name, type, location, status, last_updated, metadata FROM assets WHERE id = %s",
                (asset_id,),
            )
            row = cur.fetchone()
            if not row:
                logger.warning(f"Asset not found: {asset_id}")
                return JSONResponse(status_code=404, content={"detail": "Asset not found"})
            row["last_updated"] = row["last_updated"].isoformat().replace("+00:00", "Z") if row.get("last_updated") else datetime.utcnow().isoformat() + "Z"
            return row

@app.put("/assets/{asset_id}", response_model=Asset)
def update_asset(asset_id: str, update: AssetUpdate):
    logger.info(f"PUT /assets/{asset_id} called")
    update_data = update.dict(exclude_unset=True)
    now = datetime.utcnow()
    if db_pool is None:
        logger.warning("DATABASE_URL not set; cannot update asset")
        return JSONResponse(status_code=404, content={"detail": "Asset not found"})
    with with_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Ensure asset exists
            cur.execute("SELECT 1 FROM assets WHERE id = %s", (asset_id,))
            if cur.fetchone() is None:
                logger.warning(f"Asset not found: {asset_id}")
                return JSONResponse(status_code=404, content={"detail": "Asset not found"})
            # Build dynamic update
            sets = []
            values = []
            for field in ["name", "type", "location", "status", "metadata"]:
                if field in update_data and update_data[field] is not None:
                    sets.append(f"{field} = %s")
                    values.append(Json(update_data[field]) if field == "metadata" else update_data[field])
            sets.append("last_updated = %s")
            values.append(now)
            values.append(asset_id)
            sql = f"UPDATE assets SET {', '.join(sets)} WHERE id = %s"
            cur.execute(sql, tuple(values))
            conn.commit()
            # Return updated row
            cur.execute(
                "SELECT id::text, name, type, location, status, last_updated, metadata FROM assets WHERE id = %s",
                (asset_id,),
            )
            row = cur.fetchone()
            row["last_updated"] = row["last_updated"].isoformat().replace("+00:00", "Z") if row.get("last_updated") else now.isoformat() + "Z"
            logger.info(f"Asset updated: {asset_id}")
            return row

@app.delete("/assets/{asset_id}")
def delete_asset(asset_id: str):
    logger.info(f"DELETE /assets/{asset_id} called")
    if db_pool is None:
        logger.warning("DATABASE_URL not set; cannot delete asset")
        return JSONResponse(status_code=404, content={"detail": "Asset not found"})
    with with_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM assets WHERE id = %s", (asset_id,))
            if cur.rowcount == 0:
                logger.warning(f"Asset not found: {asset_id}")
                return JSONResponse(status_code=404, content={"detail": "Asset not found"})
            conn.commit()
    logger.info(f"Asset deleted: {asset_id}")
    return {"message": "Asset deleted successfully"}

@app.get("/healthz", response_class=PlainTextResponse)
async def healthz():
    logger.info("Health check called")
    try:
        # Test database connection if configured
        if DATABASE_URL:
            initialize_database_pool()
            ensure_schema()
        return "ok"
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return Response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content="service unavailable"
        )

@app.on_event("startup")
async def on_startup():
    try:
        if DATABASE_URL:
            initialize_database_pool()
            ensure_schema()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

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