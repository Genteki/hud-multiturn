import logging
import sys
import os
import httpx
from typing import Any

from hud import Environment

from prompts import AGENT_INSTRUCTION

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s | %(name)s | %(message)s",
    force=True,
)
for logger_name in ["httpx", "httpcore"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)
    
logger = logging.getLogger(__name__)

AGENT_BACKEND_PORT = os.getenv("AGENT_BACKEND_PORT", "8001")
USER_BACKEND_PORT = os.getenv("USER_BACKEND_PORT", "8002")
AGENT_BACKEND_URL = f"http://localhost:{AGENT_BACKEND_PORT}"
USER_BACKEND_URL = f"http://localhost:{USER_BACKEND_PORT}"

agent_client = httpx.AsyncClient(base_url=AGENT_BACKEND_URL, timeout=10.0)
user_client = httpx.AsyncClient(base_url=USER_BACKEND_URL, timeout=10.0)

env = Environment(name="multi-turn")

@env.tool()
async def switch() -> str:
    """Flip agent switch"""
    response = await agent_client.post("/switch")
    return "agent_switch flipped"

@env.tool()
async def user_switch() -> str:
    """Flip user switch"""
    response = await user_client.post("/switch")
    return "user_switch flipped"

@env.tool()
async def check_status() -> str:
    """Check if the bulb is currently lighting. Returns whether bulb is ON or OFF."""
    response = await user_client.get("/check_status")
    response.raise_for_status()

    # Check if response has content
    if not response.content:
        logger.error("check_status: Empty response from user backend")
        return "Error: Unable to check bulb status"

    result = response.json()
    bulb_on = result.get("bulb_on", False)
    return f"The bulb is {'ON' if bulb_on else 'OFF'}"
    
@env.initialize
async def init() -> None:
    """Init"""
    (await agent_client.get("/health")).raise_for_status()
    (await user_client.get("/health")).raise_for_status()
    
@env.shutdown
async def cleanup() -> None:
    """Close HTTP client on shutdown."""
    await agent_client.aclose()
    await user_client.aclose()
    
@env.scenario("bulb")
async def bulb() -> Any:
    """Bulb control scenario"""
    await agent_client.post("/reset")
    
    _ = yield AGENT_INSTRUCTION

    response = await agent_client.get("/state")
    current = response.json()

    yield int(current)


if __name__ == "__main__":
    env.run(transport="stdio")