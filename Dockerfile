FROM python:3.12-slim
WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install hud-python from feature branch
# RUN pip install -e git+https://github.com/Genteki/hud-python.git@Feature--multi-turn-agent-loop#egg=hud-python

# Install project dependencies
COPY pyproject.toml ./
RUN pip install .

# Copy source code
COPY . .

ENV AGENT_BACKEND_PORT=8001
ENV USER_BACKEND_PORT=8002

# Start both backend apps, then run mcp server
CMD ["sh", "-c", "uvicorn backend.agent:app --host 0.0.0.0 --port $AGENT_BACKEND_PORT --log-level warning >&2 & uvicorn backend.user:app --host 0.0.0.0 --port $USER_BACKEND_PORT --log-level warning >&2 & sleep 0.5 && python env.py"]
