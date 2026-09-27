import shutil
import tempfile

from flask import (
    Blueprint,
    jsonify,
    request,
    send_file,
    session,
)

from rc_directory_anki.auth import require_token
from rc_directory_anki.build_pack import build_pack
from rc_directory_anki.rc_api import (
    get_batch,
    get_batches,
    get_my_profile,
    get_profiles,
)

bp = Blueprint("api", __name__)


@bp.route("/batches")
@require_token
def batches():
    token = session["token"]
    return get_batches(token)


@bp.post("/generate-pack")
@require_token
def generate_pack():
    token = session["token"]

    match request.form.get("scope"):
        case "current":
            pack_name = "At RC now"
            profiles_query = {"scope": "current"}

        case "overlap":
            profile = get_my_profile(token)
            pack_name = f"At RC with {profile['name']}"
            profiles_query = {"scope": "overlap"}

        case "batch":
            batch_id_str = request.form.get("batch_id")
            if batch_id_str is None:
                return jsonify(error="batch_id must be an integer"), 400
            try:
                batch_id = int(batch_id_str)
            except ValueError:
                return jsonify(error="batch_id must be an integer"), 400

            batch = get_batch(token, batch_id)
            pack_name = f"RC {batch['name']}"
            profiles_query = {"batch_id": batch_id}

        case _:
            return jsonify(
                error="scope must be one of 'current', 'overlap', or 'batch'"
            ), 400

    profiles = get_profiles(token, profiles_query)

    tmpdir = tempfile.mkdtemp()
    try:
        return send_file(
            build_pack(tmpdir, pack_name, profiles),
            mimetype="application/octet-stream",
            as_attachment=True,
        )
    finally:
        shutil.rmtree(tmpdir)
