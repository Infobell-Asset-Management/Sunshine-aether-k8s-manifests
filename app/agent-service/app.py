from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import aio_pika
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Asset Agent Service", version="1.0.0")

# Configuration
RABBITMQ_HOST = os.getenv("MQ_HOST", "localhost") or "localhost"
RABBITMQ_PORT = int(os.getenv("MQ_PORT", "5672") or "5672")
RABBITMQ_USER = os.getenv("MQ_USER", "guest") or "guest"
RABBITMQ_PASS = os.getenv("MQ_PASSWORD", "guest") or "guest"
NODE_ID = os.getenv("NODE_ID", "unknown")

class AssetEvent(BaseModel):
    asset_id: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    node_id: str = NODE_ID

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    node_id: str

@app.get("/", response_model=Dict[str, str])
async def root():
    return {"msg": "Hello from Asset Agent Service", "node_id": NODE_ID}

@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        node_id=NODE_ID
    )

@app.post("/events")
async def collect_event(event: AssetEvent):
    """Collect asset events and send to RabbitMQ"""
    try:
        # Connect to RabbitMQ
        connection = await aio_pika.connect_robust(
            f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"
        )
        
        async with connection:
            channel = await connection.channel()
            
            # Declare queue
            queue = await channel.declare_queue("asset_events", durable=True)
            
            # Publish message
            message = aio_pika.Message(
                body=event.model_dump_json().encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            await channel.default_exchange.publish(message, routing_key="asset_events")
            logger.info(f"Event sent to RabbitMQ: {event.asset_id}")
            
        return {"status": "success", "message": "Event collected and queued"}
        
    except Exception as e:
        logger.error(f"Failed to send event to RabbitMQ: {e}")
        raise HTTPException(status_code=500, detail="Failed to process event")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return {
        "agent_events_collected_total": 0,  # TODO: Implement counter
        "agent_events_failed_total": 0,     # TODO: Implement counter
        "agent_rabbitmq_connection_status": 1  # TODO: Implement health check
    }

# ---------------------------
# Background system collectors
# ---------------------------

def _run(cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT, timeout=5)
    except Exception as e:
        return f"ERR: {e}"

def collect_system_snapshot() -> Dict[str, Any]:
    snapshot: Dict[str, Any] = {
        "cpu_mem": _run("COLUMNS=200 top -b -n1 | head -n 5"),
        "disk": _run("df -h"),
        "os_kernel": _run("uname -a"),
        "lsb_release": _run("lsb_release -a 2>/dev/null || cat /etc/os-release 2>/dev/null || echo 'N/A'"),
        "users": _run("who"),
        "processes_top": _run("ps -eo pid,comm,pcpu,pmem --sort=-pcpu | head -n 10"),
        "network": _run("ip -o -4 addr show || ifconfig 2>/dev/null"),
        "uptime": _run("uptime"),
        "loadavg": _run("cat /proc/loadavg"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "node_id": NODE_ID,
    }
    return snapshot

async def publish_system_snapshot():
    data = collect_system_snapshot()
    event = {
        "asset_id": f"system-{NODE_ID}",
        "event_type": "system_metrics",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": data,
        "node_id": NODE_ID,
    }

    try:
        connection = await aio_pika.connect_robust(
            f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"
        )
        async with connection:
            channel = await connection.channel()
            await channel.declare_queue("asset_events", durable=True)
            await channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(event).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
                routing_key="asset_events",
            )
            logger.info("Published system_metrics event")
    except Exception as e:
        logger.error(f"Failed to publish system snapshot: {e}")

async def periodic_system_publisher(interval_seconds: int = 3600):
    await asyncio.sleep(3)
    while True:
        await publish_system_snapshot()
        await asyncio.sleep(interval_seconds)

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(periodic_system_publisher(3600))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

