import logging
import os

from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

from rc_directory_anki.api import bp as api_bp
from rc_directory_anki.auth import bp as auth_bp
from rc_directory_anki.auth import oauth, require_token
from rc_directory_anki.rc_api import get_batches

app = Flask(__name__)
app.config.from_prefixed_env()

oauth.init_app(app)
app.wsgi_app = ProxyFix(app.wsgi_app)  # ty: ignore[invalid-assignment]

if "gunicorn" in os.environ.get("SERVER_SOFTWARE", "").lower():
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
else:
    logging.basicConfig(level=logging.INFO)

app.register_blueprint(auth_bp)
app.register_blueprint(api_bp, url_prefix="/api")


@app.route("/")
@require_token
def index():
    batches = get_batches()
    return render_template("index.html", batches=batches)
