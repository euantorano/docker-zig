FROM alpine:3.9

ARG ZIG_VERSION=0.4.0
ARG ZIG_URL=https://ziglang.org/download/${ZIG_VERSION}/zig-linux-x86_64-${ZIG_VERSION}.tar.xz
ARG ZIG_SHA256=ea544df514327e7bcf58f6a4f2c0c726a75acbfe0af51ebe250bfe39d5aa2eef

LABEL version=0.4.0
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