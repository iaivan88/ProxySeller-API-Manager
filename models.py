import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum, IntEnum

@dataclass
class APIResponse:
    """Standardized API response"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None

class ProxyFormat(IntEnum):
    LOGIN_PASS_HOST_PORT = 1
    LOGIN_PASS_COLON_HOST_PORT = 2
    HOST_PORT_LOGIN_PASS = 3
    HOST_PORT_AT_LOGIN_PASS = 4

class ExportFormat(Enum):
    TXT = "txt"
    CSV = "csv"
    JSON = "json"
