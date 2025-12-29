# HUD Multi-turn Agent Loop Example

## Task Description

### Situation
In Alice's house, a **bulb** is controlled by `agent_switch` and `user_switch`. The bulb will be lit if and only if two switches are both `True`. 

Alice can flip the `user_switch` while the agent can flip `agent_switch`. However, they don't have access to the current value of switchess.

### Agent Tools
1. **switch**: Flip the value of `agent_switch`

### User Tools:
1. **switch**: Flip the value of `user_switch`
2. **check_status**: Check if the bulb is lighting

### Task
Agent is designed to help the user to control the status of bulb.


## Example Trace

```
Round 1:
🤖 Agent: Hi, how can i help you today?
👤 User: Hi! I'd like to turn on the bulb. Can you help me get both switches flipped so it comes on?

Round 2:
🤖 Agent: Of course! I'd be happy to help you turn on the bulb.
First, please check the current status of the bulb for me. Is it currently on or off?
👤 User: The bulb is currently OFF. What would you like me to do next?

Round 3:
🤖 → agent_switch()
✓ agent_switch flipped
🤖 Agent: Great! Now let's work on turning it on. Since the bulb is currently off, I'll start by flipping the agent switch on my end. Please check the bulb status after I do this.
👤 User: The bulb is still OFF. What should I do next - should I flip my switch on now?

Round 4:
🤖 Agent: Yes! Please flip your user switch on now, and then check the bulb status again.
👤 User: Now let me check the bulb status:

Round 5:
🤖 Agent: What is the bulb status now? Is it on or off?
👤 User: The bulb is currently ON! It looks like both our switches are working together perfectly. ###STOP###

Detected stop signal: ###STOP###
Conversation ended by user signal
```
