"""Kinematic fixture exercises the actual mission engine. NOT PX4/Gazebo flight validation."""
import argparse
import json
import math
import time
from pathlib import Path
from .configuration import load
from .mission_manager import Mission
from .simulated_perception import SimulatedPerception
from .triage_engine import assess
from .report_generator import Recorder


def run(cfg,directory,fault=None,realtime=False,callback=None):
    mission=Mission(cfg);detector=SimulatedPerception(cfg);rec=Recorder(cfg)
    f=dict(position=[0.,0.,.25],valid=True,fresh=True,ready=True,armed=False,offboard=False,landed=True,speed=0.,battery=None,yaw=0.)
    dt=.1;events=0
    for step in range(15000):
        now=step*dt
        if fault=='feedback' and now>12:f['fresh']=False
        if fault=='arm_denied':f['armed']=False
        if fault=='pipeline' and now>20:f['ready']=False
        out=mission.tick(now,f)
        if out['command']=='OFFBOARD':f['offboard']=True
        if out['command']=='ARM' and fault!='arm_denied':f['armed']=True;f['landed']=False
        before=list(f['position'])
        if out['command']=='LAND':
            f['position'][2]=max(.25,f['position'][2]-.8*dt)
            if f['position'][2]<=.25:f['landed']=True;f['armed']=False
        elif f['armed'] and out['goal']:
            diff=[out['goal'][i]-f['position'][i] for i in range(3)];length=math.sqrt(sum(x*x for x in diff))
            scale=min(1,cfg['mission']['search_speed']*dt/max(length,1e-9))
            f['position']=[f['position'][i]+scale*diff[i] for i in range(3)]
        f['speed']=math.dist(before,f['position'])/dt;f['timestamp']=now;f['source']='KINEMATIC_SOFTWARE_TEST_FIXTURE'
        if step%5==0:
            for o in detector.observe(f['position'],now,yaw=0.,reinspect_id=out.get('active_target') if out['state']=='REINSPECTION' else None):
                reviewed=assess(o,cfg);rec.observation(reviewed);mission.observe(reviewed)
        rec.pose(now,f['position'],out['state']=='SEARCH',True);rec.status=out['state']
        rec.events.extend(mission.events[events:]);events=len(mission.events)
        if callback and step%5==0:callback(dict(flight=f,mission=dict(out,search_grid=mission.points),map=rec.report(),metrics={'source':'simulated'},updated_wall=time.time()))
        if out['state'] in mission.TERMINAL:break
        if realtime:time.sleep(dt)
    else:raise RuntimeError('Software fixture exceeded step budget')
    report=rec.save(directory)
    report['validation_scope']='PURE_PYTHON_KINEMATIC_FIXTURE_NOT_ROS_PX4_GAZEBO'
    (Path(directory)/'test_result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--output',required=True);parser.add_argument('--realtime',action='store_true');parser.add_argument('--serve',action='store_true');args=parser.parse_args()
    callback=None;server=None
    if args.serve:
        # This fallback deliberately requires no ROS imports.
        import threading
        from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
        state={}
        page=Path(__file__).parents[1]/'web/index.html'
        class Handler(SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path=='/api/state':body=json.dumps(state).encode();kind='application/json'
                elif self.path=='/':body=page.read_bytes();kind='text/html; charset=utf-8'
                else:self.send_error(404);return
                self.send_response(200);self.send_header('Content-Type',kind);self.end_headers();self.wfile.write(body)
            def log_message(self,*a):pass
        server=ThreadingHTTPServer(('127.0.0.1',8080),Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start();callback=lambda s:state.update(s)
        print('SOFTWARE FIXTURE ONLY — http://127.0.0.1:8080',flush=True)
    try:
        r=run(load(args.config),args.output,realtime=args.realtime,callback=callback)
        print(json.dumps({'status':r['status'],'simulation_seconds':r['duration_sim_s'],'detections':len(r['detections']),'scope':r['validation_scope']}))
        if server:input('Mission complete. Press Enter to close dashboard. ')
    finally:
        if server:server.shutdown();server.server_close()


if __name__=='__main__':main()
