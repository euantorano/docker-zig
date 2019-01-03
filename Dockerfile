FROM alpine:3.8

ARG ZIG_VERSION=0.3.0
ARG ZIG_URL=https://ziglang.org/download/${ZIG_VERSION}/zig-linux-x86_64-${ZIG_VERSION}.tar.xz
ARG ZIG_SHA256=b378d0aae30cb54f28494e7bc4efbc9bfb6326f47bfb302e8b5287af777b2f3c

LABEL maintainer="Euan T"

WORKDIR /usr/src

COPY docker-zig-manager /usr/local/bin/

RUN set -ex \
	&& /usr/local/bin/docker-zig-manager fetch $ZIG_URL $ZIG_SHA256 \
	&& /usr/local/bin/docker-zig-manager extract

ENV PATH "/usr/local/bin/zig:${PATH}"

WORKDIR /app

ENTRYPOINT ["/usr/local/bin/zig/zig"]
CMD ["help"]