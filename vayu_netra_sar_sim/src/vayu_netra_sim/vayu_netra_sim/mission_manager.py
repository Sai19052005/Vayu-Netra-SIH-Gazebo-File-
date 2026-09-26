"""Pure feedback-driven mission engine; same engine runs under ROS and software tests."""
import math
from .coordinates import distance
from .search_planner import plan
from .reinspection_manager import ReinspectionManager


class Mission:
    TERMINAL = {'COMPLETE', 'ABORTED'}
    FLIGHT = {'TAKEOFF','VERIFY_ALTITUDE','SEARCH','REINSPECTION','UPDATE','RESUME_SEARCH','RETURN_HOME'}

    def __init__(self, cfg):
        self.cfg, self.m = cfg, cfg['mission']
        self.points = plan(self.m, cfg['scene']['restricted_zones'])
        self.state, self.entered, self.started = 'INIT', 0., None
        self.index, self.goal, self.home = 0, None, None
        self.events, self.review = [], ReinspectionManager(cfg)
        self.active, self.arrived_at, self.reobserved = None, None, False
        self.aborting, self.reason = False, ''
        self.last_time = None

    def transition(self, state, now, detail=''):
        self.events.append(dict(timestamp=now, event=state, detail=detail))
        self.state, self.entered = state, now

    def observe(self, o):
        self.review.offer(o)
        if (self.active and o['id'] == self.active['id'] and self.arrived_at is not None
                and o['timestamp'] > self.arrived_at and o['observation_id'] != self.active['observation_id']):
            self.reobserved = True
            self.events.append(dict(timestamp=o['timestamp'], event='SECOND_OBSERVATION',
                                    detail=o['id'], priority=o.get('priority')))

    def abort(self, now, why):
        if self.state not in self.TERMINAL and not self.aborting:
            self.aborting, self.reason = True, why
            self.transition('LAND', now, why)

    def tick(self, now, f):
        if self.started is None:
            self.started, self.entered = now, now
        if self.last_time is not None and now < self.last_time:
            self.abort(now, 'Clock moved backwards')
        self.last_time = now
        if self.state in self.TERMINAL:
            return self.output()
        fresh = f.get('fresh', False)
        engaging={'PUBLISH_OFFBOARD_HEARTBEAT','REQUEST_OFFBOARD','VERIFY_OFFBOARD','REQUEST_ARM','VERIFY_ARMED'}
        if self.state in engaging and (not fresh or not f.get('valid') or not f.get('ready')):
            self.abort(now, 'Readiness lost during offboard/arming sequence')
        if self.state in {'REQUEST_ARM','VERIFY_ARMED'} and not f.get('offboard'):
            self.abort(now, 'Offboard lost before arming confirmation')
        if self.state in self.FLIGHT and (not fresh or not f.get('valid') or not f.get('armed') or not f.get('offboard') or not f.get('ready')):
            self.abort(now, 'Lost feedback, validity, flight mode or pipeline heartbeat')
        if self.state in self.FLIGHT and f.get('battery', 1) is not None and f.get('battery', 1) < self.m['rtl_battery']:
            self.transition('RETURN_HOME', now, 'Battery return threshold')
        if self.state in self.FLIGHT and now-self.started > self.m['mission_timeout']:
            self.abort(now, 'Mission timeout')
        if self.state not in self.FLIGHT | self.TERMINAL | {'LAND','VERIFY_LANDED'} and now-self.entered > self.m['state_timeout']:
            self.abort(now, 'Startup/command timeout: '+self.state)
        s = self.state
        if s == 'INIT': self.transition('WAIT_FOR_PX4', now)
        elif s == 'WAIT_FOR_PX4' and fresh: self.transition('WAIT_FOR_LOCAL_POSITION', now)
        elif s == 'WAIT_FOR_LOCAL_POSITION' and fresh and f.get('valid') and f.get('ready') and f.get('landed') and not f.get('armed'):
            self.home = list(f['position'])
            self.goal = list(self.home)
            self.transition('PUBLISH_OFFBOARD_HEARTBEAT', now)
        elif s == 'PUBLISH_OFFBOARD_HEARTBEAT' and now-self.entered >= 2:
            self.transition('REQUEST_OFFBOARD', now)
        elif s == 'REQUEST_OFFBOARD': self.transition('VERIFY_OFFBOARD', now)
        elif s == 'VERIFY_OFFBOARD' and fresh and f.get('offboard'): self.transition('REQUEST_ARM', now)
        elif s == 'REQUEST_ARM': self.transition('VERIFY_ARMED', now)
        elif s == 'VERIFY_ARMED' and fresh and f.get('armed') and f.get('offboard'):
            self.goal = [*self.home[:2], self.m['search_altitude']]
            self.transition('TAKEOFF', now)
        elif s == 'TAKEOFF': self.transition('VERIFY_ALTITUDE', now)
        elif s == 'VERIFY_ALTITUDE':
            if self.reached(f):
                self.goal = self.points[0]
                self.transition('SEARCH', now)
            elif now-self.entered > self.m['state_timeout']: self.abort(now, 'Takeoff timeout')
        elif s == 'SEARCH':
            review = self.review.take(f['position'], self.points[self.index])
            if review:
                self.active, self.goal = review
                self.arrived_at, self.reobserved = None, False
                self.transition('REINSPECTION', now, self.active['id'])
            elif self.reached(f):
                self.index += 1
                if self.index == len(self.points): self.transition('RETURN_HOME', now)
                else: self.goal = self.points[self.index]
        elif s == 'REINSPECTION':
            close = (f.get('valid') and self.goal is not None and distance(f['position'], self.goal) < self.m['reinspection_radius'])
            if close and self.arrived_at is None:
                self.arrived_at = now
                self.events.append(dict(timestamp=now,event='REINSPECTION_ARRIVED',detail=self.active['id']))
            if self.reobserved:
                self.transition('UPDATE', now, self.active['id'])
            elif now-self.entered > self.m['reinspection_timeout']:
                self.transition('RESUME_SEARCH', now, 'Reinspection timed out: no fabricated second observation')
        elif s == 'UPDATE': self.transition('RESUME_SEARCH', now)
        elif s == 'RESUME_SEARCH':
            self.active, self.goal = None, self.points[self.index]
            self.transition('SEARCH', now)
        elif s == 'RETURN_HOME':
            self.goal = [*self.home[:2], self.m['search_altitude']]
            if self.reached(f): self.transition('LAND', now)
        elif s == 'LAND': self.transition('VERIFY_LANDED', now)
        elif s == 'VERIFY_LANDED':
            if fresh and f.get('landed') and not f.get('armed'):
                self.transition('ABORTED' if self.aborting else 'COMPLETE', now, self.reason)
            elif now-self.entered > self.m['state_timeout']:
                self.aborting = True
                self.transition('ABORTED', now, 'Landing not confirmed; PX4 failsafe owns vehicle')
        return self.output()

    def reached(self, f):
        return f.get('valid') and self.goal is not None and distance(f['position'], self.goal) < self.m['waypoint_tolerance'] and f.get('speed', 0) < 1.2

    def output(self):
        s = self.state
        command = ('OFFBOARD' if s in {'REQUEST_OFFBOARD','VERIFY_OFFBOARD'} else
                   'ARM' if s in {'REQUEST_ARM','VERIFY_ARMED'} else
                   'LAND' if s in {'LAND','VERIFY_LANDED'} else None)
        stream = s in self.FLIGHT | {'PUBLISH_OFFBOARD_HEARTBEAT','REQUEST_OFFBOARD','VERIFY_OFFBOARD','REQUEST_ARM','VERIFY_ARMED'}
        return dict(state=s, goal=self.goal, command=command, stream=stream,
                    search_index=self.index, search_total=len(self.points), reason=self.reason,
                    active_target=self.active['id'] if self.active else None)
