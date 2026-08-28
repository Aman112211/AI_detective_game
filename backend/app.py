import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from routes.health import health_bp
from routes.chat import chat_bp
from routes.session import session_bp
from routes.submit import submit_bp


load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["ENVIRONMENT"] = os.getenv("FLASK_ENV", "development")
    app.config["JSON_SORT_KEYS"] = False

    CORS(app)
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(session_bp, url_prefix="/api")
    app.register_blueprint(submit_bp, url_prefix="/api")

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )