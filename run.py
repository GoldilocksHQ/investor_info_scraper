#!/usr/bin/env python
"""
Main entry point for the investor profile parser.

This script provides a command-line interface to the various
functionalities of the investor profile parser.

Usage:
    python run.py [command]

Commands:
    process   - Process all investor profiles in data/html
    profile   - Parse a single investor profile
    display   - Display investor data
    migrate   - Migrate data from output/ to data/
    rescrape  - Check for and rescrape missing HTML files
    help      - Show this help message

Examples:
    python run.py process
    python run.py profile data/html/investors-rick-thompson.html
    python run.py display
    python run.py migrate
    python run.py rescrape
"""
import os
import sys
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Investor Profile Scraper")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape investor profiles")
    scrape_parser.add_argument("--url-file", default="data/investor_urls.txt", help="File with URLs to scrape")
    scrape_parser.add_argument("--no-proxy", action="store_true", help="Disable proxy usage")
    scrape_parser.add_argument("--limit", type=int, help="Limit number of URLs to process")
    scrape_parser.add_argument("--min-delay", type=float, help="Minimum delay between requests in seconds")
    scrape_parser.add_argument("--max-delay", type=float, help="Maximum delay between requests in seconds")
    
    # Parse command
    parse_parser = subparsers.add_parser("parse", help="Parse HTML files")
    
    # Process command (scrape + parse)
    process_parser = subparsers.add_parser("process", help="Run end-to-end process")
    process_parser.add_argument("--url-file", default="data/investor_urls.txt", help="File with URLs to scrape")
    process_parser.add_argument("--no-proxy", action="store_true", help="Disable proxy usage")
    process_parser.add_argument("--limit", type=int, help="Limit number of URLs to process")
    process_parser.add_argument("--skip-scrape", action="store_true", help="Skip scraping and only run parsing")
    process_parser.add_argument("--skip-parse", action="store_true", help="Skip parsing and only run scraping")
    process_parser.add_argument("--check-missing", action="store_true", help="Check and rescrape missing HTML files")
    process_parser.add_argument("--min-delay", type=float, help="Minimum delay between requests in seconds")
    process_parser.add_argument("--max-delay", type=float, help="Maximum delay between requests in seconds")
    
    # Display command
    display_parser = subparsers.add_parser("display", help="Display investor data")
    
    # Profile command
    profile_parser = subparsers.add_parser("profile", help="Parse a single investor profile")
    profile_parser.add_argument("file", help="HTML file to parse")
    
    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Migrate data from output/ to data/")
    
    # Rescrape command
    rescrape_parser = subparsers.add_parser("rescrape", help="Check for and rescrape missing HTML files")
    rescrape_parser.add_argument("--url-file", default="data/investor_urls.txt", help="File with URLs to check")
    rescrape_parser.add_argument("--no-proxy", action="store_true", help="Disable proxy usage")
    rescrape_parser.add_argument("--limit", type=int, help="Limit number of URLs to rescrape")
    rescrape_parser.add_argument("--min-delay", type=float, help="Minimum delay between requests in seconds")
    rescrape_parser.add_argument("--max-delay", type=float, help="Maximum delay between requests in seconds")
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Set Python path to include the src directory
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Execute the appropriate command
    if args.command == "scrape":
        cmd = [sys.executable, "-m", "src.investor_parser.scripts.scrape_profiles"]
        if args.url_file:
            cmd.extend(["--url-file", args.url_file])
        if args.no_proxy:
            cmd.append("--no-proxy")
        if args.limit:
            cmd.extend(["--limit", str(args.limit)])
        if args.min_delay is not None:
            cmd.extend(["--min-delay", str(args.min_delay)])
        if args.max_delay is not None:
            cmd.extend(["--max-delay", str(args.max_delay)])
    elif args.command == "parse":
        cmd = [sys.executable, "-m", "src.investor_parser.scripts.parse_all"]
    elif args.command == "process":
        cmd = [sys.executable, "-m", "src.investor_parser.scripts.process_all"]
        if args.url_file:
            cmd.extend(["--url-file", args.url_file])
        if args.no_proxy:
            cmd.append("--no-proxy")
        if args.limit:
            cmd.extend(["--limit", str(args.limit)])
        if args.skip_scrape:
            cmd.append("--skip-scrape")
        if args.skip_parse:
            cmd.append("--skip-parse")
        if args.check_missing:
            cmd.append("--check-missing")
        if args.min_delay is not None:
            cmd.extend(["--min-delay", str(args.min_delay)])
        if args.max_delay is not None:
            cmd.extend(["--max-delay", str(args.max_delay)])
    elif args.command == "display":
        cmd = [sys.executable, "-m", "src.investor_parser.scripts.display_data"]
    elif args.command == "profile":
        cmd = [sys.executable, "-m", "src.investor_parser.scripts.parse_profile", args.file]
    elif args.command == "migrate":
        cmd = [sys.executable, "-m", "src.investor_parser.scripts.migrate_data"]
    elif args.command == "rescrape":
        cmd = [sys.executable, "-m", "src.investor_parser.scripts.rescrape_missing"]
        if args.url_file:
            cmd.extend(["--url-file", args.url_file])
        if args.no_proxy:
            cmd.append("--no-proxy")
        if args.limit:
            cmd.extend(["--limit", str(args.limit)])
        if args.min_delay is not None:
            cmd.extend(["--min-delay", str(args.min_delay)])
        if args.max_delay is not None:
            cmd.extend(["--max-delay", str(args.max_delay)])
    else:
        print(f"Unknown command: {args.command}")
        return
    
    # Run the command
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main() 