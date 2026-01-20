import hud
from hud.agents import create_agent
from hud.datasets import load_tasks
from prompts import AGENT_INSTRUCTION, USER_INSTRUCTION
from loop import multi_turn_run
import asyncio

async def main():
    ds = "multiturn-test"
    model = "claude-haiku-4-5"
    tasks = load_tasks(ds)
    
    async with hud.eval(tasks, max_concurrent=10) as ctx:
        assistant = create_agent(
            model= model, 
            system_prompt=AGENT_INSTRUCTION,
            allowed_tools=["agent_switch"]
        )
        user = create_agent(
            model=model, 
            system_prompt=USER_INSTRUCTION,
            allowed_tools=["user_switch", "check_status"]
        )
        await multi_turn_run(ctx=ctx, agent=assistant, simulated_user=user, max_steps=10)

if __name__ == "__main__":
    asyncio.run(main())

