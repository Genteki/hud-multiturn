export AGENT_BACKEND_PORT=8001
export USER_BACKEND_PORT=8002
uvicorn backend.user:app --host 0.0.0.0 --port $USER_BACKEND_PORT --log-level warning