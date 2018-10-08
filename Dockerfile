FROM alpine:3.8

ARG ZIG_VERSION=0.3.0
ARG ZIG_URL=https://ziglang.org/download/${ZIG_VERSION}/zig-linux-x86_64-${ZIG_VERSION}.tar.xz
ARG ZIG_SHA256=b378d0aae30cb54f28494e7bc4efbc9bfb6326f47bfb302e8b5287af777b2f3c

WORKDIR /usr/src

RUN set -xe ; \
		apk add --no-cache --virtual .fetch-deps curl ; \
		curl -o zig.tar.xz "$ZIG_URL" ; \
		if [ -n "$ZIG_SHA256" ]; then \
			echo "$ZIG_SHA256 *zig.tar.xz" | sha256sum -c - ; \
		fi ; \
		apk del .fetch-deps ;

COPY docker-zig-manager /usr/local/bin/

RUN set -xe \
		&& apk add --no-cache --virtual .extract-deps tar xz \
		&& docker-zig-manager extract \
		&& apk del .extract-deps

ENV PATH "/usr/local/bin/zig:${PATH}"

WORKDIR /app

ENTRYPOINT ["/usr/local/bin/zig/zig"]
CMD ["help"]