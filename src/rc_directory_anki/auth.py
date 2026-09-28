from functools import wraps

from authlib.integrations.base_client import OAuthError
from authlib.integrations.flask_client import FlaskOAuth2App, OAuth
from flask import Blueprint, redirect, request, session, url_for


def fetch_token():
    return session["token"]


def update_token(token, refresh_token=None, access_token=None):
    session["token"] = token


oauth = OAuth()
recurse: FlaskOAuth2App = oauth.register(
    name="recurse",
    access_token_url="https://www.recurse.com/oauth/token",
    authorize_url="https://www.recurse.com/oauth/authorize",
    api_base_url="https://www.recurse.com/api/v1/",
    client_kwargs={"code_challenge_method": "S256"},
    fetch_token=fetch_token,
    update_token=update_token
)

bp = Blueprint("auth", __name__)


@bp.app_errorhandler(OAuthError)
def handle_invalid_token(e):
    session["next_url"] = request.full_path
    return redirect(url_for("auth.login"))


@bp.route("/login")
def login():
    redirect_uri = url_for("auth.authorize", _external=True)
    return recurse.authorize_redirect(redirect_uri)


@bp.route("/authorize")
def authorize():
    session["token"] = recurse.authorize_access_token()
    next_url = session.get("next_url") or url_for("index")
    del session["next_url"]
    return redirect(next_url)


def require_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "token" not in session:
            session["next_url"] = request.full_path
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function
