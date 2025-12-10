from flask import Flask
from dotenv import load_dotenv
from .extensions import db, jwt
from .config import Config
from .auth.routes import bp as auth_bp
from .catalog.routes import bp as catalog_bp
from .inventory.routes import bp as inventory_bp
from .waitlist.routes import bp as waitlist_bp
from .users.routes import bp as users_bp
from .loans.routes import bp as loans_bp
from .notification.routes import bp as notification_bp
from .reports.routes import bp as reports_bp
from .common.models import create_all_tables, TokenBlocklist

def create_app(config_obj=Config):
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(config_obj)
    
    # Configurar Flask para que acepte URLs con o sin barra final
    # Esto evita errores 404 por inconsistencias en las URLs del frontend
    app.url_map.strict_slashes = False

    db.init_app(app)
    jwt.init_app(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
        try:
            jti = jwt_payload["jti"]
            token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()
            return token is not None
        except Exception:
            # Si hay error (ej: tabla no existe), asumir token no revocado
            return False

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
