import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TenantManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.tenants_dir = os.path.join(base_dir, "tenants")
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.load_all()

    def load_all(self):
        if not os.path.exists(self.tenants_dir):
            os.makedirs(self.tenants_dir, exist_ok=True)
            return

        for fname in os.listdir(self.tenants_dir):
            if fname.endswith(".json"):
                tenant_id = fname[:-5]
                fpath = os.path.join(self.tenants_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        self.cache[tenant_id] = json.load(f)
                except Exception as e:
                    logger.error(f"Error loading tenant {fname}: {e}")

    def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        return self.cache.get(tenant_id)

    def save_tenant(self, tenant_id: str, data: Dict[str, Any]) -> bool:
        """Saves a new shop or updates an existing shop dynamically in memory and JSON."""
        self.cache[tenant_id] = data
        try:
            os.makedirs(self.tenants_dir, exist_ok=True)
            fpath = os.path.join(self.tenants_dir, f"{tenant_id}.json")
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save tenant {tenant_id} to disk: {e}")
            return True  # Retained in memory cache even if serverless disk is read-only

tenant_manager = TenantManager()
