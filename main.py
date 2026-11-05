#!/usr/bin/env python3
"""Starts the Dream World server with `uv run main.py [--lang en] [--debug]`.

config.py reads the site language from $DW_LANG when it's first imported.
"""
import argparse
import logging
import os

logger = logging.getLogger(__name__)

# the PokemonBridge patch in utils/patching/swf_patches.py has this port in its API address
PORT = 8080


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line options."""
    parser = argparse.ArgumentParser(description="Dream World HTTP server")
    parser.add_argument("--debug", action="store_true", help="debug logging and Flask debug mode")
    parser.add_argument("--lang", help="site language (ja, en, fr, it, de, es, ko); "
                                       "defaults to $DW_LANG, else en")
    return parser


def main() -> None:
    """Set up the language and logging, patch the SWFs if needed, then run the app."""
    parser = build_parser()
    args = parser.parse_args()
    if args.lang:
        os.environ["DW_LANG"] = args.lang

    try:
        from config import EmailNotConfiguredError, get_email_config
    except ValueError as e:  # an unsupported language
        parser.error(str(e))

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # ask for the Gmail details now, on the first run only
    try:
        get_email_config(prompt=True)
    except EmailNotConfiguredError as e:
        logger.info("Activation emails are off: %s", e)

    from api.server import create_app
    from utils import patching

    patching.prewarm()
    app = create_app()
    app.logger.info("Server started!%s", " (debug mode)" if args.debug else "")
    app.run(host="0.0.0.0", port=PORT, debug=args.debug, use_reloader=False)


if __name__ == "__main__":
    main()
