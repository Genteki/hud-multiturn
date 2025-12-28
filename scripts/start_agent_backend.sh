export AGENT_BACKEND_PORT=8001
export USER_BACKEND_PORT=8002
uvicorn backend.agent:app --host 0.0.0.0 --port $AGENT_BACKEND_PORT --log-level warning