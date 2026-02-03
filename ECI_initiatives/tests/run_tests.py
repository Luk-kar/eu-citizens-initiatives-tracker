#!/usr/bin/env python3
"""
Test runner script for ECI initiatives scraper, extractor, and merger tests.

Usage:
    python run_tests.py [options]

Basic Examples:
    python run_tests.py                                    # Run all tests
    python run_tests.py --scraper                          # Run all scraper tests
    python run_tests.py --extractor                        # Run all extractor tests
    python run_tests.py --merger                           # Run all merger tests
    python run_tests.py --merger --behaviour               # Run merger behaviour tests
    python run_tests.py --merger --end-to-end              # Run merger end-to-end tests
    python run_tests.py --scraper --initiatives            # Run scraper initiatives tests
    python run_tests.py --scraper --responses              # Run scraper responses tests
    python run_tests.py --scraper --followup-website       # Run scraper followup website tests
    python run_tests.py --scraper --followup-website --behaviour  # Run followup website behaviour tests

Specific Test Selection:
    # Run specific test file
    python run_tests.py scraper/responses_followup_website/behaviour/test_browser.py

    # Run specific test class
    python run_tests.py scraper/responses_followup_website/behaviour/test_browser.py::TestBrowserInitialization

    # Run specific test method
    python run_tests.py scraper/responses_followup_website/behaviour/test_browser.py::TestBrowserInitialization::test_browser_initialized_with_chrome_options
"""

import os
import sys
import subprocess
import argparse


def run_tests(
    test_path=".",
    verbose=True,
    stop_on_failure=True,
    coverage=False,
    markers=None,
):
    """Run the scraper, extractor, and merger tests with appropriate options."""
    # Change to the tests directory
    test_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(test_dir)

    # Base pytest command
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        test_path,
    ]

    # Add options
    if verbose:
        cmd.append("-v")
        cmd.extend(
            [
                "--tb=short",  # shorter traceback format
                "--color=yes",  # colored output
                "--durations=10",  # show 10 slowest tests
            ]
        )

    if stop_on_failure:
        cmd.append("-x")  # stop on first failure

    if coverage:
        cmd.extend(
            ["--cov=ECI_initiatives", "--cov-report=html", "--cov-report=term-missing"]
        )

    if markers:
        cmd.extend(["-m", markers])

    print(f"Running tests from: {test_path}")
    print("Command:", " ".join(cmd))
    print("-" * 60)

    result = subprocess.run(cmd)
    return result.returncode


def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Run ECI scraper, extractor, and merger tests"
    )

    # Define all arguments in a dictionary
    arguments = {
        "path": {
            "nargs": "?",
            "default": None,
            "help": "Test path to run (optional, overrides other path flags)",
        },
        "--no-verbose": {"action": "store_true", "help": "Disable verbose output"},
        "--no-stop": {"action": "store_true", "help": "Don't stop on first failure"},
        "--coverage": {"action": "store_true", "help": "Generate coverage report"},
        "--markers": {"help": "Run tests with specific markers (e.g., 'not slow')"},
        "--scraper": {"action": "store_true", "help": "Run scraper tests"},
        "--extractor": {"action": "store_true", "help": "Run extractor tests"},
        "--merger": {"action": "store_true", "help": "Run merger tests"},
        "--initiatives": {
            "action": "store_true",
            "help": "Run initiatives tests (scraper/extractor)",
        },
        "--responses": {
            "action": "store_true",
            "help": "Run responses tests (scraper only)",
        },
        "--followup-website": {
            "action": "store_true",
            "help": "Run responses followup website tests (scraper only)",
        },
        "--behaviour": {"action": "store_true", "help": "Run only behaviour tests"},
        "--end-to-end": {"action": "store_true", "help": "Run only end-to-end tests"},
    }

    # Add all arguments to parser
    for arg_name, arg_config in arguments.items():
        parser.add_argument(arg_name, **arg_config)

    args = parser.parse_args()

    # Determine test path based on arguments (priority order)
    if args.path:
        # Explicit path provided - use it directly
        test_path = args.path

    # --- MERGER ---
    elif args.merger and args.behaviour:
        test_path = "csv_merger/responses/behaviour"
    elif args.merger and getattr(args, "end_to_end"):
        test_path = "csv_merger/responses/end_to_end"
    elif args.merger:
        test_path = "csv_merger"

    # --- SCRAPER ---

    # Scraper paths with initiatives/responses differentiation
    elif args.scraper and args.initiatives and args.behaviour:
        test_path = "scraper/initiatives/behaviour"
    elif args.scraper and args.initiatives and getattr(args, "end_to_end"):
        test_path = "scraper/initiatives/end_to_end"
    elif args.scraper and args.initiatives:
        test_path = "scraper/initiatives"

    elif args.scraper and args.responses and args.behaviour:
        test_path = "scraper/responses/behaviour"
    elif args.scraper and args.responses and getattr(args, "end_to_end"):
        test_path = "scraper/responses/end_to_end"
    elif args.scraper and args.responses:
        test_path = "scraper/responses"

    elif args.scraper and getattr(args, "followup_website") and args.behaviour:
        test_path = "scraper/responses_followup_website/behaviour"
    elif (
        args.scraper
        and getattr(args, "followup_website")
        and getattr(args, "end_to_end")
    ):
        test_path = "scraper/responses_followup_website/end_to_end"
    elif args.scraper and getattr(args, "followup_website"):
        test_path = "scraper/responses_followup_website"

    elif args.scraper and args.behaviour:
        # Run all scraper behaviour tests (both initiatives and responses)
        test_path = "scraper"
        if not args.markers:
            args.markers = "behaviour"
    elif args.scraper and getattr(args, "end_to_end"):
        # Run all scraper end-to-end tests (both initiatives and responses)
        test_path = "scraper"
        if not args.markers:
            args.markers = "end_to_end"
    elif args.scraper:
        # All scraper tests
        test_path = "scraper"

    # --- EXTRACTOR ---
    # Extractor paths
    elif args.extractor and args.initiatives and args.behaviour:
        test_path = "extractor/initiatives/behaviour"
    elif args.extractor and args.initiatives and getattr(args, "end_to_end"):
        test_path = "extractor/initiatives/end_to_end"
    elif args.extractor and args.initiatives:
        test_path = "extractor/initiatives"

    elif args.extractor and args.behaviour:
        test_path = "extractor/initiatives/behaviour"
    elif args.extractor and getattr(args, "end_to_end"):
        test_path = "extractor/initiatives/end_to_end"
    elif args.extractor:
        # All extractor tests
        test_path = "extractor"

    # --- COMBINED (without scraper/extractor/merger specification) ---
    # Initiatives/Responses only
    elif args.initiatives and args.behaviour:
        # Run all initiatives behaviour tests (scraper + extractor)
        test_path = "."
        if not args.markers:
            args.markers = "initiatives and behaviour"
    elif args.initiatives and getattr(args, "end_to_end"):
        # Run all initiatives end-to-end tests (scraper + extractor)
        test_path = "."
        if not args.markers:
            args.markers = "initiatives and end_to_end"
    elif args.initiatives:
        # All initiatives tests
        test_path = "."
        if not args.markers:
            args.markers = "initiatives"

    elif args.responses:
        # All responses tests (scraper only)
        test_path = "scraper/responses"

    elif getattr(args, "followup_website"):
        # All responses followup website tests (scraper only)
        test_path = "scraper/responses_followup_website"

    else:
        # Default - run all tests
        test_path = "."

    exit_code = run_tests(
        test_path=test_path,
        verbose=not args.no_verbose,
        stop_on_failure=not args.no_stop,
        coverage=args.coverage,
        markers=args.markers,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
