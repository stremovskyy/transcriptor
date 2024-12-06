from flask import Flask
from app.config import configure_app
from app.routes import register_routes
from app.models import ModelCache

def create_app():
    app = Flask(__name__)
    configure_app(app)
    register_routes(app)

    model_cache = ModelCache()
    model_cache.load_model('tiny')
    model_cache.load_model('base')

    return app
