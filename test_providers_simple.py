"""Simple test for data providers without Streamlit dependency."""

from src.data_providers.yahoo_provider import YahooFinanceProvider
from src.data_providers.alpha_vantage_provider import AlphaVantageProvider
from src.data_providers import DataAggregator

print("=" * 60)
print("Testing Data Providers")
print("=" * 60)
print()

# Test 1: Yahoo Finance (always available)
print("1. Testing Yahoo Finance Provider...")
yahoo = YahooFinanceProvider()
print(f"   Available: {yahoo.is_available()}")
print(f"   Priority: {yahoo.get_priority()}")
print(f"   Connection: {yahoo.test_connection()}")
data = yahoo.get_financial_data("AAPL", years=3)
if data:
    print(f"   ✅ Got data for {data.ticker}")
    print(f"   ✅ Company: {data.company_name}")
    print(f"   ✅ Price: ${data.current_price:.2f}")
    fcf = data.calculate_fcf()
    print(f"   ✅ FCF points: {len(fcf) if fcf else 0}")
print()

# Test 2: Alpha Vantage
print("2. Testing Alpha Vantage Provider...")
av_key = "E4UZIP8B15YJMHKU"
alpha = AlphaVantageProvider(api_key=av_key)
print(f"   Available: {alpha.is_available()}")
print(f"   Priority: {alpha.get_priority()}")
print("   Testing connection (this may take a few seconds)...")
connection = alpha.test_connection()
print(f"   Connection: {connection}")

if connection:
    print("   Fetching AAPL data...")
    data = alpha.get_financial_data("AAPL", years=3)
    if data:
        print(f"   ✅ Got data for {data.ticker}")
        print(f"   ✅ Company: {data.company_name}")
        print(f"   ✅ Completeness: {data.data_completeness:.1f}%")
        print(f"   ✅ Confidence: {data.confidence_score:.1f}%")
        fcf = data.calculate_fcf()
        print(f"   ✅ FCF points: {len(fcf) if fcf else 0}")
    else:
        print("   ❌ Could not fetch data")
else:
    print("   ⚠️ Alpha Vantage connection failed - check API key")
print()

# Test 3: Aggregator with manual config
print("3. Testing DataAggregator...")
config = {"alpha_vantage": av_key}
aggregator = DataAggregator(config)
print(f"   Available providers: {aggregator.get_available_providers()}")
print()

print("4. Fetching with 'best_quality' strategy...")
data = aggregator.get_financial_data("AAPL", years=3, strategy="best_quality")
if data:
    print(f"   ✅ Source: {data.data_source}")
    print(f"   ✅ Company: {data.company_name}")
    print(f"   ✅ Price: ${data.current_price:.2f}")
    print(f"   ✅ Completeness: {data.data_completeness:.1f}%")
    print(f"   ✅ Confidence: {data.confidence_score:.1f}%")
    fcf = data.calculate_fcf()
    print(f"   ✅ FCF points: {len(fcf) if fcf else 0}")
    if fcf:
        print(f"   ✅ FCF values: {[f'{x/1e9:.2f}B' for x in fcf[:3]]}")
print()

print("=" * 60)
print("✨ Test completed!")
print("=" * 60)
