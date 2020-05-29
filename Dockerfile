FROM alpine:3.11

ARG ZIG_VERSION=0.6.0
ARG ZIG_URL=https://ziglang.org/download/${ZIG_VERSION}/zig-linux-x86_64-${ZIG_VERSION}.tar.xz
ARG ZIG_SHA256=08fd3c757963630645441c2772362e9c2294020c44f14fce1b89f45de0dc1253

LABEL version=0.6.0
LABEL maintainer="Euan Torano <euan@torano.co.uk>"

WORKDIR /usr/src

COPY docker-zig-manager /usr/local/bin/docker-zig-manager

RUN set -ex \
	&& /usr/local/bin/docker-zig-manager fetch $ZIG_URL $ZIG_SHA256 \
	&& /usr/local/bin/docker-zig-manager extract

ENV PATH "/usr/local/bin/zig:${PATH}"

WORKDIR /app

ENTRYPOINT ["/usr/local/bin/zig/zig"]
CMD ["--help"]
