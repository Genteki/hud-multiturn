"""User backend app"""

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
app = FastAPI(title="User Backend App")


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
    """Flip the value of `user_switch`."""
    shared_db.user_switch = not shared_db.user_switch
    shared_db.dump(DB_PATH)
    logger.info(f"User switch flipped to {shared_db.user_switch}")
    return {"ok": True, "message": "User switch flipped"}


@app.get("/check_status")
def check_status():
    """Check if the bulb is lighting. Bulb is on if both switches are True."""
    bulb_on = shared_db.agent_switch and shared_db.user_switch
    logger.info(f"Bulb status: {'ON' if bulb_on else 'OFF'}")
    return {"bulb_on": bulb_on, "message": f"The bulb is {'ON' if bulb_on else 'OFF'}"}

