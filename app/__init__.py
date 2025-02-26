from flask import Flask
from app.config import configure_app
from app.routes import register_routes
from app.models import ModelCache
import warnings
warnings.simplefilter("ignore", category=FutureWarning)

def create_app():
    app = Flask(__name__)
    configure_app(app)
    register_routes(app)

    return app
