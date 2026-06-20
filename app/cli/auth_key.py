"""CLI to encode auth-key for local MCP clients (Bearer base64 BASE_URL|user_token)."""

from __future__ import annotations

import argparse
import sys

from app.utils.app_key_codec import (
    app_context_from_encoded,
    encode_app_key_from_credentials,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Encode auth-key header: Bearer + base64(BASE_URL|user_token). "
            "Example: pnpm auth-key -- http://localhost:8069|99031c76-d288-41ea-866b-ef656f58e497"
        ),
    )
    parser.add_argument(
        "credentials",
        help="BASE_URL|user_token (e.g. http://localhost:8069|device-token-uuid)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print decoded base_url and bearer_token on stderr",
    )
    args = parser.parse_args(argv)

    encoded = encode_app_key_from_credentials(args.credentials)
    print(encoded)

    if args.verbose:
        ctx = app_context_from_encoded(encoded)
        print(f"base_url: {ctx.base_url}", file=sys.stderr)
        print(f"bearer_token: {ctx.bearer_token}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
