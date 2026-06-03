"""
Factorio Optimizer — web server entry point.

Usage:
    python server.py
    python server.py --port 8080
"""
from __future__ import annotations

import argparse
import sys

from factorio_optimizer.web.app import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Factorio Optimizer Web Server")
    parser.add_argument("--port", type=int, default=5000, help="Port to run on (default: 5000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode")
    args = parser.parse_args()

    print(f"")
    print(f"  +------------------------------------------+")
    print(f"  |       FACTORIO OPTIMIZER  v0.2.0         |")
    print(f"  |  Full factory efficiency optimizer       |")
    print(f"  +------------------------------------------+")
    print(f"")
    print(f"  -> Open in browser:  http://{args.host}:{args.port}")
    print(f"  -> Press Ctrl+C to stop")
    print(f"")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
