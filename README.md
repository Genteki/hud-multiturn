# HUD Multi-turn Agent Loop Example

## Task Description

### Situation
In Alice's house, a **bulb** is controlled by `agent_switch` and `user_switch`. The bulb will be lighted if and only if two switches are both `True`. 

Alice can flip the `user_switch` while the agent can flip `agent_switch`. However, they don't have access to the current value of switchess.

### Agent Tools
1. **switch**: Flip the value of `agent_switch`

### User Tools:
1. **switch**: Flip the value of `user_switch`
2. **check_status**: Check if the bulb is lighting

### Task
Agent is designed to help the user to control the status of bulb.

