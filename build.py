import logging
from typing import Generator, List, Optional
from pyquery import PyQuery as pq
import semver
import docker
import os
import time

REPOSITORY_NAME = "euantorano/zig"


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


class BuiltImage(object):
    def __init__(self, image_id: str, tags: List[str], image: docker.models.images.Image):
        super(BuiltImage, self).__init__()
        self.image_id = image_id
        self.tags = tags
        self.image = image


def get_releases(doc: pq) -> Generator[str, None, None]:
    headings = doc("h2")

    for heading in headings.items():
        heading_id = heading.attr.id
        if heading_id.startswith("release-"):
            release = heading_id[8:]
            if len(release) > 0:
                yield release


def is_valid_version(release: str) -> bool:
    try:
        _ = semver.parse_version_info(release)
        return True
    except ValueError:
        return False


def escape_release_id(release: str) -> str:
    return release.replace(".", "\\.")


def get_release_table_for_heading(doc: pq, release: str) -> pq:
    escaped_heading = escape_release_id(release)
    table = doc("h2#release-{} ~ table".format(escaped_heading))

    return table


def is_binary_release(row: pq) -> bool:
    if len(row) != 4:
        return False

    kind = row.eq(1)

    return kind.text() == "Binary"


def get_release_hash(table: pq, release: str) -> Optional[ReleaseHash]:
    for tr in table("tbody tr").items():
        tds = tr("td")

        if is_binary_release(tds):
            download_cell = tds.eq(0)
            download_link = download_cell("a:first")
            href = download_link.attr("href")
            if "zig-linux" in href:
                sha = tds.eq(3).text()
                url = href

                is_master = release == "master"

                if is_master:
                    file_name = download_link.text()
                    file_name_components = file_name.split("+")

                    if len(file_name_components) >= 2:
                        # last entry is the git tag followed by extension like ".tar.xz"
                        tag_components = file_name_components[-1].split(".")
                        release = tag_components[0]

                return ReleaseHash(release, sha, url, is_master)

    return None


def get_release_hashes() -> Generator[ReleaseHash, None, None]:
    doc = pq(url="https://ziglang.org/download/")

    for release in get_releases(doc):
        if release != "master" and not is_valid_version(release):
            continue

        table = get_release_table_for_heading(doc, release)

        release_hash = get_release_hash(table, release)

        if release_hash is not None:
            yield release_hash


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
    except Exception as e:
        logging.error("Error building image for release %s: %s", release.tag_without_repository(), e)

        return None


def get_existing_images(client: docker.DockerClient) -> List[str]:
    images = []

    for image in client.images.list(name=REPOSITORY_NAME):
        images.extend(image.tags)

    return images


def main() -> None:
    logging.basicConfig(format='%(levelname)s: %(asctime)s: %(message)s', level=logging.INFO)

    client = docker.from_env()

    existing_images = get_existing_images(client)

    logging.info("Got %d existing images: %s", len(existing_images), existing_images)

    built_images = []

    max_version: Optional[semver.VersionInfo] = None
    max_version_image: Optional[docker.models.images.Image] = None

    for release_hash in get_release_hashes():
        if release_hash.tag() not in existing_images:
            built_image = build_image_for_release(client, release_hash)
            if built_image is not None:
                built_images.append(built_image)

                if not release_hash.is_master:
                    version = semver.parse_version_info(release_hash.release)

                    if max_version is None:
                        max_version = version
                        max_version_image = built_image.image
                    else:
                        if version > max_version:
                            max_version = version
                            max_version_image = built_image.image

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

        if max_version is not None and max_version_image is not None:
            logging.info("Tagging release %s as latest", max_version)
            max_version_image.tag(REPOSITORY_NAME, "latest")
            client.images.push(REPOSITORY_NAME, tag="latest")
    else:
        logging.info("Build 0 images, nothing to push")


if __name__ == "__main__":
    main()
