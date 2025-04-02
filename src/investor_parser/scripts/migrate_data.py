#!/usr/bin/env python
"""
Migrate data from legacy 'output/' directory to new 'data/' directory.

This script is used to consolidate all data storage to the 'data/' folder.
It performs the following actions:
1. Moves HTML files from output/html/ to data/html/
2. Moves investor_urls.txt from output/ to data/
3. Moves investor_data.json from output/ to data/output/
4. Updates queue state files to use new paths

Usage:
    python -m src.investor_parser.scripts.migrate_data

After running this script, the old output/ directory can be safely deleted
if all data was successfully migrated.
"""

import os
import shutil
import glob
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/migration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure directories exist
os.makedirs("data/html", exist_ok=True)
os.makedirs("data/output", exist_ok=True)
os.makedirs("logs", exist_ok=True)

def migrate_html_files():
    """
    Migrate HTML files from output/html/ to data/html/.
    """
    if not os.path.exists("output/html"):
        logger.info("No output/html directory found, skipping HTML migration")
        return 0
    
    html_files = glob.glob("output/html/*.html")
    if not html_files:
        logger.info("No HTML files found in output/html/")
        return 0
    
    logger.info(f"Found {len(html_files)} HTML files to migrate")
    
    migrated_count = 0
    for html_file in html_files:
        filename = os.path.basename(html_file)
        dest_path = os.path.join("data/html", filename)
        
        if os.path.exists(dest_path):
            logger.info(f"File already exists in data/html/: {filename}, skipping")
            continue
        
        try:
            shutil.copy2(html_file, dest_path)
            logger.info(f"Migrated {html_file} -> {dest_path}")
            migrated_count += 1
        except Exception as e:
            logger.error(f"Error migrating {html_file}: {str(e)}")
    
    logger.info(f"Successfully migrated {migrated_count} HTML files")
    return migrated_count

def migrate_investor_urls():
    """
    Migrate investor_urls.txt from output/ to data/.
    """
    source_file = "output/investor_urls.txt"
    dest_file = "data/investor_urls.txt"
    
    if not os.path.exists(source_file):
        logger.info(f"No {source_file} found, skipping migration")
        return False
    
    if os.path.exists(dest_file):
        logger.info(f"{dest_file} already exists, checking for differences")
        
        # Check if files are different
        try:
            with open(source_file, "r") as src, open(dest_file, "r") as dst:
                src_content = src.read()
                dst_content = dst.read()
                
                if src_content == dst_content:
                    logger.info(f"Files are identical, no migration needed")
                    return True
                else:
                    logger.info(f"Files are different, merging content")
                    
                    # Merge the files (keeping unique URLs)
                    src_urls = set(src_content.strip().split("\n"))
                    dst_urls = set(dst_content.strip().split("\n"))
                    all_urls = sorted(src_urls.union(dst_urls))
                    
                    with open(dest_file, "w") as f:
                        f.write("\n".join(all_urls))
                    
                    logger.info(f"Merged URL files, total URLs: {len(all_urls)}")
                    return True
        except Exception as e:
            logger.error(f"Error comparing files: {str(e)}")
            return False
    
    try:
        shutil.copy2(source_file, dest_file)
        logger.info(f"Migrated {source_file} -> {dest_file}")
        return True
    except Exception as e:
        logger.error(f"Error migrating {source_file}: {str(e)}")
        return False

def migrate_investor_data():
    """
    Migrate investor_data.json from output/ to data/output/.
    """
    source_file = "output/investor_data.json"
    dest_file = "data/output/investor_data.json"
    
    if not os.path.exists(source_file):
        logger.info(f"No {source_file} found, skipping migration")
        return False
    
    if os.path.exists(dest_file):
        logger.info(f"{dest_file} already exists, checking if source is newer")
        
        # Check file modification times
        src_mtime = os.path.getmtime(source_file)
        dst_mtime = os.path.getmtime(dest_file)
        
        if src_mtime <= dst_mtime:
            logger.info(f"Destination file is newer, no migration needed")
            return True
        
        logger.info(f"Source file is newer, updating destination")
    
    try:
        shutil.copy2(source_file, dest_file)
        logger.info(f"Migrated {source_file} -> {dest_file}")
        return True
    except Exception as e:
        logger.error(f"Error migrating {source_file}: {str(e)}")
        return False

def update_queue_state():
    """
    Update queue state file to use new paths.
    """
    state_file = "data/queue_state.json"
    
    if not os.path.exists(state_file):
        # Check if there's a legacy state file
        legacy_state_file = "output/queue_state.json"
        if os.path.exists(legacy_state_file):
            try:
                shutil.copy2(legacy_state_file, state_file)
                logger.info(f"Migrated {legacy_state_file} -> {state_file}")
            except Exception as e:
                logger.error(f"Error migrating {legacy_state_file}: {str(e)}")
                return False
        else:
            logger.info(f"No queue state file found, skipping update")
            return True
    
    # Update output paths in the queue state
    try:
        with open(state_file, "r") as f:
            data = json.load(f)
        
        # Update paths in items
        updated = 0
        for item in data.get("items", []):
            if item.get("output_path") and "output/html" in item["output_path"]:
                old_path = item["output_path"]
                new_path = old_path.replace("output/html", "data/html")
                item["output_path"] = new_path
                updated += 1
        
        if updated > 0:
            logger.info(f"Updated {updated} paths in queue state")
            
            # Save updated state
            with open(state_file, "w") as f:
                json.dump(data, f, indent=2)
        else:
            logger.info("No paths needed to be updated in queue state")
        
        return True
    except Exception as e:
        logger.error(f"Error updating queue state: {str(e)}")
        return False

def main():
    """
    Main function to migrate all data.
    """
    logger.info("Starting data migration from output/ to data/")
    
    # Migrate HTML files
    html_count = migrate_html_files()
    
    # Migrate investor URLs
    urls_migrated = migrate_investor_urls()
    
    # Migrate investor data
    data_migrated = migrate_investor_data()
    
    # Update queue state
    state_updated = update_queue_state()
    
    # Summary
    logger.info("\nMigration summary:")
    logger.info(f"- HTML files: {html_count} migrated")
    logger.info(f"- Investor URLs: {'Success' if urls_migrated else 'Failed'}")
    logger.info(f"- Investor data: {'Success' if data_migrated else 'Failed'}")
    logger.info(f"- Queue state: {'Success' if state_updated else 'Failed'}")
    
    if html_count > 0 and urls_migrated and data_migrated and state_updated:
        logger.info("\nAll data successfully migrated. You can now safely remove the output/ directory.")
        logger.info("To remove output/ directory, run: rm -rf output/")
    else:
        logger.warning("\nSome migration steps failed. Please check the logs and fix any issues.")

if __name__ == "__main__":
    main() 