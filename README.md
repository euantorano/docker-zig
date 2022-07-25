# Zig

A docker image for [Zig](https://ziglang.org) based upon Alpine Linux 3.16.

## Using this image

### Building an executable

```
docker run -v $PWD:/app euantorano/zig:0.9.1 build-exe hello.zig
```

## Available tags

There are two variants of tags provided by this repository - release tags such as `0.9.1`, and `master` branch builds such as `master-28018703`.

The most recent `master-X` build is always tagged as simply `master` as well as having a tag including the Git hash for the release.

The most recent stable release is always tagged as `latest`.

## Building the Docker image(s)

A bash script (`build.sh`) is ran by GitHub actions nightly in order to check for new versions and to then build and push images for them.