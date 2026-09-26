"""A separate authored thermal-evidence fixture; no temperature or physiology claim."""
from .ros_support import Base, spin


class ThermalSimulator(Base):
    def __init__(self):
        super().__init__('thermal_simulator')
        self.listen('/vayu/detections',self.observe);self.health_ok=True

    def observe(self,o):
        if o['source']!='SIMULATED_PERCEPTION':return
        self.send('/vayu/thermal_observations',dict(id=o['id'],observation_id=o['observation_id'],timestamp=o['timestamp'],
             source='SIMULATED_THERMAL_FIXTURE',thermal_evidence='WARM_TARGET' if o['class']=='person' else 'SCENE_HAZARD',temperature_c=None))


def main():spin(ThermalSimulator)
