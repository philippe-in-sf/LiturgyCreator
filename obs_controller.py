"""
OBS Controller Module
Handles connection and communication with OBS via WebSocket
"""

import logging
from typing import Dict, Optional, Any
import configparser
from obsws_python import ReqClient
import obsws_python.error as obs_errors

class OBSController:
    """Controls OBS WebSocket connection and text source updates"""
    
    def __init__(self, config: configparser.ConfigParser):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.client = None
        
        # Parse OBS connection settings
        self.host = config.get('OBS', 'host', fallback='localhost')
        self.port = config.getint('OBS', 'port', fallback=4455)
        self.password = config.get('OBS', 'password', fallback='')
        
        # Parse scene mappings
        self.scene_mappings = self._parse_scene_mappings(config)
        
    def _parse_scene_mappings(self, config: configparser.ConfigParser) -> Dict[str, Dict[str, str]]:
        """Parse scene mapping configuration"""
        mappings = {}
        
        if 'SCENE_MAPPING' in config:
            for key, value in config['SCENE_MAPPING'].items():
                if ':' in value:
                    scene_name, source_name = value.split(':', 1)
                    mappings[key] = {
                        'scene': scene_name.strip(),
                        'source': source_name.strip()
                    }
                else:
                    self.logger.warning(f"Invalid scene mapping format for {key}: {value}")
        
        return mappings
    
    def connect(self) -> bool:
        """
        Connect to OBS WebSocket
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.logger.info(f"Connecting to OBS at {self.host}:{self.port}")
            
            self.client = ReqClient(
                host=self.host,
                port=self.port,
                password=self.password if self.password else None
            )
            
            # Test connection by getting version info
            version_info = self.client.get_version()
            self.logger.info(f"Connected to OBS version {version_info.obs_version}")
            
            return True
            
        except obs_errors.OBSSDKError as e:
            self.logger.error(f"OBS SDK error during connection: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error connecting to OBS: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from OBS WebSocket"""
        if self.client:
            try:
                self.client.disconnect()
                self.logger.info("Disconnected from OBS")
            except Exception as e:
                self.logger.warning(f"Error during OBS disconnection: {str(e)}")
            finally:
                self.client = None
    
    def update_scripture_sources(self, scriptures: Dict[str, Any]) -> bool:
        """
        Update OBS text sources with scripture readings
        
        Args:
            scriptures: Dictionary containing parsed scripture readings
            
        Returns:
            True if all updates successful, False if any failed
        """
        if not self.client:
            self.logger.error("Not connected to OBS")
            return False
        
        success_count = 0
        total_updates = 0
        
        for reading_type, reading_data in scriptures.items():
            # Update text content
            text_mapping_key = f"{reading_type}_text"
            if text_mapping_key in self.scene_mappings:
                total_updates += 1
                if self._update_text_source(
                    self.scene_mappings[text_mapping_key],
                    reading_data.get('text', '')
                ):
                    success_count += 1
            
            # Update reference
            ref_mapping_key = f"{reading_type}_reference"
            if ref_mapping_key in self.scene_mappings:
                total_updates += 1
                if self._update_text_source(
                    self.scene_mappings[ref_mapping_key],
                    reading_data.get('reference', '')
                ):
                    success_count += 1
        
        self.logger.info(f"Updated {success_count}/{total_updates} OBS text sources")
        return success_count == total_updates
    
    def _update_text_source(self, mapping: Dict[str, str], text: str) -> bool:
        """
        Update a specific text source in OBS
        
        Args:
            mapping: Dictionary with 'scene' and 'source' keys
            text: Text content to set
            
        Returns:
            True if update successful, False otherwise
        """
        scene_name = mapping['scene']
        source_name = mapping['source']
        
        try:
            # Check if scene exists
            scenes = self.client.get_scene_list()
            scene_exists = any(scene['sceneName'] == scene_name for scene in scenes.scenes)
            
            if not scene_exists:
                self.logger.warning(f"Scene '{scene_name}' not found in OBS")
                return False
            
            # Check if source exists in the scene
            try:
                scene_items = self.client.get_scene_item_list(scene_name)
                source_exists = any(
                    item['sourceName'] == source_name 
                    for item in scene_items.scene_items
                )
                
                if not source_exists:
                    self.logger.warning(f"Source '{source_name}' not found in scene '{scene_name}'")
                    return False
                
            except obs_errors.OBSSDKError:
                # If we can't check scene items, try the update anyway
                pass
            
            # Apply formatting
            formatted_text = self._format_text(text)
            
            # Update text source
            self.client.set_input_settings(
                source_name,
                {'text': formatted_text},
                overlay=True
            )
            
            self.logger.info(f"Updated '{source_name}' in scene '{scene_name}'")
            return True
            
        except obs_errors.OBSSDKError as e:
            self.logger.error(f"OBS error updating {source_name}: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error updating {source_name}: {str(e)}")
            return False
    
    def _format_text(self, text: str) -> str:
        """Apply text formatting based on configuration"""
        if not text:
            return ""
        
        # Get formatting settings
        max_length = self.config.getint('FORMATTING', 'max_text_length', fallback=500)
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length - 3] + "..."
        
        # Clean up text
        text = text.strip()
        
        # Replace multiple spaces with single spaces
        import re
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def list_scenes_and_sources(self) -> Dict[str, list]:
        """
        List all scenes and their text sources for configuration help
        
        Returns:
            Dictionary mapping scene names to lists of text source names
        """
        if not self.client:
            self.logger.error("Not connected to OBS")
            return {}
        
        try:
            scenes_data = {}
            scenes = self.client.get_scene_list()
            
            for scene in scenes.scenes:
                scene_name = scene['sceneName']
                try:
                    scene_items = self.client.get_scene_item_list(scene_name)
                    text_sources = []
                    
                    for item in scene_items.scene_items:
                        # Check if this is a text source
                        source_name = item['sourceName']
                        try:
                            source_settings = self.client.get_input_settings(source_name)
                            if 'text' in source_settings.input_settings:
                                text_sources.append(source_name)
                        except:
                            # Not a text source
                            pass
                    
                    scenes_data[scene_name] = text_sources
                    
                except Exception as e:
                    self.logger.warning(f"Could not get items for scene {scene_name}: {str(e)}")
                    scenes_data[scene_name] = []
            
            return scenes_data
            
        except Exception as e:
            self.logger.error(f"Error listing scenes and sources: {str(e)}")
            return {}
