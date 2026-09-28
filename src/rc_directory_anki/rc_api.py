from urllib.parse import urlencode

from flask import abort, jsonify, make_response

from rc_directory_anki.auth import recurse

MAX_PROFILES = 200


def get_batches() -> list:
    resp = recurse.get("batches")
    resp.raise_for_status()
    return resp.json()


def get_batch(batch_id: int):
    resp = recurse.get(f"batches/{batch_id}")
    resp.raise_for_status()
    return resp.json()


def get_profiles(query) -> list:
    result = []

    while True:
        params = query.copy()
        params["limit"] = 50
        params["offset"] = len(result)
        resp = recurse.get(f"profiles?{urlencode(params)}")
        resp.raise_for_status()

        page = resp.json()

        result.extend(page)

        if len(page) < 50:
            break

        if len(result) >= MAX_PROFILES:
            abort(
                make_response(
                    jsonify(error="too many profiles, try a more narrow query"), 400
                )
            )

    return result


def get_my_profile():
    resp = recurse.get("profiles/me")
    resp.raise_for_status()
    return resp.json()
