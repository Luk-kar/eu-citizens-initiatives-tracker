#!/usr/bin/env python3

"""
Test runner script for ECI initiatives scraper tests.

This script provides a convenient interface to run pytest tests for the ECI scraper
with pre-configured options and shortcuts for common test scenarios.

Usage:
    python run_tests.py [path] [options]

Basic Examples:
    python run_tests.py                           # Run all scraping tests
    python run_tests.py --behaviour               # Run only behaviour tests
    python run_tests.py --end-to-end              # Run only end-to-end tests
    python run_tests.py scraper/behaviour        # Run specific directory

Specific Test Selection:

    # Run specific test file
    python run_tests.py scraper/behaviour/test_scraping_process.py

    # Run specific test class
    python run_tests.py scraper/behaviour/test_scraping_process.py::TestErrorRecoveryAndResilience

    # Run specific test method
    python run_tests.py scraper/behaviour/test_scraping_process.py::TestErrorRecoveryAndResilience::test_individual_page_download_failure_handling
"""


import os
import sys
import subprocess
import argparse


def run_tests(
    test_path="scraper",
    verbose=True,
    stop_on_failure=True,
    coverage=False,
    markers=None,
):
    """Run the scraper tests with appropriate options."""

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

    print(f"Running scraper tests from: {test_path}")
    print("Command:", " ".join(cmd))
    print("-" * 60)

    result = subprocess.run(cmd)
    return result.returncode


def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(description="Run ECI scraper tests")

    # Define all arguments in a dictionary
    arguments = {
        "path": {
            "nargs": "?",
            "default": "scraper",
            "help": "Test path to run (default: scraper)",
        },
        "--no-verbose": {"action": "store_true", "help": "Disable verbose output"},
        "--no-stop": {"action": "store_true", "help": "Don't stop on first failure"},
        "--coverage": {"action": "store_true", "help": "Generate coverage report"},
        "--markers": {"help": "Run tests with specific markers (e.g., 'not slow')"},
        "--behaviour": {"action": "store_true", "help": "Run only behaviour tests"},
        "--end-to-end": {"action": "store_true", "help": "Run only end-to-end tests"},
    }

    # Add all arguments to parser
    for arg_name, arg_config in arguments.items():
        parser.add_argument(arg_name, **arg_config)

    args = parser.parse_args()

    # Determine test path based on arguments
    if args.behaviour:
        test_path = "scraper/behaviour"
    elif getattr(args, "end_to_end"):  # Use getattr because of the hyphen
        test_path = "scraper/end_to_end"
    else:
        test_path = args.path

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
