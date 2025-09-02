from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import aio_pika
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Asset Collector Service", version="1.0.0")

# Configuration
RABBITMQ_HOST = os.getenv("MQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("MQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("MQ_USER", "guest")
RABBITMQ_PASS = os.getenv("MQ_PASSWORD", "guest")

class AssetEvent(BaseModel):
    asset_id: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    node_id: str

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    queue_status: str

from typing import Optional
class EventStats(BaseModel):
    total_events_processed: int
    events_by_type: Dict[str, int]
    last_processed: Optional[datetime] = None

# In-memory storage for demo (replace with database in production)
processed_events: List[AssetEvent] = []
event_stats = {
    "total_events_processed": 0,
    "events_by_type": {},
    "last_processed": None
}

@app.get("/", response_model=Dict[str, str])
async def root():
    return {"msg": "Hello from Asset Collector Service"}

@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        queue_status="connected"  # TODO: Implement actual queue health check
    )

@app.get("/stats", response_model=EventStats)
async def get_stats():
    return EventStats(
        total_events_processed=event_stats["total_events_processed"],
        events_by_type=event_stats["events_by_type"],
        last_processed=event_stats["last_processed"]
    )

@app.get("/events", response_model=List[AssetEvent])
async def get_events(limit: int = 100):
    """Get recent processed events"""
    return processed_events[-limit:]

async def process_message(message: aio_pika.IncomingMessage):
    """Process incoming RabbitMQ messages"""
    async with message.process():
        try:
            # Parse message body
            body = json.loads(message.body.decode())
            event = AssetEvent(**body)
            
            # Store event
            processed_events.append(event)
            if len(processed_events) > 1000:  # Keep only last 1000 events
                processed_events.pop(0)
            
            # Update stats
            event_stats["total_events_processed"] += 1
            event_stats["events_by_type"][event.event_type] = event_stats["events_by_type"].get(event.event_type, 0) + 1
            event_stats["last_processed"] = datetime.utcnow()
            
            logger.info(f"Processed event: {event.asset_id} - {event.event_type}")
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")

async def start_consumer():
    """Start RabbitMQ consumer"""
    try:
        # Connect to RabbitMQ
        connection = await aio_pika.connect_robust(
            f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"
        )
        
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        
        # Declare queue
        queue = await channel.declare_queue("asset_events", durable=True)
        
        # Start consuming
        await queue.consume(process_message)
        logger.info("Started consuming messages from asset_events queue")
        
        return connection
        
    except Exception as e:
        logger.error(f"Failed to start consumer: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Start RabbitMQ consumer on startup"""
    app.state.rabbitmq_connection = await start_consumer()

@app.on_event("shutdown")
async def shutdown_event():
    """Close RabbitMQ connection on shutdown"""
    if hasattr(app.state, 'rabbitmq_connection'):
        await app.state.rabbitmq_connection.close()

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return {
        "collector_events_processed_total": event_stats["total_events_processed"],
        "collector_events_by_type": event_stats["events_by_type"],
        "collector_queue_connection_status": 1  # TODO: Implement health check
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

