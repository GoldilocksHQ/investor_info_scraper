#!/usr/bin/env python

import os
import json
import logging
import shutil
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class URLItem:
    """
    Represents a URL to be processed with its metadata.
    """
    url: str
    name: str
    status: str = "pending"  # pending, in_progress, completed, failed
    retry_count: int = 0
    last_attempt: Optional[str] = None
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'URLItem':
        """Create from dictionary."""
        return cls(**data)

class URLQueue:
    """
    Manages a queue of URLs to be processed.
    Supports saving/loading state and tracking progress.
    """
    
    def __init__(self, state_file: str = "data/queue_state.json"):
        """
        Initialize the URL queue.
        
        Args:
            state_file: Path to file for saving queue state
        """
        self.state_file = state_file
        self.items: List[URLItem] = []
        self.current_index = 0
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        # Try to load existing state
        if not self.load_state():
            # Check for legacy state file in output directory
            legacy_state_file = self.state_file.replace("data/", "output/")
            if os.path.exists(legacy_state_file):
                logger.info(f"Found legacy state file at {legacy_state_file}")
                try:
                    # Copy the legacy state file to the new location
                    shutil.copy2(legacy_state_file, self.state_file)
                    logger.info(f"Migrated state file from {legacy_state_file} to {self.state_file}")
                    
                    # Try loading again
                    self.load_state()
                    
                    # Update output paths to new directory structure
                    self._update_output_paths()
                except Exception as e:
                    logger.error(f"Error migrating state file: {str(e)}")
    
    def _update_output_paths(self) -> None:
        """
        Update output paths in queue items to use data/ instead of output/.
        """
        updated = 0
        for item in self.items:
            if item.output_path and "output/html" in item.output_path:
                # Update output path
                new_path = item.output_path.replace("output/html", "data/html")
                
                # Check if the new path exists, or if we need to migrate the file
                if os.path.exists(new_path):
                    item.output_path = new_path
                    updated += 1
                elif os.path.exists(item.output_path):
                    # Ensure data/html directory exists
                    os.makedirs("data/html", exist_ok=True)
                    
                    try:
                        # Copy the file
                        shutil.copy2(item.output_path, new_path)
                        item.output_path = new_path
                        updated += 1
                    except Exception as e:
                        logger.error(f"Error migrating file {item.output_path}: {str(e)}")
        
        if updated > 0:
            logger.info(f"Updated {updated} output paths")
            self.save_state()
    
    def load_state(self) -> bool:
        """
        Load queue state from file if it exists.
        
        Returns:
            True if state was loaded, False otherwise
        """
        if not os.path.exists(self.state_file):
            logger.info(f"No state file found at {self.state_file}")
            return False
            
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                
            self.items = [URLItem.from_dict(item) for item in data.get('items', [])]
            self.current_index = data.get('current_index', 0)
            
            # Make sure current_index is valid
            if self.current_index >= len(self.items):
                self.current_index = 0
                
            logger.info(f"Loaded {len(self.items)} URLs from state file")
            return True
            
        except Exception as e:
            logger.error(f"Error loading state: {str(e)}")
            return False
    
    def save_state(self) -> bool:
        """
        Save current queue state to file.
        
        Returns:
            True if state was saved, False otherwise
        """
        try:
            data = {
                'items': [item.to_dict() for item in self.items],
                'current_index': self.current_index,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved queue state to {self.state_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving state: {str(e)}")
            return False
    
    def add_url(self, url: str, name: str) -> None:
        """
        Add a URL to the queue if it doesn't exist.
        
        Args:
            url: URL to add
            name: Investor name or identifier
        """
        # Check if URL already exists
        if any(item.url == url for item in self.items):
            logger.info(f"URL already in queue: {url}")
            return
            
        # Add new URL
        self.items.append(URLItem(url=url, name=name))
        logger.info(f"Added URL to queue: {url} - Total items in queue: {len(self.items)}")
        
        # Save state
        self.save_state()
    
    def add_urls_from_file(self, file_path: str) -> int:
        """
        Add URLs from a text file, one URL per line.
        Expected format: name,url
        
        Args:
            file_path: Path to text file with URLs
            
        Returns:
            Number of URLs added
        """
        if not os.path.exists(file_path):
            logger.error(f"URL file not found: {file_path}")
            
            # Check for legacy URL file in output directory
            legacy_file_path = file_path.replace("data/", "output/")
            if os.path.exists(legacy_file_path):
                logger.info(f"Found legacy URL file at {legacy_file_path}")
                
                # Copy the legacy file to the new location
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                try:
                    shutil.copy2(legacy_file_path, file_path)
                    logger.info(f"Migrated URL file from {legacy_file_path} to {file_path}")
                except Exception as e:
                    logger.error(f"Error migrating URL file: {str(e)}")
                    return 0
            else:
                return 0
            
        try:
            added_count = 0
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                        
                    # Parse line - expected format: name,url
                    # If only URL is provided, extract name from URL
                    parts = line.split(',', 1)
                    if len(parts) == 2:
                        name, url = parts
                    else:
                        url = parts[0]
                        # Extract name from URL
                        name = url.split('/')[-1].replace('investors-', '').replace('-', ' ')
                        
                    self.add_url(url, name)
                    added_count += 1
                    
            logger.info(f"Added {added_count} URLs from {file_path}")
            return added_count
            
        except Exception as e:
            logger.error(f"Error reading URL file: {str(e)}")
            return 0
    
    def get_next_url(self) -> Optional[Tuple[URLItem, int]]:
        """
        Get the next URL to process.
        
        Returns:
            Tuple of (URLItem, index) or None if no more URLs
        """
        if not self.items:
            logger.info("Queue is empty")
            return None
            
        # Find the next pending item
        start_index = self.current_index
        
        while True:
            item = self.items[self.current_index]
            
            # Move to the next index for next time
            next_index = self.current_index
            self.current_index = (self.current_index + 1) % len(self.items)
            
            # If item is pending or failed (but not max retries), return it
            if item.status == "pending" or (item.status == "failed" and item.retry_count < 3):
                return item, next_index
                
            # If we've checked all items, stop
            if self.current_index == start_index:
                logger.info("No more URLs to process")
                return None
    
    def update_status(self, index: int, status: str, 
                      error_message: Optional[str] = None,
                      output_path: Optional[str] = None) -> None:
        """
        Update the status of a URL.
        
        Args:
            index: Index of the URL in the queue
            status: New status - pending, in_progress, completed, failed
            error_message: Error message if failed
            output_path: Path to saved output file if completed
        """
        if index < 0 or index >= len(self.items):
            logger.error(f"Invalid index: {index}")
            return
            
        item = self.items[index]
        
        # Update status
        item.status = status
        item.last_attempt = datetime.now().isoformat()
        
        # Update error message if provided
        if error_message:
            item.error_message = error_message
            
        # Update output path if provided
        if output_path:
            item.output_path = output_path
            
        # Increment retry count if failed
        if status == "failed":
            item.retry_count += 1
            
        # Save state
        self.save_state()
        
        logger.info(f"Updated status of {item.url} to {status}")
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about the queue.
        
        Returns:
            Dictionary with statistics
        """
        if not self.items:
            return {
                'total': 0,
                'pending': 0,
                'in_progress': 0,
                'completed': 0,
                'failed': 0
            }
            
        stats = {
            'total': len(self.items),
            'pending': sum(1 for item in self.items if item.status == "pending"),
            'in_progress': sum(1 for item in self.items if item.status == "in_progress"),
            'completed': sum(1 for item in self.items if item.status == "completed"),
            'failed': sum(1 for item in self.items if item.status == "failed")
        }
        
        # Calculate percentages
        if stats['total'] > 0:
            stats['completed_pct'] = round(stats['completed'] / stats['total'] * 100, 1)
            stats['failed_pct'] = round(stats['failed'] / stats['total'] * 100, 1)
            
        return stats 