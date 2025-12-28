"""Agent backend app"""

import sys
import logging
from fastapi import FastAPI
from .db import shared_db, DB_PATH

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)
app = FastAPI(title="Agent Backend App")


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/reset")
def reset():
    """Reset the shared state."""
    shared_db.reset()
    shared_db.dump(DB_PATH)
    logger.info("State reset")
    return {"ok": True}


@app.post("/switch")
def switch():
    """Flip the value of `agent_switch`."""
    shared_db.agent_switch = not shared_db.agent_switch
    shared_db.dump(DB_PATH)
    logger.info(f"Agent switch flipped to {shared_db.agent_switch}")
    return {"ok": True, "message": "Agent switch flipped"}

@app.get("/state")
def state() -> bool:
    """Get the status of bulb"""
    return (shared_db.agent_switch and shared_db.user_switch)
