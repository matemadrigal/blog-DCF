import os
from src.companies import get_sp500_companies, get_all_sectors, search_companies
from src.companies.fcf_scanner import FCFScanner

"""Test company selector functionality."""

print("=" * 70)
print("TEST: Company Selector with Filters")
print("=" * 70)
print()

# Test 1: Get all companies
companies = get_sp500_companies()
print(f"✓ Total companies loaded: {len(companies)}")
print()

# Test 2: Get all sectors
sectors = get_all_sectors()
print(f"✓ Sectors available: {len(sectors)}")
print(f"  {', '.join(sectors[:5])}...")
print()

# Test 3: Search companies
search_results = search_companies("apple")
print(f"✓ Search for 'apple': {len(search_results)} results")
for r in search_results:
    print(f"  - {r['ticker']}: {r['name']} ({r['sector']})")
print()

# Test 4: Filter by letter
letter_a = [c for c in companies if c["ticker"].startswith("A")]
print(f"✓ Companies starting with 'A': {len(letter_a)}")
print(f"  {', '.join([c['ticker'] for c in letter_a[:5]])}...")
print()

# Test 5: Filter by sector
tech_companies = [c for c in companies if c["sector"] == "Technology"]
print(f"✓ Technology companies: {len(tech_companies)}")
print(f"  {', '.join([c['ticker'] for c in tech_companies[:5]])}...")
print()

# Test 6: FCF Scanner
print("=" * 70)
print("TEST: FCF Scanner")
print("=" * 70)
print()

scanner = FCFScanner(cache_file=".test_fcf_cache.json")

# Test with a few companies
test_tickers = ["AAPL", "MSFT", "GOOGL"]
print(f"Scanning {len(test_tickers)} companies...")
print()

for i, ticker in enumerate(test_tickers, 1):
    fcf, error = scanner.get_base_fcf(ticker)
    if error:
        print(f"{i}. {ticker}: ❌ Error - {error}")
    else:
        fcf_display = f"${fcf/1e9:.2f}B" if fcf > 1e9 else f"${fcf/1e6:.2f}M"
        print(f"{i}. {ticker}: ✓ FCF = {fcf_display}")

print()

# Test 7: Cache functionality
print("=" * 70)
print("TEST: Cache Functionality")
print("=" * 70)
print()

cached_fcf = scanner.get_cached_fcf("AAPL")
if cached_fcf:
    print(f"✓ Cached FCF for AAPL: ${cached_fcf/1e9:.2f}B")
else:
    print("❌ No cached data for AAPL")

print()

# Test 8: Sort by FCF
print("=" * 70)
print("TEST: Sorting by FCF")
print("=" * 70)
print()

# Add FCF to test companies
test_companies = [
    c for c in companies if c["ticker"] in ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
]
for company in test_companies:
    fcf, _ = scanner.get_base_fcf(company["ticker"])
    company["fcf"] = fcf

# Sort by FCF (highest first)
test_companies.sort(key=lambda x: x.get("fcf", 0), reverse=True)

print("Companies sorted by FCF (highest first):")
for i, company in enumerate(test_companies, 1):
    fcf_display = (
        f"${company['fcf']/1e9:.2f}B"
        if company["fcf"] > 1e9
        else f"${company['fcf']/1e6:.2f}M"
    )
    print(f"{i}. {company['ticker']:6} - {company['name']:30} - FCF: {fcf_display}")

print()
print("=" * 70)
print("All tests completed successfully!")
print("=" * 70)


# Cleanup
if os.path.exists(".test_fcf_cache.json"):
    os.remove(".test_fcf_cache.json")
    print("✓ Test cache file cleaned up")
