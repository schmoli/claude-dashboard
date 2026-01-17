"""Entry point for cdash CLI."""

from cdash.app import ClaudeDashApp


def main() -> None:
    """Run the Claude Dashboard application."""
    app = ClaudeDashApp()
    app.run()


if __name__ == "__main__":
    main()
