import argparse
import json
import sys
from pathlib import Path

from coreason_validator.utils.exporter import export_json_schema
from coreason_validator.validator import validate_file


def handle_check(args: argparse.Namespace) -> int:
    """
    Handles the 'check' subcommand.
    Validates the file at the given path.
    """
    path = Path(args.path)
    if not path.exists():
        if args.json:
            print(json.dumps({"is_valid": False, "errors": [{"msg": f"File not found: {path}"}]}))
        else:
            print(f"Error: File not found: {path}")
        return 1

    result = validate_file(path)

    if args.json:
        # Dump the result model to JSON.
        print(result.model_dump_json())
        return 0 if result.is_valid else 1

    if result.is_valid:
        print(f"✅ Validation successful: {path}")
        return 0
    else:
        print(f"❌ Validation failed: {path}")
        for error in result.errors:
            msg = error.get("msg", "Unknown error")
            loc = error.get("loc", [])
            loc_str = " -> ".join(str(loc_item) for loc_item in loc) if loc else "Root"
            print(f"  - [{loc_str}]: {msg}")
        return 1


def handle_export(args: argparse.Namespace) -> int:
    """
    Handles the 'export' subcommand.
    Exports JSON schemas to the given directory.
    """
    output_dir = Path(args.dir)
    try:
        export_json_schema(output_dir)
        print(f"✅ Schemas exported to: {output_dir}")
        return 0
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return 1


def main() -> None:
    """
    Main entry point for the CLI.
    """
    parser = argparse.ArgumentParser(description="CoReason Validator CLI: Enforce structural integrity.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommands")

    # Subcommand: check
    parser_check = subparsers.add_parser("check", help="Validate a file against its schema.")
    parser_check.add_argument("path", help="Path to the file to validate.")
    parser_check.add_argument("--json", action="store_true", help="Output result as JSON.")
    parser_check.set_defaults(func=handle_check)

    # Subcommand: export
    parser_export = subparsers.add_parser("export", help="Export JSON schemas to a directory.")
    parser_export.add_argument("dir", help="Directory to output schema files.")
    parser_export.set_defaults(func=handle_export)

    # Parse args
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    # Execute the selected function
    exit_code = args.func(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()  # pragma: no cover
