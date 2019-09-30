FROM alpine:3.9

ARG ZIG_VERSION=0.5.0
ARG ZIG_URL=https://ziglang.org/download/${ZIG_VERSION}/zig-linux-x86_64-${ZIG_VERSION}.tar.xz
ARG ZIG_SHA256=43e8f8a8b8556edd373ddf9c1ef3ca6cf852d4d09fe07d5736d12fefedd2b4f7

LABEL version=0.5.0
LABEL maintainer="Euan Torano <euan@torano.co.uk>"

WORKDIR /usr/src

COPY docker-zig-manager /usr/local/bin/docker-zig-manager

RUN set -ex \
	&& /usr/local/bin/docker-zig-manager fetch $ZIG_URL $ZIG_SHA256 \
	&& /usr/local/bin/docker-zig-manager extract

ENV PATH "/usr/local/bin/zig:${PATH}"

WORKDIR /app

ENTRYPOINT ["/usr/local/bin/zig/zig"]
CMD ["help"]