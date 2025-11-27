#!/usr/bin/env python3

from .processor import ECIFollowupWebsiteProcessor


def main():
    processor = ECIFollowupWebsiteProcessor()
    processor.run()


if __name__ == "__main__":
    main()
