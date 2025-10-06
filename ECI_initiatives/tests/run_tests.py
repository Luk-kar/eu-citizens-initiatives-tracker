#!/usr/bin/env python3

"""
Test runner script for ECI initiatives scraper tests.

This script provides a convenient interface to run pytest tests for the ECI scraper
with pre-configured options and shortcuts for common test scenarios.

Usage:
    python run_tests.py [options]

Basic Examples:
    python run_tests.py                              # Run all tests
    python run_tests.py --scraper                    # Run all scraper tests
    python run_tests.py --scraper --behaviour        # Run only behaviour tests
    python run_tests.py --scraper --end-to-end       # Run only end-to-end tests

Specific Test Selection:

    # Run specific test file
    python run_tests.py scraper/initiatives/behaviour/test_scraping_process.py

    # Run specific test class
    python run_tests.py scraper/initiatives/behaviour/test_scraping_process.py::TestErrorRecoveryAndResilience

    # Run specific test method
    python run_tests.py scraper/initiatives/behaviour/test_scraping_process.py::TestErrorRecoveryAndResilience::test_individual_page_download_failure_handling
"""


# python
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

    print(f"Running tests from: {test_path}")
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
            "default": None,
            "help": "Test path to run (optional, overrides other path flags)",
        },
        "--no-verbose": {"action": "store_true", "help": "Disable verbose output"},
        "--no-stop": {"action": "store_true", "help": "Don't stop on first failure"},
        "--coverage": {"action": "store_true", "help": "Generate coverage report"},
        "--markers": {"help": "Run tests with specific markers (e.g., 'not slow')"},
        "--scraper": {"action": "store_true", "help": "Run scraper tests"},
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
    elif args.behaviour:
        # Behaviour tests flag
        test_path = "scraper/initiatives/behaviour"
    elif getattr(args, "end_to_end"):
        # End-to-end tests flag
        test_path = "scraper/initiatives/end_to_end"
    elif args.scraper:
        # All scraper tests
        test_path = "scraper"
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
