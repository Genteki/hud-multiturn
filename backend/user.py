"""User backend app"""

import sys
import logging
from fastapi import FastAPI
from .db import DB, DB_PATH

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
    db = DB.load(DB_PATH)
    db.reset()
    db.dump(DB_PATH)
    logger.info("State reset")
    return {"ok": True}


@app.post("/switch")
def switch():
    """Flip the value of `user_switch`."""
    db = DB.load(DB_PATH)
    db.user_switch = not db.user_switch
    db.dump(DB_PATH)
    logger.info(f"User switch flipped to {db.user_switch}")
    return {"ok": True, "message": "User switch flipped"}


@app.get("/check_status")
def check_status():
    """Check if the bulb is lighting. Bulb is on if both switches are True."""
    db = DB.load(DB_PATH)
    bulb_on = db.agent_switch and db.user_switch
    logger.info(f"Bulb status: {'ON' if bulb_on else 'OFF'}")
    return {"bulb_on": bulb_on, "message": f"The bulb is {'ON' if bulb_on else 'OFF'}"}

