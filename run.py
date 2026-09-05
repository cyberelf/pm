import os
from pathlib import Path

from reports_app.config import DATA_DIR, load_env_file
from reports_app.server import run


if __name__ == "__main__":
    load_env_file()
    tls_port = (os.environ.get("REPORTS_TLS_PORT") or "8443").strip()
    tls_cert = Path(os.environ.get("REPORTS_TLS_CERT") or DATA_DIR / "tls" / "service.crt")
    tls_key = Path(os.environ.get("REPORTS_TLS_KEY") or DATA_DIR / "tls" / "service.key")
    use_tls = bool(tls_port) and tls_cert.is_file() and tls_key.is_file()
    run(
        host=os.environ.get("REPORTS_HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
        tls_port=int(tls_port) if use_tls else None,
        tls_cert=str(tls_cert) if use_tls else None,
        tls_key=str(tls_key) if use_tls else None,
    )
