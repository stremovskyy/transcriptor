from app import create_app
from app.managers import ConfigManager

if __name__ == '__main__':
    app = create_app()

    app.run(
        debug=ConfigManager.get_env('FLASK_ENV') == 'development',
        host=ConfigManager.get_env('FLASK_HOST', 'localhost'),
        port=int(ConfigManager.get_env('FLASK_PORT', 8080)),
    )
