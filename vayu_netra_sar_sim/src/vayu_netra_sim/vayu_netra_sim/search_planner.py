"""Rectangle is the supported four-vertex search polygon; forbidden regions are checked."""
import math


def inside(p, box, margin=0):
    return box[0]-margin <= p[0] <= box[1]+margin and box[2]-margin <= p[1] <= box[3]+margin


def segment_safe(a, b, zones):
    steps = max(1, math.ceil(math.dist(a[:2], b[:2])/.2))
    return all(not any(inside([a[0]+(b[0]-a[0])*t/steps,
                              a[1]+(b[1]-a[1])*t/steps], z, .5) for z in zones)
               for t in range(steps+1))


def plan(m, zones=()):
    lo, hi = m['search_min_x'], m['search_max_x']
    y0, y1 = m['search_min_y'], m['search_max_y']
    count = math.ceil((y1-y0)/m['search_spacing'])
    points = []
    for i in range(count+1):
        y = min(y1, y0+i*m['search_spacing'])
        xs = (lo, hi) if i % 2 == 0 else (hi, lo)
        points += [[x, y, m['search_altitude']] for x in xs]
    if any(not segment_safe(a, b, zones) for a, b in zip([[0, 0, m['search_altitude']]]+points, points)):
        raise ValueError('Search/transit crosses restricted zone: change rectangle; no obstacle planner is claimed')
    if not segment_safe(points[-1], [0, 0, m['search_altitude']], zones):
        raise ValueError('Home transit crosses restricted zone')
    return points


class Coverage:
    """Visited grid-cell fraction inside camera-footprint proxy, not guaranteed visual detection."""
    def __init__(self, m, cell=1):
        self.m, self.cell, self.visited = m, cell, set()
        self.cells = [(x+.5, y+.5) for x in range(math.floor(m['search_min_x']), math.ceil(m['search_max_x']))
                      for y in range(math.floor(m['search_min_y']), math.ceil(m['search_max_y']))]

    def update(self, p, radius):
        self.visited.update(i for i, xy in enumerate(self.cells) if math.dist(p[:2], xy) <= radius)
        return len(self.visited)/len(self.cells) if self.cells else 0
