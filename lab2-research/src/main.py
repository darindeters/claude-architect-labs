import os
import sys

from dotenv import load_dotenv

from .coordinator import run


def main():
    load_dotenv()
    if len(sys.argv) < 2:
        print("Usage: python -m src.main '<research topic>'")
        sys.exit(1)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set.")
        sys.exit(1)
    print(run(sys.argv[1]))


if __name__ == "__main__":
    main()
