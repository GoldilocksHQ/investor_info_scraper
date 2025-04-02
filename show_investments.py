#!/usr/bin/env python
import json
import random
from typing import Dict, Any, List

def load_data(file_path: str = "output/investor_data.json") -> List[Dict[str, Any]]:
    """Load investor data from JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def display_sample_investor(investors: List[Dict[str, Any]]):
    """Display details for a sample investor with investments."""
    # Find investors with investments
    investors_with_investments = [inv for inv in investors if inv.get("investments")]
    
    if not investors_with_investments:
        print("No investors with investments found.")
        return
    
    # Select a random investor with investments
    investor = random.choice(investors_with_investments)
    
    print(f"\n===== SAMPLE INVESTOR: {investor.get('name', 'Unknown')} =====")
    print(f"Position: {investor.get('position', 'Unknown')}")
    print(f"Firm: {investor.get('firm', 'Unknown')}")
    print(f"Location: {investor.get('location', 'Unknown')}")
    
    # Print roles
    if investor.get("roles"):
        print(f"Roles: {', '.join(investor.get('roles', []))}")
    
    # Print areas of interest
    if investor.get("areas_of_interest"):
        print(f"Areas of Interest: {', '.join(investor.get('areas_of_interest', []))}")
    
    # Print co-investors
    if investor.get("co_investors"):
        print(f"Co-investors: {', '.join(investor.get('co_investors', []))}")
    
    # Print investment range
    inv_range = investor.get("investment_range", {})
    if inv_range.get("min") and inv_range.get("max"):
        print(f"Investment range: ${inv_range.get('min'):,} - ${inv_range.get('max'):,}")
    
    if inv_range.get("target"):
        print(f"Sweet spot: ${inv_range.get('target'):,}")
    
    # Print fund size
    if investor.get("current_fund_size"):
        print(f"Current fund size: ${investor.get('current_fund_size'):,}")
    
    # Print investment count
    investment_count = len(investor.get("investments", []))
    print(f"\nInvestment count: {investment_count}")
    
    # Display a few sample investments
    print("\nSample investments:")
    for i, inv in enumerate(investor.get("investments", [])[:3]):
        print(f"\n{i+1}. {inv.get('company', 'Unknown')} (Total raised: {inv.get('total_raised', 'Unknown')})")
        
        # Display co-investors for this investment
        if inv.get("coinvestors"):
            print(f"   Co-investors: {', '.join(inv.get('coinvestors', []))}")
        else:
            print("   Co-investors: None identified")
        
        # Display rounds
        if inv.get("rounds"):
            print(f"   Rounds:")
            for round_info in inv.get("rounds", []):
                lead_status = " (Lead)" if round_info.get("is_lead") else ""
                stage = round_info.get("stage", "Unknown")
                date = round_info.get("date", "Unknown date")
                amount = round_info.get("amount", "Unknown amount")
                print(f"   - {stage} ({date}): {amount}{lead_status}")
        else:
            print("   Rounds: None identified")

def display_all_investors_summary(investors: List[Dict[str, Any]]):
    """Display a summary of all investors and their investment counts."""
    # Sort investors by number of investments
    sorted_investors = sorted(
        investors, 
        key=lambda x: len(x.get("investments", [])), 
        reverse=True
    )
    
    print("\n===== ALL INVESTORS =====")
    for investor in sorted_investors:
        investment_count = len(investor.get("investments", []))
        if investment_count > 0:
            print(f"{investor.get('name', 'Unknown')}: {investment_count} investments")

def display_field_statistics(investors: List[Dict[str, Any]]):
    """Display statistics about fields extracted."""
    total = len(investors)
    with_investments = sum(1 for inv in investors if inv.get("investments"))
    roles_count = sum(1 for inv in investors if inv.get("roles"))
    areas_count = sum(1 for inv in investors if inv.get("areas_of_interest"))
    coinvestors_count = sum(1 for inv in investors if inv.get("co_investors"))
    scouts_count = sum(1 for inv in investors if inv.get("scouts_angels"))
    fund_size_count = sum(1 for inv in investors if inv.get("current_fund_size"))
    
    print("\n===== FIELD STATISTICS =====")
    print(f"Total investors: {total}")
    print(f"Investors with investments: {with_investments}")
    print(f"Investors with roles: {roles_count}")
    print(f"Investors with areas of interest: {areas_count}")
    print(f"Investors with co-investors: {coinvestors_count}")
    print(f"Investors with scouts & angels: {scouts_count}")
    print(f"Investors with fund size: {fund_size_count}")

def main():
    """Main function to display investor data."""
    try:
        investors = load_data()
        
        # Display field statistics
        display_field_statistics(investors)
        
        # Display sample investor
        display_sample_investor(investors)
        
        # Display all investors summary
        display_all_investors_summary(investors)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 