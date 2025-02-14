import yaml
from datetime import datetime as dt
from typing import Dict, Optional

class HAMQTTModels:
    def __init__(self, serial_number: str, system_type: str, description: str):
        """
        Initialize HAMQTTModels with basic system information.
        
        Args:
            serial_number: System serial number
            system_type: Type of the Tecnoalarm system
            description: System description
        """
        self.sn = serial_number
        self.device_id = f"tecnoalarm_{serial_number}"
        self.system_type = system_type
        self.description = description
        self.programs: Dict[str, dict] = {}
        self.zones: Dict[str, dict] = {}
        
        # Create base device info
        self.device_info = {
            "identifiers": [self.device_id],
            "manufacturer": "Tecnoalarm",
            "model": system_type,
            "name": f"Tecnoalarm - {description}",
            "sw_version": "unknown"
        }
        
        self.discovery_messages = {}

    @staticmethod
    def log(name: str, message: str) -> None:
        print(f"{dt.now()} [ha-mqtt-{name}] {message}")

    @staticmethod
    def get_device_class(description: str) -> str:
        """Determine device class based on zone description."""
        description = description.lower()
        if "porta" in description:
            return "door"
        elif "fin." in description:
            return "window"
        elif "gas" in description:
            return "gas"
        elif "emergenza" in description:
            return "safety"
        elif "vol." in description:
            return "motion"
        elif "cassaf" in description:
            return "lock"
        return "door"  # default device class

    def add_program(self, program_id: str, description: str, topic: str) -> None:
        """
        Add a single program to the system.
        
        Args:
            program_id: Program identifier
            description: Program description
            topic: MQTT topic for the program
        """
        self.programs[program_id] = {
            'description': description,
            'topic': topic
        }

    def add_zone(self, zone_id: str, description: str, topic: str, allocated: bool = True) -> None:
        """
        Add a single zone to the system.
        
        Args:
            zone_id: Zone identifier
            description: Zone description
            topic: MQTT topic for the zone
            allocated: Whether the zone is allocated
        """
        self.zones[zone_id] = {
            'description': description,
            'topic': topic,
            'allocated': allocated
        }

    def create_program_discovery(self, program_id: str) -> Optional[Dict[str, dict]]:
        """
        Create discovery message for a single program.
        
        Args:
            program_id: Program identifier
            
        Returns:
            Dictionary with discovery topic and message, or None if program doesn't exist
        """
        if program_id not in self.programs:
            return None
            
        program = self.programs[program_id]
        panel_config = {
            "name": f"{self.description} - {program['description']}",
            "unique_id": f"{self.device_id}_{program_id}_panel",
            "state_topic": program['topic'],
            "value_template": "{% if value_json.alarm %}triggered{% elif value_json.status == 0 %}disarmed{% else %}armed_away{% endif %}",
            "command_topic": f"{program['topic']}/set",
            "supported_features": ['arm_away'],
            "code_arm_required": "True",
            "code_disarm_required": "True",
            "payload_arm_away": "ON",
            "payload_disarm": "OFF",
            "device": self.device_info
        }
        
        panel_topic = f"homeassistant/alarm_control_panel/{self.device_id}/panel_{program_id}/config"
        
        self.log("alarm_panel yaml model", f"\n{yaml.dump({'alarm_control_panel':[panel_config]}, width=2147483647, indent=2, sort_keys=False)}")
        
        return {panel_topic: panel_config}

    def create_zone_discovery(self, zone_id: str) -> Optional[Dict[str, dict]]:
        """
        Create discovery message for a single zone.
        
        Args:
            zone_id: Zone identifier
            
        Returns:
            Dictionary with discovery topic and message, or None if zone doesn't exist or isn't allocated
        """
        if zone_id not in self.zones or not self.zones[zone_id]['allocated']:
            return None
            
        zone = self.zones[zone_id]
        object_id = zone['topic'].split('/')[-1]
        
        sensor_config = {
            "name": zone['description'].strip(),
            "unique_id": f"{self.device_id}_zone_{zone_id}",
            "state_topic": zone['topic'],
            "value_template": "{{ 'ON' if value_json.status == 'OPEN' else 'OFF' }}",
            "device_class": self.get_device_class(zone['description']),
            "payload_on": "ON",
            "payload_off": "OFF",
            "device": self.device_info,
        }
        
        sensor_topic = f"homeassistant/binary_sensor/{self.device_id}/{object_id}/config"
        
        self.log("yaml zone model", f"\n{yaml.dump({'binary_sensor':[sensor_config]}, width=2147483647, indent=2, sort_keys=False)}")
        
        return {sensor_topic: sensor_config}

    def create_all_discovery_messages(self, include_programs: bool = True) -> Dict[str, dict]:
        """
        Create all discovery messages for configured programs and zones.
        
        Args:
            include_programs: Whether to include program discovery messages
            
        Returns:
            Dictionary with all discovery topics and messages
        """
        self.discovery_messages = {}
        
        if include_programs:
            for program_id in self.programs:
                program_discovery = self.create_program_discovery(program_id)
                if program_discovery:
                    self.discovery_messages.update(program_discovery)
        
        for zone_id in self.zones:
            zone_discovery = self.create_zone_discovery(zone_id)
            if zone_discovery:
                self.discovery_messages.update(zone_discovery)
        
        return self.discovery_messages
