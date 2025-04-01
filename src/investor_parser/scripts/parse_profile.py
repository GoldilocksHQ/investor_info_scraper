#!/usr/bin/env python
"""
Parse a single investor profile HTML file and display the extracted data.

This script is useful for testing the parser on individual investor profiles.
It extracts and displays the key information from an investor profile.

Usage:
    python -m investor_parser.scripts.parse_profile [html_file]

    If no html_file is provided, it defaults to Rick Thompson's profile.
"""
import os
import sys
import json
from investor_parser.core.parser import InvestorProfileParser

def main():
    # Create output and logs directories if they don't exist
    os.makedirs('data/output', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Default to Rick Thompson's profile if no arg provided
    html_file = sys.argv[1] if len(sys.argv) > 1 else "data/html/investors-rick-thompson.html"
    
    if not os.path.exists(html_file):
        print(f"File not found: {html_file}")
        sys.exit(1)
    
    # Read the HTML file
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parse the investor profile
    parser = InvestorProfileParser(html_content, html_file)
    data = parser.parse()
    
    # Display the extracted information
    print(f"Name: {data['name']}")
    print(f"Position: {data['position']}")
    print(f"Firm: {data['firm']}")
    print(f"Location: {data['location']}")
    print(f"Extraction method: {data['extraction_method']}")
    
    print(f"Roles: {', '.join(data['roles'])}")
    print(f"Areas of Interest: {', '.join(data['areas_of_interest'])}")
    print(f"Co-investors: {', '.join(data['co_investors'][:5])}")
    print(f"Scouts & Angels: {', '.join(data['scouts_angels'][:5])}")
    
    if data['investment_range']['min'] and data['investment_range']['max']:
        print(f"Investment range: ${data['investment_range']['min']:,} - ${data['investment_range']['max']:,}")
    
    if data['investment_range']['target']:
        print(f"Sweet spot: ${data['investment_range']['target']:,}")
    
    if data['current_fund_size']:
        print(f"Current fund size: ${data['current_fund_size']:,}")
    
    # Show a few sample investments
    print(f"\nInvestments ({len(data['investments'])} total):")
    for i, inv in enumerate(data['investments'][:3]):
        print(f"\n{i+1}. {inv['company']} (Total raised: {inv['total_raised']})")
        print(f"   Co-investors: {', '.join(inv['coinvestors'][:3]) if inv['coinvestors'] else 'None identified'}")
        print(f"   Rounds:")
        for round in inv['rounds'][:2]:
            lead_status = " (Lead)" if round['is_lead'] else ""
            print(f"   - {round['stage']} ({round['date']}): {round['amount']}{lead_status}")
    
    # Save the result to a JSON file for inspection
    output_file = "data/output/parsed_investor.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"\nResult saved to {output_file}")

if __name__ == "__main__":
    main() 