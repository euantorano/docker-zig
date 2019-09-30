import logging
from typing import Generator, List, Optional
import requests
import semver
import docker
import os
import time
import argparse
from urllib.parse import urlparse


REPOSITORY_NAME = "euantorano/zig"
RELEASES_URL = "https://ziglang.org/download/index.json"


class ReleaseHash(object):
    def __init__(self, release: str, sha: str, url: str, is_master: bool = False):
        super(ReleaseHash, self).__init__()
        self.release = release
        self.hash = sha
        self.url = url
        self.is_master = is_master

    def __repr__(self):
        return "{} (hash: {}; url: {}; master: {})".format(self.release, self.hash, self.url, self.is_master)

    def tag_without_repository(self) -> str:
        if self.is_master:
            return "master-{}".format(self.release)

        return self.release

    def tag(self) -> str:
        return "{}:{}".format(REPOSITORY_NAME, self.tag_without_repository())

    def version(self) -> Optional[semver.VersionInfo]:
        if self.is_master:
            return None

        return semver.parse_version_info(self.release)


class BuiltImage(object):
    def __init__(self, image_id: str, tags: List[str], image: docker.models.images.Image):
        super(BuiltImage, self).__init__()
        self.image_id = image_id
        self.tags = tags
        self.image = image


def is_valid_version(release: str) -> bool:
    try:
        _ = semver.parse_version_info(release)
        return True
    except ValueError:
        return False


def extract_release_from_url(url: str) -> str:
    parsed_url = urlparse(url)
    path = parsed_url.path
    base_name = os.path.basename(path)

    index_of_plus = base_name.find('+')

    if index_of_plus != -1:
        base_name = base_name[index_of_plus + 1:]

    index_of_period = base_name.find('.')
    if index_of_period != -1:
        base_name = base_name[:index_of_period]

    return base_name


def get_release_hashes() -> Generator[ReleaseHash, None, None]:
    r = requests.get(RELEASES_URL)

    r.raise_for_status()

    json = r.json()

    for release, info in json.items():
        if "x86_64-linux" not in info:
            continue

        linux_info = info["x86_64-linux"]

        if release == "master":
            release_name = extract_release_from_url(linux_info["tarball"])

            yield ReleaseHash(release_name, linux_info["shasum"], linux_info["tarball"], True)
        elif is_valid_version(release):
            yield ReleaseHash(release, linux_info["shasum"], linux_info["tarball"], False)


def print_build_log(build_log: iter):
    for log in build_log:
        if isinstance(log, dict):
            if 'stream' in log:
                entry = log['stream'].strip()
                if entry:
                    logging.info(entry)
            if 'status' in log:
                entry = log['status'].strip()
                if entry:
                    logging.info(entry)


def build_image_for_release(client: docker.DockerClient, release: ReleaseHash) -> Optional[BuiltImage]:
    try:
        script_file_path = os.path.dirname(os.path.realpath(__file__))

        tag = release.tag()

        tags = [release.tag_without_repository()]

        args = {
            "ZIG_VERSION": release.release,
            "ZIG_URL": release.url,
            "ZIG_SHA256": release.hash
        }

        logging.info("Building image for release %s", release)

        start = time.time()

        built_image, _ = client.images.build(
            path=script_file_path,
            tag=tag,
            rm=True,
            pull=True,
            buildargs=args
        )

        if release.is_master:
            # tag as main master release
            if built_image.tag(REPOSITORY_NAME, "master", force=True):
                tags.append("master")

            built_image.reload()

        end = time.time()

        elapsed = end - start

        logging.info("Built image for release %s with ID %s in %ss", tag, built_image.id, elapsed)

        return BuiltImage(built_image.id, tags, built_image)
    except docker.errors.BuildError as e:
        logging.error("Error building image for release %s: %s", release.tag_without_repository(), e)
        print_build_log(e.build_log)

        return None
    except docker.errors.APIError as e:
        logging.error("API error building image for release %s: %s", release.tag_without_repository(), e)

        return None


def get_last_built_master_image(path: str) -> Optional[str]:
    if not os.path.isfile(path):
        return None

    with open(path, 'r') as f:
        return f.read()


def get_last_built_version(path: str) -> Optional[semver.VersionInfo]:
    if not os.path.isfile(path):
        return None

    with open(path, 'r') as f:
        release = f.read()

    try:
        return semver.parse_version_info(release)
    except ValueError:
        return None


def write_file_content(path: str, release: str):
    with open(path, 'w') as f:
        f.write(release)


def main() -> None:
    logging.basicConfig(format='%(levelname)s: %(asctime)s: %(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser(description='Build and tag the Docker containers for the most recent Zig releases')
    parser.add_argument('--master-path', dest='master_path', required=True, type=str)
    parser.add_argument('--version-path', dest='version_path', required=True, type=str)

    args = parser.parse_args()

    client = docker.from_env()

    last_built_master_image = get_last_built_master_image(args.master_path)
    last_built_version = get_last_built_version(args.version_path)

    logging.info("Got latest master hash: %s; latest version: %s", last_built_master_image, last_built_version)

    built_images = []

    max_version: Optional[semver.VersionInfo] = None

    latest_updated = False

    for release_hash in get_release_hashes():
        if release_hash.is_master:
            if release_hash.release != last_built_master_image:
                # new master release
                built_image = build_image_for_release(client, release_hash)
                if built_image is not None:
                    built_images.append(built_image)
                    write_file_content(args.master_path, release_hash.release)
        else:
            if last_built_version is None or release_hash.version() > last_built_version:
                built_image = build_image_for_release(client, release_hash)
                if built_image is not None:
                    built_images.append(built_image)

                    if max_version is None or max_version < release_hash.version():
                        max_version = release_hash.version()

                        write_file_content(args.version_path, release_hash.release)

                        logging.info("Tagging release %s as latest", max_version)
                        built_image.image.tag(REPOSITORY_NAME, "latest")
                        latest_updated = True

    if len(built_images) > 0:
        logging.info("Built %d images, pushing to the repository", len(built_images))

        num_pushed = 0

        for built_image in built_images:
            for tag in built_image.tags:
                try:
                    logging.info("Pushing tag %s to repository %s", tag, REPOSITORY_NAME)
                    client.images.push(REPOSITORY_NAME, tag=tag)
                    num_pushed += 1
                except Exception as e:
                    logging.error("Error pushing tag %s to the repository: %s", tag, e)

        logging.info("Pushed %d images to the repository", num_pushed)

        if latest_updated:
            logging.info("Pushing latest tag for version: %s", max_version)
            client.images.push(REPOSITORY_NAME, tag="latest")
    else:
        logging.info("Built 0 images, nothing to push")


if __name__ == "__main__":
    main()
