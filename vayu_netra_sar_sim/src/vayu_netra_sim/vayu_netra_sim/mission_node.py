import time
from .ros_support import Base, spin
from .mission_manager import Mission


class MissionNode(Base):
    def __init__(self):
        super().__init__('mission_manager')
        self.engine=Mission(self.cfg);self.f=None;self.peers={};self.event_index=0
        self.listen('/vayu/flight',self.flight)
        self.listen('/vayu/triage',self.engine.observe)
        self.listen('/vayu/health',self.peer)
        self.create_timer(.1,self.tick)
        self.health_ok=True

    def flight(self,f):self.f=f;self.received=time.monotonic()
    def peer(self,h):self.peers[h['node']]=(time.monotonic(),h['ok'])

    def tick(self):
        f=dict(self.f or {})
        f['fresh']=f.get('fresh',False) and time.monotonic()-getattr(self,'received',0)<2
        f['ready']=all(self.peers.get(n,(0,False))[1] and time.monotonic()-self.peers[n][0]<3
                       for n in ['perception','fusion_triage','mapping','dashboard'])
        out=self.engine.tick(self.now_s(),f)
        self.send('/vayu/control',out)
        self.send('/vayu/mission',dict(out,timestamp=self.now_s(),search_grid=self.engine.points))
        for e in self.engine.events[self.event_index:]:self.send('/vayu/events',e)
        self.event_index=len(self.engine.events)


def main():spin(MissionNode)
