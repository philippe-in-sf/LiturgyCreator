#!/usr/bin/env python3
"""
Daily Liturgical Scripture OBS Automation
Fetches liturgical readings and updates OBS scene text sources
"""

import logging
import sys
from datetime import datetime
from liturgy_fetcher import LiturgyFetcher
from obs_controller import OBSController
from scripture_parser import ScriptureParser
import configparser
import os

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('liturgy_obs.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def load_config():
    """Load configuration from config.ini"""
    config = configparser.ConfigParser()
    
    if not os.path.exists('config.ini'):
        logger.error("Configuration file 'config.ini' not found. Please create it first.")
        sys.exit(1)
    
    config.read('config.ini')
    return config

def main():
    """Main automation workflow"""
    global logger
    logger = setup_logging()
    logger.info("Starting liturgical scripture OBS automation")
    
    try:
        # Load configuration
        config = load_config()
        
        # Initialize components
        liturgy_fetcher = LiturgyFetcher()
        obs_controller = OBSController(config)
        scripture_parser = ScriptureParser()
        
        # Get current date
        current_date = datetime.now()
        logger.info(f"Fetching liturgical readings for {current_date.strftime('%Y-%m-%d')}")
        
        # Fetch liturgical data
        liturgical_data = liturgy_fetcher.fetch_daily_readings(current_date)
        
        if not liturgical_data:
            logger.error("Failed to fetch liturgical data")
            return False
        
        # Parse scripture data
        parsed_scriptures = scripture_parser.parse_readings(liturgical_data)
        
        if not parsed_scriptures:
            logger.error("Failed to parse scripture readings")
            return False
        
        # Connect to OBS
        if not obs_controller.connect():
            logger.error("Failed to connect to OBS")
            return False
        
        # Update OBS text sources
        success = obs_controller.update_scripture_sources(parsed_scriptures)
        
        # Disconnect from OBS
        obs_controller.disconnect()
        
        if success:
            logger.info("Successfully updated OBS with liturgical readings")
            return True
        else:
            logger.error("Failed to update some OBS text sources")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error in main workflow: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
