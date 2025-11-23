"""
ATEM Controller Module
Handles connection and communication with Blackmagic ATEM video switchers
"""

import logging
from typing import Dict, Optional, Any, List
import configparser
import os
try:
    import PyATEMMax
except ImportError:
    PyATEMMax = None

class ATEMController:
    """Controls ATEM switcher connection and operations"""
    
    def __init__(self, config: configparser.ConfigParser):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.switcher = None
        
        if PyATEMMax is None:
            self.logger.warning("PyATEMMax not installed. ATEM control will be unavailable.")
            return
        
        # Parse ATEM connection settings
        atem_section = 'ATEM' if 'ATEM' in config else 'atem'
        self.host = config.get(atem_section, 'host', fallback='192.168.1.240')
        self.port = config.getint(atem_section, 'port', fallback=20890)
        
        # Parse input/output mappings
        self.input_mappings = self._parse_input_mappings(config)
    
    def _parse_input_mappings(self, config: configparser.ConfigParser) -> Dict[str, int]:
        """Parse ATEM input mapping configuration"""
        mappings = {}
        
        mapping_section = 'ATEM_INPUTS' if 'ATEM_INPUTS' in config else 'atem_inputs'
        
        if mapping_section in config:
            for key, value in config[mapping_section].items():
                try:
                    mappings[key] = int(value.strip())
                except ValueError:
                    self.logger.warning(f"Invalid input mapping value: {key}={value}")
        
        return mappings
    
    def connect(self) -> bool:
        """
        Connect to ATEM switcher
        
        Returns:
            True if connection successful, False otherwise
        """
        if PyATEMMax is None:
            self.logger.error("PyATEMMax not installed")
            return False
        
        try:
            self.logger.info(f"Connecting to ATEM at {self.host}:{self.port}")
            
            self.switcher = PyATEMMax.ATEMMax()
            self.switcher.connect(self.host)
            self.switcher.waitForConnection()
            
            # Get switcher info
            model_name = getattr(self.switcher.productName, 'model', 'Unknown Model')
            self.logger.info(f"Connected to ATEM {model_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to ATEM: {str(e)}")
            self.switcher = None
            return False
    
    def disconnect(self):
        """Disconnect from ATEM switcher"""
        if self.switcher:
            try:
                self.switcher.disconnect()
                self.logger.info("Disconnected from ATEM")
            except Exception as e:
                self.logger.warning(f"Error during ATEM disconnection: {str(e)}")
            finally:
                self.switcher = None
    
    def switch_to_input(self, me: int, input_num: int) -> bool:
        """
        Switch program output to specified input
        
        Args:
            me: Mix effect unit (0, 1, etc.)
            input_num: Input number to switch to
            
        Returns:
            True if successful, False otherwise
        """
        if not self.switcher:
            self.logger.error("Not connected to ATEM")
            return False
        
        try:
            self.switcher.setProgramInputVideoSource(me, input_num)
            self.logger.info(f"Switched ME{me} Program to input {input_num}")
            return True
        except Exception as e:
            self.logger.error(f"Error switching input: {str(e)}")
            return False
    
    def set_preview_input(self, me: int, input_num: int) -> bool:
        """
        Set preview input for specified mix effect
        
        Args:
            me: Mix effect unit (0, 1, etc.)
            input_num: Input number to preview
            
        Returns:
            True if successful, False otherwise
        """
        if not self.switcher:
            self.logger.error("Not connected to ATEM")
            return False
        
        try:
            self.switcher.setPreviewInputVideoSource(me, input_num)
            self.logger.info(f"Set ME{me} Preview to input {input_num}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting preview input: {str(e)}")
            return False
    
    def trigger_cut(self, me: int) -> bool:
        """
        Trigger cut transition
        
        Args:
            me: Mix effect unit (0, 1, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.switcher:
            self.logger.error("Not connected to ATEM")
            return False
        
        try:
            self.switcher.performCutTransition(me)
            self.logger.info(f"Cut triggered on ME{me}")
            return True
        except Exception as e:
            self.logger.error(f"Error triggering cut: {str(e)}")
            return False
    
    def trigger_auto(self, me: int) -> bool:
        """
        Trigger auto transition
        
        Args:
            me: Mix effect unit (0, 1, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.switcher:
            self.logger.error("Not connected to ATEM")
            return False
        
        try:
            self.switcher.performAutoTransition(me)
            self.logger.info(f"Auto transition triggered on ME{me}")
            return True
        except Exception as e:
            self.logger.error(f"Error triggering auto: {str(e)}")
            return False
    
    def upload_media(self, file_path: str, media_index: int) -> bool:
        """
        Upload image to ATEM media pool
        
        Args:
            file_path: Path to image file (PNG, JPG)
            media_index: Media pool index (0-19)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.switcher:
            self.logger.error("Not connected to ATEM")
            return False
        
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            return False
        
        try:
            self.logger.info(f"Uploading {file_path} to media pool slot {media_index}")
            # PyATEMMax uses uploadStill for image uploads
            with open(file_path, 'rb') as f:
                self.switcher.uploadStill(media_index, f)
            self.logger.info(f"Uploaded media to slot {media_index}")
            return True
        except Exception as e:
            self.logger.error(f"Error uploading media: {str(e)}")
            return False
    
    def set_media_player(self, player: int, media_index: int) -> bool:
        """
        Set media player to use specific media pool item
        
        Args:
            player: Media player number (0, 1, etc.)
            media_index: Media pool index
            
        Returns:
            True if successful, False otherwise
        """
        if not self.switcher:
            self.logger.error("Not connected to ATEM")
            return False
        
        try:
            # Use the media player source (input 3000 + player_number)
            source_num = 3000 + player
            self.switcher.setProgramInputVideoSource(0, source_num)
            self.logger.info(f"Set media player {player} (source {source_num})")
            return True
        except Exception as e:
            self.logger.error(f"Error setting media player: {str(e)}")
            return False
    
    def set_audio_volume(self, channel: int, volume: float) -> bool:
        """
        Set audio volume for a channel
        
        Args:
            channel: Audio input channel
            volume: Volume level in dB (-60 to +6)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.switcher:
            self.logger.error("Not connected to ATEM")
            return False
        
        try:
            self.switcher.setAudioMixerInputVolume(channel, volume)
            self.logger.info(f"Set audio channel {channel} volume to {volume}dB")
            return True
        except Exception as e:
            self.logger.error(f"Error setting audio volume: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current ATEM status
        
        Returns:
            Dictionary with switcher status information
        """
        if not self.switcher:
            return {
                'connected': False,
                'message': 'Not connected to ATEM'
            }
        
        try:
            status = {
                'connected': True,
                'model': getattr(self.switcher.productName, 'model', 'Unknown'),
                'program_input': self.switcher.mixEffects[0].programInput if self.switcher.mixEffects else None,
                'preview_input': self.switcher.mixEffects[0].previewInput if self.switcher.mixEffects else None
            }
            return status
        except Exception as e:
            self.logger.warning(f"Error getting ATEM status: {str(e)}")
            return {
                'connected': True,
                'message': 'Connected but status unavailable'
            }
    
    def list_inputs(self) -> Dict[int, str]:
        """
        List available inputs on the switcher
        
        Returns:
            Dictionary mapping input numbers to input names
        """
        if not self.switcher:
            return {}
        
        try:
            inputs = {}
            if hasattr(self.switcher, 'inputs'):
                for input_num, input_info in self.switcher.inputs.items():
                    inputs[input_num] = getattr(input_info, 'label', f'Input {input_num}')
            return inputs
        except Exception as e:
            self.logger.warning(f"Error listing inputs: {str(e)}")
            return {}
