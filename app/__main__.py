"""``python -m app`` entrypoint."""

from __future__ import annotations

from app.server import run


def main() -> None:
    run()


if __name__ == "__main__":
    main()
