# whisper.cpp ASR server image for the docker compose deployment mode.
#
# Builds the whisper-server HTTP binary from a pinned upstream tag and serves
# /inference on port 8766. The GGML model is not baked into the image; compose
# mounts ./data/models read-only at /models (the same directory the native
# install uses), so one model download serves both deployment modes.
FROM debian:bookworm-slim AS build

# Optional apt mirror host (e.g. mirrors.tuna.tsinghua.edu.cn) for networks
# where deb.debian.org is slow or unreachable.
ARG APT_MIRROR=""
# whisper.cpp tag to build; override in .env to move to a newer release.
ARG WHISPER_CPP_VERSION="v1.9.3"

RUN if [ -n "$APT_MIRROR" ]; then \
        sed -i "s|deb.debian.org|$APT_MIRROR|g" /etc/apt/sources.list.d/debian.sources; \
    fi \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        cmake \
        git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch "$WHISPER_CPP_VERSION" \
        https://github.com/ggml-org/whisper.cpp /src/whisper.cpp

RUN cmake -S /src/whisper.cpp -B /src/whisper.cpp/build \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_SHARED_LIBS=OFF \
        -DGGML_NATIVE=OFF \
        -DWHISPER_BUILD_TESTS=OFF \
    && cmake --build /src/whisper.cpp/build --target whisper-server -j"$(nproc)"

# Older whisper.cpp tags named the binary `server`; normalize so the runtime
# stage has one known path regardless of the tag the image was built from.
RUN mkdir -p /out \
    && if [ -f /src/whisper.cpp/build/bin/whisper-server ]; then \
           cp /src/whisper.cpp/build/bin/whisper-server /out/whisper-server; \
       else \
           cp /src/whisper.cpp/build/bin/server /out/whisper-server; \
       fi

FROM debian:bookworm-slim

# Optional apt mirror host, same knob as the build stage.
ARG APT_MIRROR=""

# libgomp1 is the OpenMP runtime ggml was built against; bash ships with
# debian-slim and backs the healthcheck (/dev/tcp probe). Nothing else needed.
RUN if [ -n "$APT_MIRROR" ]; then \
        sed -i "s|deb.debian.org|$APT_MIRROR|g" /etc/apt/sources.list.d/debian.sources; \
    fi \
    && apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /out/whisper-server /usr/local/bin/whisper-server

# Runs as the same fixed uid as the reports container; the model mount is
# read-only and the server only writes to stdout/stderr (docker logs).
USER 1000:1000

EXPOSE 8766

ENTRYPOINT ["/usr/local/bin/whisper-server"]
