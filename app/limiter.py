from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def init_limiter(app):
    return Limiter(
        get_remote_address,
        app=app,
        default_limits=["10000 per hour", "30 per second"],
        storage_uri="memory://",
    )
