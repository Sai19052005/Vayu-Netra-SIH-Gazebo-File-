import time
from .ros_support import Base, spin
from .triage_engine import assess


class FusionNode(Base):
    def __init__(self):
        super().__init__('fusion_triage')
        self.pending={};self.thermal={}
        self.listen('/vayu/detections',lambda o:self.pending.update({o['observation_id']:(time.monotonic(),o)}))
        self.listen('/vayu/thermal_observations',lambda o:self.thermal.update({o['observation_id']:(time.monotonic(),o)}))
        self.create_timer(.1,self.tick);self.health_ok=True

    def tick(self):
        for id,(wall,o) in list(self.pending.items()):
            t=self.thermal.get(id)
            if t is None and time.monotonic()-wall<.3:continue
            if t and t[1]['id']==o['id'] and abs(t[1]['timestamp']-o['timestamp'])<=.2:
                o=dict(o,thermal=t[1])
            # Thermal corroboration is retained as evidence; no medical-score boost.
            self.send('/vayu/triage',assess(o,self.cfg))
            del self.pending[id]
        self.thermal={k:v for k,v in self.thermal.items() if time.monotonic()-v[0]<2}


def main():spin(FusionNode)
