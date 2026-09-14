import argparse
import os

from .app import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the DeepJudge mobile web app.")
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    args = parser.parse_args()
    run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
