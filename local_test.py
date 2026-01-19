"""Local test script for the blank environment.

Run the backend first: uvicorn backend.app:app --port 8005
Then run this script: python local_test.py
"""

import os
import asyncio
import hud
from openai import AsyncOpenAI
from hud.agents import OpenAIChatAgent, multi_turn_run, create_agent

from env import env

# Use HUD inference gateway - see all models at https://hud.ai/models
api_key = os.getenv("HUD_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    from hud.settings import settings
    api_key = settings.api_key

client = AsyncOpenAI(base_url="https://inference.hud.ai", api_key=api_key) if api_key else None

async def test_tools_standalone():
    """Test environment tools directly."""
    print("=== Test 1: Standalone Tools ===")

    async with env:
        print(f"Tools: {[t.name for t in env.as_tools()]}")

async def test_scenario_agent():
    """Test scenario with OpenAIChatAgent."""
    print("\n=== Test 2: Scenario (Agent) ===")
    if not client:
        print("Skipping: API key not set. Set HUD_API_KEY or OPENAI_API_KEY environment variable.")
        return
    bound_tasks = [env("bulb")]
    async with hud.eval(bound_tasks) as ctx:
        agent = OpenAIChatAgent.create(model="gpt-5")
        # await agent.run(ctx, max_steps=30)


async def test_multi_turn():
    """Test multi-turn agent interaction."""
    print("\n=== Test 3: Multi-Turn Agent Loop ===")
    if not client:
        print("Skipping: API key not set. Set HUD_API_KEY or OPENAI_API_KEY environment variable.")
        return

    from prompts import AGENT_INSTRUCTION, USER_INSTRUCTION

    # Create agent with butler instructions
    # Agent can only use 'switch' tool (for agent_switch)
    agent = create_agent(
        model="claude-haiku-4-5", 
        system_prompt=AGENT_INSTRUCTION,
        allowed_tools=["agent_switch"]
    )
    user = create_agent(
        model="claude-haiku-4-5", 
        system_prompt=USER_INSTRUCTION,
        allowed_tools=["user_switch", "check_status"]
    )
    task = env("bulb")

    async with hud.eval(task) as ctx:
        # Instead of: await agent.run(ctx, max_steps=30)
        await multi_turn_run(ctx, agent, user, max_steps=10)

        print(f"\nReward: {ctx.reward}")
        print(f"Success: {ctx.success}")


async def main():
    await test_tools_standalone()
    # await test_scenario_agent()
    await test_multi_turn()


if __name__ == "__main__":
    asyncio.run(main())