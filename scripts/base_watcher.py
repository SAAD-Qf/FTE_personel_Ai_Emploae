"""
Base Watcher Module

Abstract base class for all watcher scripts in the AI Employee system.
All watchers follow the same pattern: monitor inputs → create action files.
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Any, Optional


class BaseWatcher(ABC):
    """
    Abstract base class for all AI Employee watchers.
    
    Watchers are lightweight Python scripts that run continuously,
    monitoring various inputs and creating actionable files for
    Claude Code to process.
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the watcher.
        
        Args:
            vault_path: Path to the Obsidian vault directory
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.inbox = self.vault_path / 'Inbox'
        self.logs = self.vault_path / 'Logs'
        self.check_interval = check_interval
        
        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Track processed items to avoid duplicates
        self.processed_ids: set = set()
        
        self.logger.info(f'{self.__class__.__name__} initialized')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Check interval: {check_interval}s')
    
    def _setup_logging(self):
        """Configure logging to file and console."""
        log_file = self.logs / f'{datetime.now().strftime("%Y-%m-%d")}.log'
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Setup logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    @abstractmethod
    def check_for_updates(self) -> List[Any]:
        """
        Check for new items to process.
        
        Returns:
            List of new items that need processing
            
        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError(
            "Subclasses must implement check_for_updates()"
        )
    
    @abstractmethod
    def create_action_file(self, item: Any) -> Optional[Path]:
        """
        Create a .md action file in the Needs_Action folder.
        
        Args:
            item: The item to create an action file for
            
        Returns:
            Path to the created file, or None if creation failed
            
        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError(
            "Subclasses must implement create_action_file()"
        )
    
    def run(self):
        """
        Main run loop for the watcher.
        
        Continuously checks for updates and creates action files.
        Runs until interrupted (Ctrl+C).
        """
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info('Press Ctrl+C to stop')
        
        try:
            while True:
                try:
                    # Check for new items
                    items = self.check_for_updates()
                    
                    if items:
                        self.logger.info(f'Found {len(items)} new item(s)')
                        
                        for item in items:
                            filepath = self.create_action_file(item)
                            if filepath:
                                self.logger.info(f'Created action file: {filepath.name}')
                    else:
                        self.logger.debug('No new items')
                    
                except Exception as e:
                    self.logger.error(f'Error processing items: {e}', exc_info=True)
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info(f'{self.__class__.__name__} stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}', exc_info=True)
            raise
        finally:
            self.logger.info(f'{self.__class__.__name__} shutting down')
    
    def generate_frontmatter(self, item_type: str, **kwargs) -> str:
        """
        Generate YAML frontmatter for action files.
        
        Args:
            item_type: Type of item (email, whatsapp, file_drop, etc.)
            **kwargs: Additional frontmatter fields
            
        Returns:
            Formatted YAML frontmatter string
        """
        frontmatter = [
            '---',
            f'type: {item_type}',
            f'created: {datetime.now().isoformat()}',
            'status: pending',
        ]
        
        # Add additional fields
        for key, value in kwargs.items():
            if value is not None:
                frontmatter.append(f'{key}: {value}')
        
        frontmatter.append('---')
        return '\n'.join(frontmatter)
    
    def log_action(self, action_type: str, details: dict):
        """
        Log an action to the audit log.
        
        Args:
            action_type: Type of action performed
            details: Dictionary of action details
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'actor': self.__class__.__name__,
            **details
        }
        
        # Append to daily log file
        log_file = self.logs / f'{datetime.now().strftime("%Y-%m-%d")}.json'
        
        # Simple JSON lines format
        with open(log_file, 'a') as f:
            import json
            f.write(json.dumps(log_entry) + '\n')
        
        self.logger.debug(f'Logged action: {action_type}')
