from flask import Flask
from .extensions import db, jwt, migrate
from .config import Config
from .auth.routes import bp as auth_bp
from .catalog.routes import bp as catalog_bp
from .inventory.routes import bp as inventory_bp
from .waitlist.routes import bp as waitlist_bp
from .users.routes import bp as users_bp
from .loans.routes import bp as loans_bp
from .notification.routes import bp as notification_bp
from .reports.routes import bp as reports_bp
from .common.models import create_all_tables

def create_app(config_obj=Config):
    app = Flask(__name__)
    app.config.from_object(config_obj)

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(catalog_bp, url_prefix="/catalog")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")
    app.register_blueprint(waitlist_bp, url_prefix="/waitlist")
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(loans_bp, url_prefix="/loans")
    app.register_blueprint(notification_bp, url_prefix="/notifications")
    app.register_blueprint(reports_bp, url_prefix="/reports")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
