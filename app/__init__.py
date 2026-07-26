"""
Royal Brothers Fitness Gym - Flask Application Factory
Builds and configures the Flask app: config, Flask-Mail, blueprints,
and static frontend serving.

The actual server entry point is wsgi.py at the project root, which
imports create_app() from here. This split (factory in a package,
thin entry point at the root) is the standard Flask production layout
and is what Render/Railway/Gunicorn expect.
"""

import os

from flask import Flask, send_from_directory
from flask_mail import Mail

from .config import Config
from .routes.auth_routes import auth_bp
from .routes.membership_routes import membership_bp
from .routes.contact_routes import contact_bp
from .routes.admin_routes import admin_bp

# Flask-Mail instance, shared by any route module that needs to send
# email (imported lazily inside functions as `from .. import mail` to
# avoid circular imports with the blueprints above).
mail = Mail()


def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="",
    )

    # Load Config (reads environment variables; raises a clear error at
    # startup if a required secret is missing -- see app/config.py)
    app.config.from_object(Config)

    # Initialize Flask-Mail
    mail.init_app(app)

    # Register API blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(membership_bp, url_prefix="/api/membership")
    app.register_blueprint(contact_bp, url_prefix="/api/contact")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    # Home page
    @app.route("/")
    def serve_index():
        return send_from_directory(app.static_folder, "index.html")

    # Serve HTML/CSS/JS/image files (multi-page frontend, no templating)
    @app.route("/<path:filename>")
    def serve_frontend_files(filename):
        return send_from_directory(app.static_folder, filename)

    return app
