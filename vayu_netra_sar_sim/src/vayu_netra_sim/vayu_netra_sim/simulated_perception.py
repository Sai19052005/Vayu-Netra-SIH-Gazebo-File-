"""Scenario oracle, explicitly NOT image inference. Frustum gate, no occlusion realism."""
import math
from .perception_interface import validate


class SimulatedPerception:
    def __init__(self, cfg):
        self.cfg, self.counts, self.last, self.reviewed = cfg, {}, {}, set()

    def observe(self, pose, timestamp, **kwargs):
        out = []
        w, h = self.cfg['perception']['width'], self.cfg['perception']['height']
        fx = w/(2*math.tan(self.cfg['perception']['hfov']/2))
        yaw = kwargs.get('yaw', 0.)  # ENU yaw; camera optical top points body-forward
        for t in self.cfg['scene']['targets']:
            z = pose[2]-t['position'][2]-.12
            if z <= 2 or timestamp-self.last.get(t['id'], -100) < 2:
                continue
            dx, dy = t['position'][0]-pose[0], t['position'][1]-pose[1]
            forward = dx*math.cos(yaw)+dy*math.sin(yaw)
            right = dx*math.sin(yaw)-dy*math.cos(yaw)
            u, v = w/2+fx*right/z, h/2-fx*forward/z
            if not 8 <= u <= w-8 or not 8 <= v <= h-8:
                continue
            self.last[t['id']] = timestamp
            n = self.counts.get(t['id'], 0)+1
            self.counts[t['id']] = n
            context = dict(t['context'])
            # Explicit authored scene change after second close observation, not a medical inference.
            if n > 1 and kwargs.get('reinspect_id')==t['id'] and math.hypot(dx, dy) < 3 and 'review_context' in t:
                self.reviewed.add(t['id'])
            if t['id'] in self.reviewed:context = dict(t['review_context'])
            o = dict(schema_version=1, id=t['id'], observation_id=f"{t['id']}:{n}",
                     **{'class': t['class']}, confidence=.90, timestamp=timestamp,
                     bbox=[max(0,u-8),max(0,v-14),min(w,u+8),min(h,v+14)],
                     uav_pose=list(pose), local_position=list(t['position']),
                     position_method='SCENARIO_ORACLE_NOT_MEASURED', source='SIMULATED_PERCEPTION',
                     sensor_source='GAZEBO_RGB_TRIGGER' if kwargs.get('image') else 'SOFTWARE_TEST_FIXTURE',
                     context=context, context_source='AUTHORED_SCENARIO', thermal=None, depth=None,
                     inference_ms=None)
            out.append(validate(o))
        return out
