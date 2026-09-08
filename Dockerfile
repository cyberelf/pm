# Weekly Reports server image for the docker compose deployment mode.
#
# Ships chromium for server-side PDF export and Noto CJK fonts so Chinese
# report content renders in exported PDFs. Git hosts are reached through
# their REST APIs with per-user tokens; no git CLIs are needed.
FROM python:3.12-slim

# Optional apt mirror host (e.g. mirrors.tuna.tsinghua.edu.cn) for networks
# where deb.debian.org is slow or unreachable.
ARG APT_MIRROR=""

ENV PYTHONUNBUFFERED=1 \
    PORT=8765 \
    REPORTS_HOST=0.0.0.0 \
    REPORTS_TLS_PORT=8443

RUN if [ -n "$APT_MIRROR" ]; then \
        sed -i "s|deb.debian.org|$APT_MIRROR|g" /etc/apt/sources.list.d/debian.sources; \
    fi \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        chromium \
        curl \
        fonts-noto-cjk \
        openssl \
        tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY run.py ./
COPY reports_app ./reports_app
COPY static ./static
COPY scripts ./scripts

# Pre-create the named-volume mount point with the runtime uid's ownership so
# a freshly initialized volume is writable by the container user (1000:1000).
RUN mkdir -p /app/data && chown 1000:1000 /app/data

COPY --chmod=0755 docker/entrypoint.sh /usr/local/bin/entrypoint.sh

EXPOSE 8765 8443

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["python3", "-u", "run.py"]
