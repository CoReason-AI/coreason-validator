# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

from coreason_identity.models import UserContext
from coreason_validator.utils.exporter import export_json_schema, generate_validation_report
from coreason_validator.utils.logger import logger
from coreason_validator.validator import validate_file


def get_cli_context() -> Optional[UserContext]:
    """
    Mints a UserContext from environment variables.
    """
    user_id = os.getenv("COREASON_USER_ID")
    email = os.getenv("COREASON_EMAIL")

    if user_id and email:
        return UserContext(user_id=user_id, email=email)

    logger.warning("No identity found. Validation report will be unattributed.")
    return None


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

    ctx = get_cli_context()
    result = validate_file(path, user_context=ctx)
    report = generate_validation_report(result)

    if args.json:
        # Dump the report to JSON.
        print(json.dumps(report))
        return 0 if result.is_valid else 1

    if result.is_valid:
        print(f"✅ Validation successful: {path}")
        meta = result.validation_metadata
        print(f"   Validated by: {meta.get('validated_by')}")
        print(f"   Context: {meta.get('signature_context')}")
        return 0
    else:
        print(f"❌ Validation failed: {path}")
        meta = result.validation_metadata
        print(f"   Validated by: {meta.get('validated_by')}")
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
