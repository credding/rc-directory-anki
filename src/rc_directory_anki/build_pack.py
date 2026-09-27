import concurrent.futures
import importlib.resources
import os
import re
import threading

import filetype
import genanki
import requests
from jinja2 import Environment, PackageLoader

NOPHOTO_URL = "https://d29xw0ra2h4o4u.cloudfront.net/assets/people/no_photo_150-445e994d9f825a8fb6fbf92e0eab7a8566139b2a201ee1aa41570a772c5e78dd.jpg"

jinja_env = Environment(loader=PackageLoader("rc_directory_anki", "."))
card_info_template = jinja_env.get_template("card-info.jinja")

resources_env = importlib.resources.files("rc_directory_anki")
card_style = resources_env.joinpath("card-style.css").read_text()

rc_directory_deck_id = 1832163555
rc_directory_deck_name = "RC Directory 🐙"

rc_directory_profile_model = genanki.Model(
    1282812154,
    "RC Directory Profile",
    fields=[
        {"name": "ID"},
        {"name": "Image"},
        {"name": "FirstName"},
        {"name": "LastName"},
        {"name": "Pronouns"},
        {"name": "Info"},
        {"name": "HasImage"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": '<div class="profile-image">{{Image}}</div>'
            "{{^HasImage}}"
            '<div class="name"><b>{{FirstName}}</b> {{LastName}}</div>'
            "{{/HasImage}}",
            "afmt": "{{FrontSide}}"
            '<hr id="answer">'
            "{{#HasImage}}"
            '<div class="name"><b>{{FirstName}}</b> {{LastName}}</div>'
            "{{/HasImage}}"
            '<div class="pronouns">{{Pronouns}}</div>'
            "{{Info}}",
        }
    ],
    css=card_style,
)


class RCDirectoryProfile(genanki.Note):
    @property
    def guid(self):
        # identify cards by ID
        return genanki.guid_for(self.fields[0])  # ty: ignore[not-subscriptable]


def build_pack(tmpdir: str, package_name: str, profiles: list) -> str:
    deck = genanki.Deck(rc_directory_deck_id, rc_directory_deck_name)
    media_files = []

    image_urls = {profile["image_path"]: profile for profile in profiles}
    image_paths = {
        url: path
        for url, path in zip(
            image_urls.keys(),
            fetch_profile_image_executor.map(
                fetch_profile_image, [tmpdir] * len(image_urls), image_urls.values()
            ),
        )
    }

    for profile in profiles:
        tags = set()
        for stint in profile["stints"]:
            stint_type = stint["type"]
            match stint_type:
                case "retreat":
                    tags.add("recurser")
                    batch_tag = re.sub(
                        "\\W+", "_", stint["batch"]["short_name"].lower()
                    )
                    tags.add(batch_tag)
                    tags.add(
                        f"{batch_tag}_{'half' if stint['for_half_batch'] else 'full'}"
                    )
                case "employment":
                    tags.add("faculty")
                case _:
                    tags.add(stint_type)

        image_url = profile["image_path"]
        image_path = image_paths[image_url]

        deck.add_note(
            RCDirectoryProfile(
                model=rc_directory_profile_model,
                fields=[
                    str(profile["id"]),  # ID
                    f'<img src="{os.path.basename(image_path)}">',  # Image
                    profile["first_name"],  # Name
                    profile["last_name"],  # Name
                    profile["pronouns"],  # Pronouns
                    card_info_template.render(profile=profile),  # Info
                    "1" if image_url != NOPHOTO_URL else "",  # HasImage
                ],
                tags=tags,
            )
        )
        media_files.append(image_path)

    package = genanki.Package(deck)
    package.media_files = media_files

    deck_file_name = re.sub("\\W+", "_", package_name)
    deck_file = os.path.join(tmpdir, f"{deck_file_name}.apkg")
    package.write_to_file(deck_file)

    return deck_file


fetch_profile_image_thread_local = threading.local()
fetch_profile_image_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)


def fetch_profile_image(tmpdir: str, profile) -> str:
    if not hasattr(fetch_profile_image_thread_local, "session"):
        fetch_profile_image_thread_local.session = requests.Session()

    session = fetch_profile_image_thread_local.session
    image_url = profile["image_path"]
    response = session.get(image_url)

    ext = filetype.guess_extension(response.content)
    image_name = f"{profile['slug'] if image_url != NOPHOTO_URL else 'no_photo'}.{ext}"
    image_path = os.path.join(tmpdir, image_name)

    with open(image_path, "wb") as f:
        f.write(response.content)

    return image_path
