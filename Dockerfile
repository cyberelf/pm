# Weekly Reports server image for the docker compose deployment mode.
#
# Ships the external CLIs the app shells out to (gh, glab, claude), chromium
# for server-side PDF export, and Noto CJK fonts so Chinese report content
# renders in exported PDFs. The codex CLI is intentionally not included;
# report generation in this mode uses the claude or internal provider.
FROM python:3.12-slim

ARG GLAB_VERSION=1.116.0
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

# gh from the official GitHub CLI apt repository.
RUN mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        -o /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

# glab from the official GitLab CLI release (.deb exists for amd64/arm64).
RUN curl -fsSL -o /tmp/glab.deb \
        "https://gitlab.com/gitlab-org/cli/-/releases/v${GLAB_VERSION}/downloads/glab_${GLAB_VERSION}_linux_$(dpkg --print-architecture).deb" \
    && apt-get install -y --no-install-recommends /tmp/glab.deb \
    && rm -f /tmp/glab.deb

# Claude Code CLI (native build). The installer lays everything out under
# $HOME, so point HOME at a shared prefix instead of /root to keep the
# binary usable when the container runs as an unprivileged uid.
RUN HOME=/usr/local bash -c 'curl -fsSL https://claude.ai/install.sh | bash -s stable' \
    && rm -rf /usr/local/.claude /usr/local/.cache \
    && ln -s /usr/local/.local/bin/claude /usr/local/bin/claude

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
