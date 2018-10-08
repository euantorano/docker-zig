#!/bin/sh

set -e

loop_iter=0

while IFS='' read -r line || [[ -n "$line" ]]; do
	line_parts=( $line )

	len="${#line_parts[@]}"

	if [ $len -gt 1 ]; then
		version_number=${line_parts[0]}
		checksum=${line_parts[1]}

		# most recent version should be first in the "versions.txt" file
		if [ $loop_iter -eq 0 ]; then
			docker build -t "euantorano/zig:$version_number" \
				-t "euantorano/zig:latest" \
				--build-arg "ZIG_SHA256=$checksum" \
				--build-arg "ZIG_VERSION=$version_number" .
		else
			docker build -t "euantorano/zig:$version_number" \
				--build-arg "ZIG_SHA256=$checksum" \
				--build-arg "ZIG_VERSION=$version_number" .
		fi

		((loop_iter++))
	fi
done < "versions.txt"