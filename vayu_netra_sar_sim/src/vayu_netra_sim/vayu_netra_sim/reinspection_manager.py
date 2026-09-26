from .search_planner import segment_safe


class ReinspectionManager:
    def __init__(self, cfg):
        self.cfg, self.queue, self.finished = cfg, {}, set()

    def offer(self, o):
        if (o['class'] == 'person' and o.get('priority') in self.cfg['mission']['reinspect_priorities']
                and o.get('local_position') is not None and o['id'] not in self.finished):
            self.queue[o['id']] = o

    def take(self, pose, resume):
        zones = self.cfg['scene']['restricted_zones']
        for id, o in sorted(self.queue.items(), key=lambda p: p[1]['priority']):
            goal = [*o['local_position'][:2], self.cfg['mission']['search_altitude']]
            if segment_safe(pose, goal, zones) and segment_safe(goal, resume, zones):
                del self.queue[id]
                self.finished.add(id)  # one attempt per incident; avoids endless diversions
                return o, goal
        return None
