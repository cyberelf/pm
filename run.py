import os

from reports_app.server import run


if __name__ == "__main__":
    run(
        host=os.environ.get("REPORTS_HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
    )
