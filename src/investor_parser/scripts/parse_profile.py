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

# Try to import from src structure (if installed as package)
try:
    from src.investor_parser.core.parser import InvestorProfileParser
except ImportError:
    # Fallback to local import
    sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))
    from custom_parser import InvestorProfileParser

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
    print(f"Name: {data.get('name', 'Unknown')}")
    print(f"Position: {data.get('position', 'None')}")
    print(f"Firm: {data.get('firm', 'None')}")
    print(f"Location: {data.get('location', 'None')}")
    print(f"Extraction method: {data.get('extraction_method', 'Unknown')}")
    
    print(f"Roles: {', '.join(data.get('roles', []))}")
    print(f"Areas of Interest: {', '.join(data.get('areas_of_interest', []))}")
    
    if 'co_investors' in data and data['co_investors']:
        print(f"Co-investors: {', '.join(data['co_investors'][:5])}")
    else:
        print("Co-investors: None")
        
    if 'scouts_angels' in data and data['scouts_angels']:
        print(f"Scouts & Angels: {', '.join(data['scouts_angels'][:5])}")
    else:
        print("Scouts & Angels: None")
    
    investment_range = data.get('investment_range', {})
    if investment_range.get('min') and investment_range.get('max'):
        print(f"Investment range: ${investment_range['min']:,} - ${investment_range['max']:,}")
    
    if investment_range.get('target'):
        print(f"Sweet spot: ${investment_range['target']:,}")
    
    if data.get('current_fund_size'):
        print(f"Current fund size: ${data['current_fund_size']:,}")
    
    # Show a few sample investments
    investments = data.get('investments', [])
    print(f"\nInvestments ({len(investments)} total):")
    
    if not investments:
        print("  No investment data available")
    else:
        for i, inv in enumerate(investments[:3]):
            print(f"\n{i+1}. {inv.get('company', 'Unknown')} (Total raised: {inv.get('total_raised', 'Unknown')})")
            
            coinvestors = inv.get('coinvestors', [])
            if coinvestors:
                print(f"   Co-investors: {', '.join(coinvestors[:3])}")
            else:
                print("   Co-investors: None identified")
                
            print(f"   Rounds:")
            rounds = inv.get('rounds', [])
            if not rounds:
                print("     No round data available")
            else:
                for round in rounds[:2]:
                    lead_status = " (Lead)" if round.get('is_lead') else ""
                    print(f"   - {round.get('stage', 'Unknown')} ({round.get('date', 'Unknown')}): {round.get('amount', 'Unknown')}{lead_status}")
    
    # Save the result to a JSON file for inspection
    output_file = "data/output/parsed_investor.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"\nResult saved to {output_file}")

if __name__ == "__main__":
    main() 