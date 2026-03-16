"""Flask blueprints for Market Intelligence API."""
from routes.prices import bp as prices_bp
from routes.news import bp as news_bp
from routes.map_routes import bp as map_bp
from routes.risk import bp as risk_bp
from routes.market import bp as market_bp
from routes.misc import bp as misc_bp

__all__ = ["prices_bp", "news_bp", "map_bp", "risk_bp", "market_bp", "misc_bp"]
