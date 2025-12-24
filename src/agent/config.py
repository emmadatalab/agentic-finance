"""Configuration loading and environment helpers for the agent."""

from dataclasses import dataclass, field
from pathlib import Path
import json
import os
from typing import Any, Dict


DEFAULT_CONFIG_PATH = Path(os.getenv("AGENT_CONFIG_PATH", "config.json"))


@dataclass
class AgentConfig:
    """Simple configuration container."""

    knowledge_base_path: Path = Path("data/knowledge_base")
    index_path: Path = Path("data/index")
    model_name: str = "gpt-placeholder"
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None = None) -> "AgentConfig":
        """Load configuration from JSON if it exists, otherwise return defaults."""
        config_path = path or DEFAULT_CONFIG_PATH
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            return cls(
                knowledge_base_path=Path(payload.get("knowledge_base_path", cls.knowledge_base_path)),
                index_path=Path(payload.get("index_path", cls.index_path)),
                model_name=payload.get("model_name", cls.model_name),
                extra=payload.get("extra", {}),
            )
        return cls()

    def to_json(self) -> str:
        """Serialize configuration to JSON string."""
        return json.dumps(
            {
                "knowledge_base_path": str(self.knowledge_base_path),
                "index_path": str(self.index_path),
                "model_name": self.model_name,
                "extra": self.extra,
            },
            indent=2,
        )
