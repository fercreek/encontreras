import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class ContextLoader:
    """
    Handles loading client-specific context (voice, tone, business rules)
    from the storage/clients directory.
    """
    def __init__(self, base_path: str = "storage/clients"):
        self.base_path = Path(base_path)

    def get_client_path(self, client_id: str) -> Path:
        return self.base_path / client_id

    def load_context(self, client_id: str) -> Dict[str, Any]:
        """
        Loads the context.md or context.yaml for a specific client.
        """
        client_dir = self.get_client_path(client_id)
        context_file = client_dir / "context.md"
        
        if not context_file.exists():
            return {"error": f"Client {client_id} not found or has no context.md"}

        # For now, we return the raw content of the markdown file.
        # In a more advanced version, we could parse YAML frontmatter.
        with open(context_file, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "client_id": client_id,
            "content": content,
            "status": "loaded"
        }

    def list_clients(self) -> list:
        if not self.base_path.exists():
            return []
        return [d.name for d in self.base_path.iterdir() if d.is_dir()]

# Example usage:
# loader = ContextLoader()
# context = loader.load_context("demo-academy")
