"""Entry point: python -m sidecar"""

import uvicorn

from sidecar.app import app


def main(host: str = "127.0.0.1", port: int = 8731):
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
