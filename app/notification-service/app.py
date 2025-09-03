import logging
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="notification-service", version="1.0.0")

K8S_API = os.getenv("K8S_API", "https://kubernetes.default.svc")
NAMESPACE = os.getenv("TARGET_NAMESPACE", "assettrack")
DEPLOYMENT = os.getenv("TARGET_DEPLOYMENT", "processor")

async def scale_deployment(namespace: str, name: str, replicas: int) -> None:
    # Use in-cluster service account; no cert validation tweaks here for brevity
    url = f"{K8S_API}/apis/apps/v1/namespaces/{namespace}/deployments/{name}/scale"
    async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
        payload = {"spec": {"replicas": replicas}}
        headers = {"Content-Type": "application/json"}
        # Rely on in-cluster auth token
        try:
            with open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r") as f:
                token = f.read().strip()
                headers["Authorization"] = f"Bearer {token}"
        except Exception:
            logger.warning("Could not read in-cluster token; scale call will likely fail")
        resp = await client.put(url, json=payload, headers=headers)
        resp.raise_for_status()

@app.post("/alert")
async def receive_alert(request: Request):
    body = await request.json()
    logger.info(f"Alert received: {body}")
    # Minimal filter: scale down on critical DB errors
    try:
        alerts = body.get("alerts", [])
        for a in alerts:
            if a.get("labels", {}).get("severity") == "critical":
                await scale_deployment(NAMESPACE, DEPLOYMENT, 0)
                return JSONResponse({"status": "scaled", "replicas": 0})
    except Exception as e:
        logger.error(f"Failed to process alert: {e}")
        return JSONResponse({"status": "error", "error": str(e)}, status_code=500)
    return {"status": "ignored"}


