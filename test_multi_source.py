"""Test script for multi-source data providers."""

from src.data_providers import DataAggregator

# Create aggregator (will use Yahoo Finance by default, no API keys needed)
print("🔧 Initializing data aggregator...")
aggregator = DataAggregator()

print(f"📡 Available providers: {aggregator.get_available_providers()}")
print()

# Test connection
print("🔌 Testing connections...")
results = aggregator.test_all_connections()
for provider, status in results.items():
    emoji = "✅" if status else "❌"
    print(f"  {emoji} {provider}: {'Connected' if status else 'Failed'}")
print()

# Test fetching data
ticker = "AAPL"
print(f"📊 Fetching data for {ticker}...")
print()

# Test strategy 1: First available
print("Strategy 1: First Available (fastest)")
data1 = aggregator.get_financial_data(ticker, years=5, strategy="first_available")
if data1:
    print(f"  ✅ Source: {data1.data_source}")
    print(f"  ✅ Company: {data1.company_name}")
    print(f"  ✅ Price: ${data1.current_price}")
    print(f"  ✅ Completeness: {data1.data_completeness:.1f}%")
    print(f"  ✅ Confidence: {data1.confidence_score:.1f}%")
    fcf = data1.calculate_fcf()
    if fcf:
        print(f"  ✅ FCF data points: {len(fcf)}")
else:
    print("  ❌ No data found")
print()

# Test strategy 2: Best quality (if multiple providers available)
if len(aggregator.providers) > 1:
    print("Strategy 2: Best Quality (compares all sources)")
    data2 = aggregator.get_financial_data(ticker, years=5, strategy="best_quality")
    if data2:
        print(f"  ✅ Source: {data2.data_source}")
        print(f"  ✅ Completeness: {data2.data_completeness:.1f}%")
        print(f"  ✅ Confidence: {data2.confidence_score:.1f}%")
    print()

print("✨ Test completed!")
print()
print(
    "💡 To enable more data sources, configure API keys in .env or .streamlit/secrets.toml"
)
print("   See docs/MULTI_SOURCE_DATA.md for details")
