# Zig

A docker image for [Zig](https://ziglang.org) based upon Alpine Linux 3.8.

## Building

This repository includes a script (`build.sh`) to build a set of known versions. Versions are listed in the `versions.txt` file in the form:

```
VERSION_NUMBER SHA256_CHECKSUM
```

The most recent version should be at the top of the file.

## Using this image

### Building an executable

```
docker run -v $PWD:/app euantorano/zig:0.3.0 build-exe hello.zig
```