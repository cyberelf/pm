import os

from reports_app.config import load_env_file
from reports_app.server import run


if __name__ == "__main__":
    load_env_file()
    run(
        host=os.environ.get("REPORTS_HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
    )
