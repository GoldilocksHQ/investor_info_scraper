#!/usr/bin/env python
"""
Display investor data in a readable format.

This script reads the extracted investor data from JSON and displays
formatted information about investors, their investments, and related statistics.

Usage:
    python -m investor_parser.scripts.display_data
"""
import os
import json
import random
from datetime import datetime

def main():
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Load investor data
    data_file = "data/output/investor_data.json"
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            investors = json.load(f)
    except FileNotFoundError:
        print(f"Error: Data file '{data_file}' not found.")
        print("Please run batch_process.py first to generate the data.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not parse '{data_file}' as JSON.")
        return
    
    # Count investors with various fields
    total_investors = len(investors)
    investors_with_investments = sum(1 for inv in investors if inv.get('investments'))
    investors_with_roles = sum(1 for inv in investors if inv.get('roles'))
    investors_with_aoi = sum(1 for inv in investors if inv.get('areas_of_interest'))
    investors_with_coinvestors = sum(1 for inv in investors if inv.get('co_investors'))
    investors_with_scouts = sum(1 for inv in investors if inv.get('scouts_angels'))
    investors_with_fund_size = sum(1 for inv in investors if inv.get('current_fund_size'))
    
    # Print field statistics
    print("\n===== FIELD STATISTICS =====")
    print(f"Total investors: {total_investors}")
    print(f"Investors with investments: {investors_with_investments}")
    print(f"Investors with roles: {investors_with_roles}")
    print(f"Investors with areas of interest: {investors_with_aoi}")
    print(f"Investors with co-investors: {investors_with_coinvestors}")
    print(f"Investors with scouts & angels: {investors_with_scouts}")
    print(f"Investors with fund size: {investors_with_fund_size}")
    
    # Filter investors with investments
    investors_with_investments_list = [inv for inv in investors if inv.get('investments')]
    
    # Pick a random sample investor to display
    if investors_with_investments_list:
        sample_investor = random.choice(investors_with_investments_list)
        
        # Display sample investor details
        print(f"\n===== SAMPLE INVESTOR: {sample_investor['name']} =====")
        print(f"Position: {sample_investor.get('position', 'None')}")
        print(f"Firm: {sample_investor.get('firm', 'None')}")
        print(f"Location: {sample_investor.get('location', 'None')}")
        
        # Display roles if available
        if sample_investor.get('roles'):
            print(f"Roles: {', '.join(sample_investor['roles'])}")
        
        # Display areas of interest if available
        if sample_investor.get('areas_of_interest'):
            areas = sample_investor['areas_of_interest']
            if len(areas) > 5:
                print(f"Areas of Interest: {', '.join(areas[:5])}\nlth")
            else:
                print(f"Areas of Interest: {', '.join(areas)}")
        
        # Display co-investors if available
        if sample_investor.get('co_investors'):
            print(f"Co-investors: {', '.join(sample_investor['co_investors'])}")
        
        # Display investment range if available
        inv_range = sample_investor.get('investment_range', {})
        if inv_range.get('min') and inv_range.get('max'):
            print(f"Investment range: ${inv_range['min']:,} - ${inv_range['max']:,}")
        
        # Display sweet spot if available
        if inv_range.get('target'):
            print(f"Sweet spot: ${inv_range['target']:,}")
        
        # Display fund size if available
        if sample_investor.get('current_fund_size'):
            print(f"Current fund size: ${sample_investor['current_fund_size']:,}")
        
        # Display investment count
        investments = sample_investor.get('investments', [])
        print(f"\nInvestment count: {len(investments)}")
        
        # Display sample investments
        if investments:
            print("\nSample investments:\n")
            for i, inv in enumerate(investments[:3]):
                print(f"{i+1}. {inv['company']} (Total raised: {inv.get('total_raised', 'Unknown')})")
                
                # Display co-investors for this investment
                coinvestors = inv.get('coinvestors', [])
                if coinvestors:
                    print(f"   Co-investors: {', '.join(coinvestors)}")
                else:
                    print("   Co-investors: None identified")
                
                # Display investment rounds
                rounds = inv.get('rounds', [])
                if rounds:
                    print("   Rounds:")
                    for r in rounds:
                        lead_indicator = " (Lead)" if r.get('is_lead') else ""
                        print(f"   - {r.get('stage', 'Unknown')} ({r.get('date', 'Unknown')}): {r.get('amount', 'Unknown')}{lead_indicator}")
                else:
                    print("   Rounds: None identified")
        
        # Print all investors with investment counts
        print("\n===== ALL INVESTORS =====")
        investors_with_counts = []
        for inv in investors:
            if inv.get('investments'):
                investors_with_counts.append((inv['name'], len(inv['investments'])))
        
        # Sort by investment count (descending)
        investors_with_counts.sort(key=lambda x: x[1], reverse=True)
        
        # Display the investors
        for name, count in investors_with_counts:
            print(f"{name}: {count} investments")
    else:
        print("\nNo investors with investments found in the data.")

    # Log execution
    with open('logs/display.log', 'a', encoding='utf-8') as log:
        log.write(f"{datetime.now()} - Displayed data for {total_investors} investors\n")

if __name__ == "__main__":
    main() 