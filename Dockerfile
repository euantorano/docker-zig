FROM alpine:3.13

ARG ZIG_VERSION=0.7.1
ARG ZIG_URL=https://ziglang.org/download/${ZIG_VERSION}/zig-linux-x86_64-${ZIG_VERSION}.tar.xz
ARG ZIG_SHA256=18c7b9b200600f8bcde1cd8d7f1f578cbc3676241ce36d771937ce19a8159b8d

LABEL version=0.7.1
LABEL maintainer="Euan Torano <euan@torano.co.uk>"

WORKDIR /usr/src

COPY docker-zig-manager /usr/local/bin/docker-zig-manager

RUN set -ex \
	&& /usr/local/bin/docker-zig-manager fetch $ZIG_URL $ZIG_SHA256 \
	&& /usr/local/bin/docker-zig-manager extract

ENV PATH "/usr/local/bin/zig:${PATH}"

WORKDIR /app

ENTRYPOINT ["/usr/local/bin/zig/zig"]
