"""
Test script for FCF Quality Check system.

Tests FCF calculation, unit consistency, and quality validation
for multiple companies across different sectors.
"""

import sys

sys.path.insert(0, "/home/mateo/blog-DCF")

from src.utils.data_fetcher import get_fcf_data
from src.utils.fcf_quality_check import (
    validate_fcf_quality,
    generate_quality_report,
    get_quality_score,
)


def test_fcf_for_company(ticker: str, verbose: bool = False) -> dict:
    """Test FCF quality for a single company."""
    try:
        # Get FCF data
        base_fcf, historical_fcf, metadata = get_fcf_data(ticker, max_years=5)

        # Validate quality
        is_valid, warnings, metrics = validate_fcf_quality(
            ticker, base_fcf, historical_fcf, metadata
        )

        # Get score
        score, grade = get_quality_score(warnings, metrics)

        result = {
            "ticker": ticker,
            "base_fcf": base_fcf,
            "is_valid": is_valid,
            "score": score,
            "grade": grade,
            "warnings": warnings,
            "metrics": metrics,
            "data_source": metadata.get("data_source", "Unknown"),
        }

        if verbose:
            print(generate_quality_report(ticker, base_fcf, historical_fcf, metadata))
            print()

        return result

    except Exception as e:
        return {
            "ticker": ticker,
            "error": str(e),
            "is_valid": False,
            "score": 0,
            "grade": "F",
        }


def run_test_suite():
    """Run comprehensive test suite for FCF quality."""
    print("=" * 80)
    print("FCF QUALITY TEST SUITE")
    print("=" * 80)
    print()

    # Test companies across different sectors
    test_companies = [
        ("AAPL", "Technology - Mature"),
        ("MSFT", "Technology - Cloud"),
        ("NVDA", "Technology - Semiconductors"),
        ("LLY", "Healthcare - Pharma (High M&A)"),
        ("JPM", "Financial Services - Bank"),
        ("XOM", "Energy - Oil & Gas"),
        ("WMT", "Consumer Defensive - Retail"),
        ("TSLA", "Consumer Cyclical - Auto"),
        ("JNJ", "Healthcare - Diversified"),
        ("PG", "Consumer Defensive - CPG"),
    ]

    results = []

    print("Testing FCF quality for 10 companies...")
    print("-" * 80)
    print(
        f"{'Ticker':<8} {'FCF':<14} {'Score':<8} {'Grade':<8} {'Source':<35} {'Issues'}"
    )
    print("-" * 80)

    for ticker, description in test_companies:
        result = test_fcf_for_company(ticker, verbose=False)
        results.append(result)

        if "error" in result:
            print(
                f"{ticker:<8} {'ERROR':<14} {result['score']:<8} {result['grade']:<8} {'N/A':<35} {result['error'][:20]}"
            )
        else:
            fcf = result["base_fcf"]
            fcf_display = f"${fcf/1e9:.2f}B" if abs(fcf) > 1e9 else f"${fcf/1e6:.2f}M"

            issue_summary = (
                f"{len(result['warnings'])} warnings" if result["warnings"] else "✅"
            )

            print(
                f"{ticker:<8} {fcf_display:<14} {result['score']:<8.0f} {result['grade']:<8} {result['data_source'][:34]:<35} {issue_summary}"
            )

    print("-" * 80)
    print()

    # Summary statistics
    valid_results = [r for r in results if "error" not in r]

    if valid_results:
        avg_score = sum(r["score"] for r in valid_results) / len(valid_results)
        companies_with_issues = sum(1 for r in valid_results if r["warnings"])

        print("SUMMARY:")
        print(f"  Total companies tested: {len(results)}")
        print(f"  Successful: {len(valid_results)}")
        print(f"  Errors: {len(results) - len(valid_results)}")
        print(f"  Average quality score: {avg_score:.1f}/100")
        print(f"  Companies with warnings: {companies_with_issues}")
        print()

    # Show detailed reports for companies with issues
    companies_with_issues = [r for r in valid_results if r["warnings"]]

    if companies_with_issues:
        print("=" * 80)
        print("DETAILED REPORTS FOR COMPANIES WITH ISSUES:")
        print("=" * 80)
        print()

        for result in companies_with_issues:
            ticker = result["ticker"]
            base_fcf, historical_fcf, metadata = get_fcf_data(ticker, max_years=5)
            print(generate_quality_report(ticker, base_fcf, historical_fcf, metadata))
            print()

    # Test specific edge cases
    print("=" * 80)
    print("EDGE CASE TESTS:")
    print("=" * 80)
    print()

    edge_cases = [
        ("BRK.B", "Berkshire Hathaway (Holding Company)"),
        ("META", "Meta (High Cash Generation)"),
        ("BAC", "Bank of America (Financial)"),
    ]

    print("Testing edge cases...")
    print()

    for ticker, description in edge_cases:
        print(f"Testing {ticker} - {description}")
        result = test_fcf_for_company(ticker, verbose=True)

    print("=" * 80)
    print("✅ TEST SUITE COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    run_test_suite()
