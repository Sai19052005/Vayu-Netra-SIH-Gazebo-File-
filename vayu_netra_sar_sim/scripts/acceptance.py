"""Run beside an active demo; asserts actual received data and completed state sequence."""
import argparse,json,time
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import String
from rosgraph_msgs.msg import Clock


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--timeout',type=float,default=420);parser.add_argument('--output',default='validation/target_acceptance.json');args=parser.parse_args()
    rclpy.init();node=Node('vayu_acceptance_observer');received={};states=set();events=[];latest={};began=time.monotonic()
    def observe(name,msg):
        received[name]=received.get(name,0)+1
        if isinstance(msg,String):
            d=json.loads(msg.data);latest[name]=d
            if name=='mission':states.add(d['state'])
            if name=='events':events.append(d)
    subscriptions=[]
    for name,topic,cls in [('clock','/clock',Clock),('rgb','/vayu/camera/image',Image),('depth','/vayu/camera/depth_image',Image),('mission','/vayu/mission',String),('flight','/vayu/flight',String),('detections','/vayu/detections',String),('triage','/vayu/triage',String),('map','/vayu/map',String),('events','/vayu/events',String)]:
        subscriptions.append(node.create_subscription(cls,topic,lambda m,n=name:observe(n,m),qos_profile_sensor_data if cls!=String else 20))
    try:
        while time.monotonic()-began<args.timeout:
            rclpy.spin_once(node,timeout_sec=.1)
            if latest.get('mission',{}).get('state') in ('COMPLETE','ABORTED'):
                # Allow last mapping/event callbacks to arrive.
                for _ in range(20):rclpy.spin_once(node,timeout_sec=.1)
                break
        f=latest.get('flight',{});report=latest.get('map',{})
        required={'SEARCH','REINSPECTION','RESUME_SEARCH','RETURN_HOME','VERIFY_LANDED','COMPLETE'}
        node_names=set(node.get_node_names())
        checks=dict(topics=all(received.get(n,0)>0 for n in ['clock','rgb','depth','flight','detections','triage','map']),
                    nodes={'offboard_controller','mission_manager','perception','fusion_triage','mapping','dashboard'}.issubset(node_names),
                    state_sequence=required.issubset(states),landed=f.get('landed') and not f.get('armed'),
                    second_observation=any(e['event']=='SECOND_OBSERVATION' for e in events+report.get('events',[])),
                    all_survivors=len([o for o in report.get('detections',[]) if o['class']=='person'])>=6,
                    report_complete=report.get('status')=='COMPLETE')
        result=dict(passed=all(checks.values()),checks=checks,received_counts=received,states=sorted(states),elapsed_wall_s=time.monotonic()-began,
                    scope='OBSERVED_ROS_GRAPH; inspect Gazebo and PX4 logs to confirm producer identity; not physical validation')
        out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2))
        print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
    finally:node.destroy_node();rclpy.shutdown()


if __name__=='__main__':raise SystemExit(main())
