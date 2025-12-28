"""Multi-turn agent interaction framework.

Provides utilities for running multi-turn conversations between an agent and a simulated user.
"""

import asyncio
import logging
from typing import Any

from hud.eval.context import EvalContext
from hud.types import Trace

logger = logging.getLogger(__name__)


async def multi_turn_run(
    ctx: EvalContext,
    agent: Any,  # MCPAgent instance
    simulated_user: Any,  # MCPAgent instance for user simulation
    max_steps: int = 30,
) -> Trace:
    """
    Run agent with multi-turn conversation loop.

    Drop-in replacement for `await agent.run(ctx)` that enables turn-based
    conversation between agent and simulated user.

    Args:
        ctx: EvalContext from hud.eval()
        agent: The main agent (MCPAgent) trying to complete the task
        simulated_user: A simulated user agent (MCPAgent) that responds
        max_steps: Maximum number of agent steps (not turns)

    Returns:
        Trace: The final trace from execution

    Example:
        ```python
        from hud.agents.openai_chat import OpenAIChatAgent
        from multi_turn import multi_turn_run
        from prompts import AGENT_INSTRUCTION, USER_INSTRUCTION

        agent = OpenAIChatAgent.create(
            model="gpt-5",
            system_prompt=AGENT_INSTRUCTION
        )
        user = OpenAIChatAgent.create(
            model="gpt-4o-mini",
            system_prompt=USER_INSTRUCTION
        )

        task = env("bulb")
        async with hud.eval(task) as ctx:
            # Instead of: await agent.run(ctx)
            await multi_turn_run(ctx, agent, user, max_steps=30)
        ```
    """
    from hud.agents.base import text_to_blocks

    if not isinstance(ctx, EvalContext):
        raise TypeError(f"ctx must be EvalContext, got {type(ctx).__name__}")

    if not ctx.prompt:
        raise ValueError("ctx.prompt is not set - did the scenario setup run?")

    # Store context for tool calls
    agent.ctx = ctx
    simulated_user.ctx = ctx

    # Initialize tools from context
    if not agent._initialized:
        await agent._initialize_from_ctx(ctx)
        # Filter tools for agent if allowed_tools is set
        if hasattr(agent.config, 'allowed_tools') and agent.config.allowed_tools:
            agent._available_tools = [
                t for t in agent._available_tools
                if t.name in agent.config.allowed_tools
            ]
            agent._tool_map = {t.name: t for t in agent._available_tools}
            agent.console.info(
                f"Filtered to {len(agent._available_tools)} allowed tools: "
                f"{', '.join([t.name for t in agent._available_tools])}"
            )
            agent._on_tools_ready()  # Rebuild provider-specific tool formats

    if not simulated_user._initialized:
        await simulated_user._initialize_from_ctx(ctx)
        # Filter tools for user if allowed_tools is set
        if hasattr(simulated_user.config, 'allowed_tools') and simulated_user.config.allowed_tools:
            simulated_user._available_tools = [
                t for t in simulated_user._available_tools
                if t.name in simulated_user.config.allowed_tools
            ]
            simulated_user._tool_map = {t.name: t for t in simulated_user._available_tools}
            simulated_user.console.info(
                f"Filtered to {len(simulated_user._available_tools)} allowed tools: "
                f"{', '.join([t.name for t in simulated_user._available_tools])}"
            )
            simulated_user._on_tools_ready()  # Rebuild provider-specific tool formats

    try:
        # Run custom conversation loop
        result = await _run_conversation_loop(
            agent, simulated_user, text_to_blocks(ctx.prompt), max_steps=max_steps
        )

        # Submit final answer to context (only if scenario is running)
        if result.content and ctx.has_scenario:
            await ctx.submit(result.content)

        return result

    except Exception as e:
        logger.exception("Error while running multi-turn agent:")
        return Trace(
            reward=0.0,
            done=True,
            content=f"Agent failed with error: {e}",
            isError=True,
            info={"error": str(e)},
        )
    finally:
        # Cleanup auto-created resources
        await agent._cleanup()
        await simulated_user._cleanup()


async def _run_conversation_loop(
    agent: Any,
    simulated_user: Any,
    context: list[Any],
    *,
    max_steps: int = 30,
) -> Trace:
    """
    Core conversation loop with turn-based interaction.

    This implements a turn-based conversation:
    1. Agent acts (tool calls and/or message)
    2. When agent sends a message, user simulator responds
    3. User response is added to messages, loop continues
    4. Stops when max_steps reached or conversation naturally ends
    """
    final_response = None
    error = None
    messages: list[Any] = []

    # Stop signal detection
    STOP_SIGNAL = "###STOP###"

    def check_for_stop_signal(text: str) -> bool:
        """Check if text contains the conversation stop signal."""
        if STOP_SIGNAL in text:
            logger.info(f"Detected stop signal: {STOP_SIGNAL}")
            return True
        return False

    async def get_user_response(agent_message: str) -> str:
        """Get simulated user response to agent's message."""
        try:
            # Run user agent with agent's message as prompt
            user_prompt = f"The assistant said: {agent_message}\n\nRespond as a user."
            user_messages = await simulated_user.get_system_messages()
            user_messages.extend(await simulated_user.format_message(user_prompt))

            # User can call tools and respond (limit to 2 iterations)
            max_user_iterations = 2
            for _ in range(max_user_iterations):
                user_response_obj = await simulated_user.get_response(user_messages)

                # If user has tool calls, execute them
                if user_response_obj.tool_calls:
                    logger.info(f"User executing {len(user_response_obj.tool_calls)} tool(s)")
                    user_tool_results = await simulated_user.call_tools(user_response_obj.tool_calls)

                    # Add user's tool call message if any content
                    if user_response_obj.content:
                        user_messages.extend(await simulated_user.format_message(user_response_obj.content))

                    # Format tool results and add to messages
                    tool_messages = await simulated_user.format_tool_results(
                        user_response_obj.tool_calls, user_tool_results
                    )
                    user_messages.extend(tool_messages)

                    # Continue to get text response after tools
                    continue
                else:
                    # No tool calls - user has a text response
                    return user_response_obj.content or "Okay."

            # Max iterations reached - return last content
            return user_response_obj.content or "Okay."

        except asyncio.TimeoutError:
            logger.error("User response timed out")
            return "Sorry, I took too long to respond."
        except Exception as e:
            logger.error(f"Failed to get user response: {e}")
            import traceback
            traceback.print_exc()
            return f"Error getting user response: {e}"

    try:
        # Start with system messages
        messages = await agent.get_system_messages()

        # Add initial context
        messages.extend(await agent.format_message(context))
        agent.console.debug(f"Messages: {messages}")

        step_count = 0
        while max_steps == -1 or step_count < max_steps:
            step_count += 1
            agent.console.debug(f"Step {step_count}/{max_steps if max_steps != -1 else 'unlimited'}")

            try:
                # 1. Get agent response
                response = await agent.get_response(messages)
                agent.console.debug(f"Agent:\n{response}")

                # 2. Check if agent has tool calls
                if response.tool_calls:
                    # Execute agent tools
                    tool_calls = response.tool_calls
                    tool_results = await agent.call_tools(tool_calls)

                    # Add agent's tool call message to history
                    # OpenAI Chat requires the assistant message with tool calls
                    if response.content:
                        messages.extend(await agent.format_message(response.content))

                    # Format tool results and add to messages
                    tool_messages = await agent.format_tool_results(tool_calls, tool_results)
                    messages.extend(tool_messages)

                    # Display
                    step_info = f"\n[bold]Step {step_count}/{max_steps if max_steps != -1 else '∞'}[/bold]"
                    for call, result in zip(tool_calls, tool_results, strict=False):
                        step_info += f"\n🤖 {call}\n{result}"
                    agent.console.info_log(step_info)

                    # Check if agent also sent a message (conversation turn)
                    if response.content:
                        agent_message = response.content
                        agent.console.info(f"[bold cyan]🤖 Agent:[/bold cyan] {agent_message}")

                        # Get user response
                        user_response = await get_user_response(agent_message)
                        agent.console.info(f"[bold green]👤 User:[/bold green] {user_response}")

                        # Check for stop signal in user response
                        if check_for_stop_signal(user_response):
                            agent.console.info("Conversation ended by user signal")
                            final_response = response
                            break

                        # Add user response to messages
                        messages.extend(await agent.format_message(user_response))

                else:
                    # No tool calls - agent sent message to user
                    agent_message = response.content or ""

                    if not agent_message:
                        # Agent provided empty response
                        agent.console.warning("Agent provided empty response, ending")
                        final_response = response
                        break

                    agent.console.info(f"[bold cyan]🤖 Agent:[/bold cyan] {agent_message}")

                    # Add agent message to history (format as string, not AgentResponse)
                    messages.extend(await agent.format_message(agent_message))

                    # Get user response
                    user_response = await get_user_response(agent_message)
                    agent.console.info(f"[bold green]👤 User:[/bold green] {user_response}")

                    # Check for stop signal in user response
                    if check_for_stop_signal(user_response):
                        agent.console.info("Conversation ended by user signal")
                        final_response = response
                        break

                    # Add user response to messages and continue
                    messages.extend(await agent.format_message(user_response))

            except Exception as e:
                agent.console.error_log(f"Step failed: {e}")
                error = str(e)
                break

    except KeyboardInterrupt:
        agent.console.warning_log("Agent execution interrupted by user")
        error = "Interrupted by user"
    except asyncio.CancelledError:
        agent.console.warning_log("Agent execution cancelled")
        error = "Cancelled"
    except Exception as e:
        agent.console.error_log(f"Unexpected error: {e}")
        error = str(e)

    # Build result
    is_error = error is not None or (
        final_response and hasattr(final_response, "isError") and final_response.isError
    )

    trace_params = {
        "reward": 0.0,
        "done": True,
        "messages": messages,
        "content": final_response.content if final_response else (error or "Conversation ended"),
        "isError": is_error,
        "info": {"error": error} if error else {},
    }
    trace_result = Trace(**trace_params)

    return trace_result
