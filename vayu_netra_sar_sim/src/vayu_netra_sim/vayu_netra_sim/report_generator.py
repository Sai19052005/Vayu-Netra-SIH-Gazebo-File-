import html
import json
from pathlib import Path
from .coordinates import geodetic, distance
from .search_planner import Coverage


class Recorder:
    def __init__(self, cfg):
        self.cfg, self.path, self.incidents, self.events = cfg, [], {}, []
        self.coverage = Coverage(cfg['mission'])
        self.start, self.end, self.status, self.length = None, None, 'INITIALIZING', 0.

    def pose(self, timestamp, p, searching=False, image_fresh=False):
        if self.start is None: self.start = timestamp
        self.end = timestamp
        if not self.path or distance(self.path[-1]['position'], p) > .2:
            if self.path: self.length += distance(self.path[-1]['position'], p)
            self.path.append(dict(timestamp=timestamp,position=list(p)))
        if searching and image_fresh:
            import math
            half_height = p[2]*math.tan(self.cfg['perception']['hfov']/2)*self.cfg['perception']['height']/self.cfg['perception']['width']
            self.coverage.update(p, max(0,half_height))

    def observation(self, o):
        previous = self.incidents.get(o['id'])
        if previous and previous['observation_id'] == o['observation_id']: return
        self.incidents[o['id']] = dict(o, observation_count=(previous or {}).get('observation_count',0)+1)
        if not previous or previous.get('priority') != o.get('priority'):
            self.events.append(dict(timestamp=o['timestamp'],event='PRIORITY_UPDATE' if previous else 'DETECTION',detail=o['id'],priority=o.get('priority')))

    def report(self):
        m = self.cfg['mission']
        return dict(schema_version=1, status=self.status, mission_start_sim=self.start,
                    mission_end_sim=self.end, duration_sim_s=None if self.start is None else self.end-self.start,
                    distance_m=self.length, search_area_m2=(m['search_max_x']-m['search_min_x'])*(m['search_max_y']-m['search_min_y']),
                    coverage_estimate=len(self.coverage.visited)/len(self.coverage.cells),
                    coverage_basis='1m cell camera-footprint proxy; occlusion not evaluated',
                    trajectory=self.path, detections=list(self.incidents.values()), events=self.events,
                    priority_counts={p:sum(o.get('priority')==p for o in self.incidents.values()) for p in ['P0','P1','P2','P3','P4','UNASSESSED']},
                    reference_origin=self.cfg['origin'], geolocation_status='SIMULATED_LOCAL_TANGENT_APPROXIMATION_NOT_RTK')

    def save(self, directory):
        d = Path(directory); d.mkdir(parents=True,exist_ok=True)
        report = self.report()
        for name, data in [('mission_report.json',report), ('incidents.geojson',self.geojson())]:
            tmp=d/(name+'.tmp'); tmp.write_text(json.dumps(data,indent=2,allow_nan=False),encoding='utf-8'); tmp.replace(d/name)
        body=html.escape(json.dumps(report,indent=2,ensure_ascii=False))
        (d/'mission_report.html').write_text('<!doctype html><meta charset="utf-8"><title>VAYU-NETRA mission report</title><style>body{font:16px system-ui;margin:40px;color:#183348}pre{white-space:pre-wrap}</style><h1>VĀYU-NETRA — SAR SIMULATION</h1><p>Runtime report. Simulation is not physical field validation.</p><pre>'+body+'</pre>',encoding='utf-8')
        return report

    def geojson(self):
        features=[]
        for o in self.incidents.values():
            if o['local_position'] is None: continue
            features.append(dict(type='Feature',geometry=dict(type='Point',coordinates=geodetic(o['local_position'],self.cfg['origin'])),properties={k:o.get(k) for k in ['id','class','priority','confidence','source','timestamp','position_method']}))
        return dict(type='FeatureCollection',features=features,reference='Simulated WGS84 small-area tangent approximation; not RTK')
