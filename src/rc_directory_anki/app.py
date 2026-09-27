from cachelib import SimpleCache
from flask import Flask, render_template, session
from flask_session.cachelib import CacheLibSessionInterface

from rc_directory_anki.api import bp as api_bp
from rc_directory_anki.auth import bp as auth_bp
from rc_directory_anki.auth import oauth, require_token
from rc_directory_anki.rc_api import get_batches

app = Flask(__name__)
app.config.from_prefixed_env()

oauth.init_app(app)
app.session_interface = CacheLibSessionInterface(client=SimpleCache())  # ty: ignore[invalid-argument-type]

app.register_blueprint(auth_bp)
app.register_blueprint(api_bp, url_prefix="/api")


@app.route("/")
@require_token
def index():
    token = session["token"]
    batches = get_batches(token)
    return render_template("index.jinja", batches=batches)
