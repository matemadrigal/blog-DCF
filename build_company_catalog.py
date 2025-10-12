"""
Script to build and test the company catalog.

This will create a comprehensive list of 600+ companies from multiple sources:
- S&P 500 (500 companies)
- NASDAQ 100 (100 companies)
- Dow Jones 30 (30 companies)
- Popular International (50+ companies)

Total: 600+ unique companies (deduplicated)
"""

import sys

sys.path.insert(0, "/home/mateo/blog-DCF")

from src.data_providers.company_catalog import get_company_catalog
import json


def main():
    print("=" * 80)
    print("BUILDING COMPANY CATALOG")
    print("=" * 80)
    print()

    # Get catalog instance
    catalog = get_company_catalog()

    # Build catalog from all sources
    print("Building catalog from multiple sources...")
    print("-" * 80)
    print()

    # Try to build with online sources first
    try:
        count = catalog.build_catalog(include_online=True)
        print(f"✅ Built catalog with {count} unique companies")
    except Exception as e:
        print(f"⚠️  Online sources failed: {e}")
        print("Building with static lists only...")
        count = catalog.build_catalog(include_online=False)
        print(f"✅ Built catalog with {count} unique companies (static lists)")

    print()
    print("=" * 80)
    print("CATALOG STATISTICS")
    print("=" * 80)
    print()

    companies = catalog.get_all_companies()

    # Count by source
    sources = {}
    for company in companies:
        source = company.get("source", "Unknown")
        sources[source] = sources.get(source, 0) + 1

    print("Companies by source:")
    for source, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  {source:<30} {count:>5} companies")

    print()

    # Count by sector (if available)
    sectors = {}
    for company in companies:
        sector = company.get("sector", "Unknown")
        if sector and sector != "Unknown":
            sectors[sector] = sectors.get(sector, 0) + 1

    if sectors:
        print("Companies by sector:")
        for sector, count in sorted(sectors.items(), key=lambda x: -x[1])[:10]:
            print(f"  {sector:<40} {count:>5} companies")
        print()

    # Show sample companies
    print("=" * 80)
    print("SAMPLE COMPANIES")
    print("=" * 80)
    print()

    # Show first 20 companies
    print("First 20 companies:")
    print("-" * 80)
    print(f"{'Ticker':<12} {'Name':<45} {'Source':<20}")
    print("-" * 80)

    for company in companies[:20]:
        ticker = company.get("ticker", "")[:12]
        name = company.get("name", "")[:45]
        source = company.get("source", "")[:20]
        print(f"{ticker:<12} {name:<45} {source:<20}")

    print()

    # Test search functionality
    print("=" * 80)
    print("TESTING SEARCH FUNCTIONALITY")
    print("=" * 80)
    print()

    test_queries = ["AAPL", "TESLA", "MICRO", "SAP", "GOO"]

    for query in test_queries:
        results = catalog.search(query, limit=5)
        print(f"Search: '{query}' -> {len(results)} results")
        for i, company in enumerate(results[:3], 1):
            print(f"  {i}. {company.get('ticker')}: {company.get('name')}")
        print()

    # Export to JSON for inspection
    print("=" * 80)
    print("EXPORTING CATALOG")
    print("=" * 80)
    print()

    export_file = "/home/mateo/blog-DCF/company_catalog_export.json"
    try:
        with open(export_file, "w") as f:
            json.dump(
                {
                    "total_companies": len(companies),
                    "sources": sources,
                    "sectors": sectors,
                    "companies": companies[:100],  # First 100 for inspection
                },
                f,
                indent=2,
            )
        print(f"✅ Exported catalog to: {export_file}")
        print("   (First 100 companies for inspection)")
    except Exception as e:
        print(f"❌ Export failed: {e}")

    print()
    print("=" * 80)
    print(f"✅ CATALOG BUILD COMPLETE - {len(companies)} COMPANIES AVAILABLE")
    print("=" * 80)


if __name__ == "__main__":
    main()
