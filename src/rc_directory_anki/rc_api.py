from urllib.parse import urlencode

from flask import abort, jsonify, make_response

from rc_directory_anki.auth import recurse

MAX_PROFILES = 200


def get_batches(token) -> list:
    resp = recurse.get("batches", token=token)
    resp.raise_for_status()
    return resp.json()


def get_batch(token, batch_id: int):
    resp = recurse.get(f"batches/{batch_id}", token=token)
    resp.raise_for_status()
    return resp.json()


def get_profiles(token, query) -> list:
    result = []

    while True:
        params = query.copy()
        params["limit"] = 50
        params["offset"] = len(result)
        resp = recurse.get(
            f"profiles?{urlencode(params)}",
            token=token,
        )
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


def get_my_profile(token):
    resp = recurse.get("profiles/me", token=token)
    resp.raise_for_status()
    return resp.json()
