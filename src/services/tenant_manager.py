import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TenantManager:
    def __init__(self, tenants_dir: str = "tenants"):
        self.tenants_dir = tenants_dir
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
                        logger.info(f"Loaded tenant config: {tenant_id}")
                except Exception as e:
                    logger.error(f"Error loading tenant {fname}: {e}")

    def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        return self.cache.get(tenant_id)

tenant_manager = TenantManager()
