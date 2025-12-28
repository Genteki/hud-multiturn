"""Multi-turn agent interaction framework.

Provides utilities for running multi-turn conversations between an agent and a simulated user.
"""

import logging
from typing import Any

from hud.eval.context import EvalContext
from hud.types import Trace

logger = logging.getLogger(__name__)


async def multi_turn_run(
    ctx: EvalContext,
    agent: Any,  # Agent with run() method
    simulated_user: Any,  # Agent with run() method
    max_turns: int = 10,
) -> Trace:
    """
    Run a multi-turn conversation between an agent and a simulated user.

    Drop-in replacement for `await agent.run(ctx)` that enables multi-turn interaction.

    Args:
        ctx: EvalContext from hud.eval()
        agent: The main agent trying to complete the task
        simulated_user: A simulated user agent that responds to the agent
        max_turns: Maximum number of conversation turns

    Returns:
        Trace: The final trace from the agent's execution

    Example:
        ```python
        from hud.agents.openai_chat import OpenAIChatAgent
        from multi_turn import multi_turn_run

        agent = OpenAIChatAgent.create(model="gpt-5")
        user = OpenAIChatAgent.create(model="gpt-4o-mini")

        task = env("bulb")
        async with hud.eval(task) as ctx:
            # Instead of: await agent.run(ctx)
            await multi_turn_run(ctx, agent, user, max_turns=5)
        ```
    """
    logger.info(f"Starting multi-turn conversation (max {max_turns} turns)")

    # Store original prompt for agent
    original_prompt = ctx.prompt
    final_trace = None

    for turn in range(max_turns):
        logger.info(f"Turn {turn + 1}/{max_turns}")

        print(f"\n{'='*60}")
        print(f"TURN {turn + 1}/{max_turns}")
        print(f"{'='*60}")

        # Agent's turn
        print(f"\n🤖 Agent's turn...")
        agent_trace = await agent.run(ctx, max_steps=3)
        final_trace = agent_trace

        agent_message = agent_trace.content
        if not agent_message:
            logger.warning("Agent provided no message")
            break

        print(f"🤖 Agent: {agent_message[:200]}")

        # Check if done
        if agent_trace.done:
            logger.info("Agent indicates done")
            break

        # User's turn - update ctx.prompt to agent's message
        print(f"\n👤 User's turn...")
        ctx.prompt = f"The assistant said: {agent_message}\n\nRespond as a user."

        user_trace = await simulated_user.run(ctx, max_steps=2)
        user_message = user_trace.content

        if not user_message:
            logger.warning("User provided no message")
            break

        print(f"👤 User: {user_message[:200]}")

        # Update ctx.prompt for next agent turn
        ctx.prompt = user_message

    else:
        logger.warning(f"Reached maximum turns ({max_turns})")
        print(f"\n⚠️ Reached max turns")

    # Restore original prompt
    ctx.prompt = original_prompt

    logger.info(f"Multi-turn ended. Reward: {ctx.reward}")
    return final_trace or Trace(done=True, content="", reward=0.0)
