# Build from this directory: docker build -t claude-travel:latest .
#
# Behind a TLS-intercepting proxy, supply its CA:
#   docker buildx build --build-context cacert=<dir-with-a-*.pem> ...

# Default (empty) source for the optional `cacert` build context.
FROM scratch AS cacert

FROM python:3.12-slim
WORKDIR /app

# Optional: trust a corporate proxy CA. No-op unless `cacert` is supplied.
COPY --from=cacert . /usr/local/share/ca-certificates/extra/
RUN apt-get update >/dev/null 2>&1 || true; \
    for f in /usr/local/share/ca-certificates/extra/*; do \
        [ -e "$f" ] || continue; \
        cp "$f" "/usr/local/share/ca-certificates/extra-$(basename "$f").crt"; \
    done; \
    (command -v update-ca-certificates >/dev/null && update-ca-certificates) || true
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    PIP_CERT=/etc/ssl/certs/ca-certificates.crt

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

# The bundled Claude Code CLI writes state under $HOME; nobody has no home dir.
ENV HOME=/tmp/home
RUN mkdir -p /tmp/home && chmod 1777 /tmp/home
USER nobody
ENTRYPOINT ["python", "-m", "claude_travel.main"]
