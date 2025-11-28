"""Convert static company lists from Python to JSON format."""

import json
import re
from pathlib import Path


def extract_companies_from_python_file(file_path: Path) -> list[dict]:
    """Extract company dictionaries from Python file."""
    content = file_path.read_text()

    # Find all company dictionaries
    # Pattern matches: {"ticker": "AAPL", "name": "...", "sector": "..."}
    pattern = r'\{\s*"ticker":\s*"([^"]+)",\s*"name":\s*"([^"]+)",\s*"sector":\s*"([^"]+)"\s*\}'

    companies = []
    for match in re.finditer(pattern, content):
        ticker, name, sector = match.groups()
        companies.append({
            "ticker": ticker,
            "name": name,
            "sector": sector
        })

    # Remove duplicates based on ticker
    unique_companies = {c["ticker"]: c for c in companies}
    companies_list = list(unique_companies.values())

    # Sort by ticker
    companies_list.sort(key=lambda x: x["ticker"])

    return companies_list


def main():
    """Convert static companies to JSON."""
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / "src" / "data_providers" / "static_companies.py"
    output_file = base_dir / "data" / "companies.json"

    print(f"Reading from: {input_file}")
    companies = extract_companies_from_python_file(input_file)

    print(f"Extracted {len(companies)} unique companies")

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(companies, f, indent=2, ensure_ascii=False)

    print(f"Saved to: {output_file}")
    print(f"File size: {output_file.stat().st_size / 1024:.2f} KB")

    # Print sample
    print("\nFirst 5 companies:")
    for company in companies[:5]:
        print(f"  {company['ticker']}: {company['name']} ({company['sector']})")


if __name__ == "__main__":
    main()
