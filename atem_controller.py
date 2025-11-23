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
    
    def _get_video_source_constant(self, source_id: int):
        """
        Convert video source ID to ATEMConstant
        
        Args:
            source_id: Video source number
            
        Returns:
            ATEMConstant for the video source, raises ValueError if invalid
        """
        if not self.switcher:
            raise ValueError("Not connected to ATEM switcher")
        
        try:
            # Map common video source IDs to their string names for lookup
            # Based on PyATEMMax documentation at https://clvlabs.github.io/PyATEMMax/docs/data/protocol/
            
            # Standard camera inputs (1-40)
            if 1 <= source_id <= 40:
                return self.switcher.atem.videoSources[f"input{source_id}"]
            
            # Special sources
            elif source_id == 0:
                return self.switcher.atem.videoSources.black
            elif source_id == 1000:
                return self.switcher.atem.videoSources.colorBars
            elif source_id == 2001:
                return self.switcher.atem.videoSources.color1
            elif source_id == 2002:
                return self.switcher.atem.videoSources.color2
            elif source_id == 3010:
                return self.switcher.atem.videoSources.mediaPlayer1
            elif source_id == 3020:
                return self.switcher.atem.videoSources.mediaPlayer2
            elif source_id == 3030:
                return self.switcher.atem.videoSources.mediaPlayer3
            elif source_id == 3040:
                return self.switcher.atem.videoSources.mediaPlayer4
            elif 7001 <= source_id <= 7004:
                clean_feed_num = source_id - 7000
                return self.switcher.atem.videoSources[f"cleanFeed{clean_feed_num}"]
            elif 8001 <= source_id <= 8024:
                aux_num = source_id - 8000
                return self.switcher.atem.videoSources[f"auxiliary{aux_num}"]
            else:
                raise ValueError(f"Unknown video source ID: {source_id}")
                
        except (KeyError, AttributeError) as e:
            raise ValueError(f"Could not resolve video source {source_id}: {str(e)}")
    
    def _get_audio_source_constant(self, source_id: int):
        """
        Convert audio source ID to ATEMConstant
        
        Args:
            source_id: Audio source number
            
        Returns:
            ATEMConstant for the audio source, raises ValueError if invalid
        """
        if not self.switcher:
            raise ValueError("Not connected to ATEM switcher")
        
        try:
            # Map common audio source IDs to their string names for lookup
            # Based on PyATEMMax documentation
            
            # Standard audio inputs (1-20)
            if 1 <= source_id <= 20:
                return self.switcher.atem.audioSources[f"input{source_id}"]
            
            # Special audio sources
            elif source_id == 1001:
                return self.switcher.atem.audioSources.xlr
            elif source_id == 1101:
                return self.switcher.atem.audioSources.aes_ebu
            elif source_id == 1201:
                return self.switcher.atem.audioSources.rca
            elif source_id == 1301:
                return self.switcher.atem.audioSources.mic1
            elif source_id == 1302:
                return self.switcher.atem.audioSources.mic2
            elif source_id == 2001:
                return self.switcher.atem.audioSources.mp1
            elif source_id == 2002:
                return self.switcher.atem.audioSources.mp2
            elif source_id == 2003:
                return self.switcher.atem.audioSources.mp3
            elif source_id == 2004:
                return self.switcher.atem.audioSources.mp4
            else:
                raise ValueError(f"Unknown audio source ID: {source_id}")
                
        except (KeyError, AttributeError) as e:
            raise ValueError(f"Could not resolve audio source {source_id}: {str(e)}")
    
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
            
            # Wait for connection with 5 second timeout
            connection_result = self.switcher.waitForConnection(timeout=5.0)
            
            if not connection_result:
                self.logger.error("ATEM connection timeout - switcher not reachable")
                self.switcher = None
                return False
            
            # Cache mix effect constant (use ME 1 which is mixEffect1)
            self.mix_effect = self.switcher.atem.mixEffects.mixEffect1
            
            # Get switcher info
            model_name = str(self.switcher.atemModel) if hasattr(self.switcher, 'atemModel') else 'Unknown Model'
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
            # Convert integer source ID to ATEMConstant
            video_source = self._get_video_source_constant(input_num)
            # Use the cached mix effect constant (supports ME1 only for now)
            self.switcher.setProgramInputVideoSource(self.mix_effect, video_source)
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
            # Convert integer source ID to ATEMConstant
            video_source = self._get_video_source_constant(input_num)
            # Use the cached mix effect constant (supports ME1 only for now)
            self.switcher.setPreviewInputVideoSource(self.mix_effect, video_source)
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
            # Use the cached mix effect constant (supports ME1 only for now)
            self.switcher.performCutTransition(self.mix_effect)
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
            # Use the cached mix effect constant (supports ME1 only for now)
            self.switcher.performAutoTransition(self.mix_effect)
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
            self.logger.info(f"Media upload to ATEM requires file conversion to RGBA format")
            self.logger.warning(f"Media upload feature not fully implemented - requires PIL/Pillow for image conversion")
            # TODO: Implement proper media upload workflow
            # 1. Load image with PIL
            # 2. Convert to RGBA 1920x1080
            # 3. Use switcher.setMediaPlayerStill or similar method
            # For now, return False to indicate not implemented
            return False
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
            # Get the proper media player constant (mediaPlayer1 is index 0)
            if player == 0:
                media_source = self.switcher.atem.videoSources.mediaPlayer1
            elif player == 1:
                media_source = self.switcher.atem.videoSources.mediaPlayer2
            elif player == 2:
                media_source = self.switcher.atem.videoSources.mediaPlayer3
            elif player == 3:
                media_source = self.switcher.atem.videoSources.mediaPlayer4
            else:
                self.logger.error(f"Invalid media player number: {player}")
                return False
            
            # Use the cached mix effect constant (supports ME1 only for now)
            self.switcher.setProgramInputVideoSource(self.mix_effect, media_source)
            self.logger.info(f"Set media player {player} on program")
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
            # Convert integer channel ID to ATEMConstant
            audio_source = self._get_audio_source_constant(channel)
            self.switcher.setAudioMixerInputVolume(audio_source, volume)
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
            # Get program and preview inputs from ME1 using the cached constant
            program_input = None
            preview_input = None
            
            if hasattr(self.switcher, 'programInput') and self.mix_effect:
                program_input = self.switcher.programInput[self.mix_effect].videoSource if self.switcher.programInput else None
            
            if hasattr(self.switcher, 'previewInput') and self.mix_effect:
                preview_input = self.switcher.previewInput[self.mix_effect].videoSource if self.switcher.previewInput else None
            
            status = {
                'connected': True,
                'model': str(self.switcher.atemModel) if hasattr(self.switcher, 'atemModel') else 'Unknown',
                'program_input': program_input,
                'preview_input': preview_input
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
            if hasattr(self.switcher, 'inputProperties'):
                # inputProperties is indexed by video source number
                for source_id in range(1, 21):  # ATEM typically has sources 1-20
                    try:
                        if self.switcher.inputProperties[source_id]:
                            long_name = self.switcher.inputProperties[source_id].longName
                            if long_name and long_name.strip():
                                inputs[source_id] = long_name
                    except:
                        # Source doesn't exist, skip
                        pass
            return inputs
        except Exception as e:
            self.logger.warning(f"Error listing inputs: {str(e)}")
            return {}
