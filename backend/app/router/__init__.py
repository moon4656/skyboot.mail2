# Router package

from .auth_router import router as auth_router
from .mail_core_router import router as mail_core_router
from .mail_convenience_router import router as mail_convenience_router
from .mail_advanced_router import router as mail_advanced_router

__all__ = [
    "auth_router",
    "mail_core_router", 
    "mail_convenience_router",
    "mail_advanced_router"
]