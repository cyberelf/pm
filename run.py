import os

from reports_app.server import run


if __name__ == "__main__":
    run(port=int(os.environ.get("PORT", "8000")))
