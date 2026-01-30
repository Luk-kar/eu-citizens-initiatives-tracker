"""
Main script for fetching EU legislation titles from CELEX references.

Usage:
    python main.py
"""

from legislation_fetcher import LegislationTitleFetcher


def main():
    """Main execution function."""

    # Example data - replace with your actual data source
    referenced_legislation_by_id = [
        '{"Article": ["19(2)"], "CELEX": ["52014DC0335"], "official_journal": {"legislation": ["2015, 260"]}}',
        None,
        '{"Directive": ["2010/63/EU"], "CELEX": ["52020DC0015"]}',
        '{"CELEX": ["52018PC0179", "32002R0178", "32019R1381"]}',
        '{"Directive": ["2010/13/EU"], "CELEX": ["62023CJ0026"]}',
        None,
        '{"Article": ["15"]}',
        '{"CELEX": ["52022PC0305"]}',
        '{"CELEX": ["32024R2522"]}',
        None,
        '{"Regulation": ["178/2002"], "Article": ["31", "29"], "CELEX": ["32025R1422"]}',
    ]

    # Initialize fetcher
    fetcher = LegislationTitleFetcher(referenced_legislation_by_id)

    # Fetch titles
    print("Fetching legislation titles from EUR-Lex...")
    df_results, metadata = fetcher.fetch_titles(verbose=True)

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"\nTotal documents found: {len(df_results)}")
    print(f"\nCELEX IDs queried: {len(metadata['celex_ids'])}")
    print(f"Unresolved references: {len(metadata['unresolved'])}")

    if not df_results.empty:
        print("\nSample results:")
        print(df_results.head(10).to_string(index=False))

    # Save results
    print("\n" + "=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)
    fetcher.save_results(
        df_results,
        csv_path="data/legislation_titles.csv",
        json_path="data/legislation_titles.json",
        metadata=metadata,
    )

    print("\nProcessing complete!")


if __name__ == "__main__":
    main()
