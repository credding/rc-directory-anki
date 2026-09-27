from functools import wraps

from authlib.integrations.flask_client import OAuth
from flask import Blueprint, redirect, request, session, url_for, current_app


def update_token(name, token):
    session["token"] = token


oauth = OAuth()
recurse = oauth.register(
    name="recurse",
    access_token_url="https://www.recurse.com/oauth/token",
    authorize_url="https://www.recurse.com/oauth/authorize",
    api_base_url="https://www.recurse.com/api/v1/",
    client_kwargs={
        "code_challenge_method": "S256",
    },
    update_token=update_token,
)

bp = Blueprint("auth", __name__)


@bp.route("/login")
def login():
    current_app.logger.info(request.headers)
    current_app.logger.info(request.headers.getlist("X-Forwarded-For"))
    current_app.logger.info(request.headers.getlist("X-Forwarded-Host"))
    current_app.logger.info(request.headers.getlist("X-Forwarded-Port"))
    redirect_uri = url_for("auth.authorize", _external=True)
    current_app.logger.info(redirect_uri)
    return recurse.authorize_redirect(redirect_uri)


@bp.route("/authorize")
def authorize():
    session["token"] = recurse.authorize_access_token()
    next_url = session.get("next_url") or url_for("index")
    return redirect(next_url)


def require_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "token" not in session:
            session["next_url"] = request.url
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function
