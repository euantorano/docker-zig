# Zig

A docker image for [Zig](https://ziglang.org) based upon Alpine Linux 3.8.

## Using this image

### Building an executable

```
docker run -v $PWD:/app euantorano/zig:0.3.0 build-exe hello.zig
```