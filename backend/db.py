import json
from pydantic import BaseModel, ConfigDict, Field
from pathlib import Path
from typing import Any


class DB(BaseModel):
    """Database model for bulb control environment."""

    model_config = ConfigDict(extra="forbid")

    agent_switch: bool = Field(default=False, description="Agent-controlled switch state")
    user_switch: bool = Field(default=False, description="User-controlled switch state")

    @classmethod
    def load(cls, path: str | Path) -> "DB":
        """Load the database from a structured file like JSON, YAML, or TOML."""
        path = Path(path)
        if not path.exists():
            return cls()
        if path.suffix == ".json":
            with open(path, "r") as fp:
                data = json.load(fp)
        else:
            raise ValueError(f"Unsupported file extension: {path}")
        return cls.model_validate(data)

    def dump(self, path: str | Path) -> None:
        """Dump the database to a file."""
        path = Path(path)
        data = self.model_dump(exclude_defaults=False)
        if path.suffix == ".json":
            with open(path, "w") as fp:
                json.dump(data, fp, indent=2)
        else:
            raise ValueError(f"Unsupported file extension: {path}")

    def get_json_schema(self) -> dict[str, Any]:
        """Get the JSON schema of the database."""
        return self.model_json_schema()

    def reset(self) -> None:
        """Reset both switches to False."""
        self.agent_switch = False
        self.user_switch = False


# Shared DB
DB_PATH = Path(__file__).parent / "db.json"
shared_db = DB.load(DB_PATH)

