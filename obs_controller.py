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
        
        # Parse OBS connection settings - support both section names
        obs_section = 'OBS' if 'OBS' in config else 'obs'
        self.host = config.get(obs_section, 'host', fallback='localhost')
        self.port = config.getint(obs_section, 'port', fallback=4455)
        self.password = config.get(obs_section, 'password', fallback='')
        
        # Parse scene mappings
        self.scene_mappings = self._parse_scene_mappings(config)
        
    def _parse_scene_mappings(self, config: configparser.ConfigParser) -> Dict[str, str]:
        """Parse scene mapping configuration"""
        mappings = {}
        
        # Support both section names
        mapping_section = 'SCENE_MAPPING' if 'SCENE_MAPPING' in config else 'scene_mappings'
        
        if mapping_section in config:
            for key, value in config[mapping_section].items():
                # For the simplified format, just store the source name directly
                mappings[key] = value.strip()
        
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
            try:
                version_info = self.client.get_version()
                version = getattr(version_info, 'obs_version', 'Unknown') if version_info else 'Unknown'
                self.logger.info(f"Connected to OBS version {version}")
            except Exception as version_error:
                self.logger.warning(f"Could not get OBS version: {version_error}")
                # Connection still successful if we can't get version
            
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
    
    def update_service_details(self, service_details: Dict[str, str]) -> bool:
        """
        Update OBS text sources with service details (hymns, clergy, musicians)
        
        Args:
            service_details: Dictionary containing service detail information
            
        Returns:
            True if all updates successful, False if any failed
        """
        if not self.client:
            self.logger.error("Not connected to OBS")
            return False
        
        success_count = 0
        total_updates = 0
        
        # Service detail mappings for OBS text sources
        detail_mappings = {
            'openingHymn': 'opening_hymn',
            'sequenceHymn': 'sequence_hymn', 
            'communionMotet': 'communion_motet',
            'closingHymn': 'closing_hymn',
            'organistName': 'organist_name',
            'preludeName': 'prelude_name',
            'preludeComposer': 'prelude_composer',
            'postludeName': 'postlude_name',
            'postludeComposer': 'postlude_composer',
            'preacherName': 'preacher_name',
            'presiderName': 'presider_name'
        }
        
        for detail_key, detail_value in service_details.items():
            if detail_key in detail_mappings and detail_value.strip():
                mapping_key = detail_mappings[detail_key]
                if mapping_key in self.scene_mappings:
                    total_updates += 1
                    if self._update_text_source(
                        self.scene_mappings[mapping_key],
                        detail_value.strip()
                    ):
                        success_count += 1
        
        self.logger.info(f"Updated {success_count}/{total_updates} service detail OBS sources")
        return success_count == total_updates or total_updates == 0
    
    def _update_text_source(self, source_name: str, text: str) -> bool:
        """
        Update a specific text source in OBS
        
        Args:
            source_name: Name of the text source to update
            text: Text content to set
            
        Returns:
            True if update successful, False otherwise
        """
        
        try:
            # Apply formatting
            formatted_text = self._format_text(text)
            
            # Update text source - simplified approach
            if self.client:
                self.client.set_input_settings(
                    source_name,
                    {'text': formatted_text},
                    overlay=True
                )
                
                self.logger.info(f"Updated text source '{source_name}'")
                return True
            else:
                self.logger.error("No OBS client connection")
                return False
            
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
            
            for scene in getattr(scenes, 'scenes', []):
                scene_name = scene.get('sceneName')
                try:
                    scene_items = self.client.get_scene_item_list(scene_name)
                    text_sources = []
                    
                    for item in getattr(scene_items, 'scene_items', []):
                        # Check if this is a text source
                        source_name = item.get('sourceName')
                        try:
                            source_settings = self.client.get_input_settings(source_name)
                            if 'text' in getattr(source_settings, 'input_settings', {}):
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
