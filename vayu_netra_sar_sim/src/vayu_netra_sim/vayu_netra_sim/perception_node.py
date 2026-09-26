import time
from collections import deque
from .ros_support import Base, spin, qos_profile_sensor_data
from .simulated_perception import SimulatedPerception
from sensor_msgs.msg import Image, CameraInfo


class PerceptionNode(Base):
    def __init__(self):
        super().__init__('perception')
        self.mode=self.declare_parameter('perception_mode','simulated').value
        self.poses=deque(maxlen=100);self.depth=None;self.k=None;self.image_seen=0;self.last_processed=0
        self.mission={}
        self.listen('/vayu/mission',lambda m:setattr(self,'mission',m))
        self.listen('/vayu/flight',lambda f:self.poses.append(f))
        if self.mode=='simulated':self.detector=SimulatedPerception(self.cfg)
        elif self.mode=='yolo':
            from .yolo_perception import YOLOPerception
            model=self.declare_parameter('model_path','').value
            self.detector=YOLOPerception(self.cfg,model)
        else:raise ValueError('perception_mode must be simulated or yolo; no silent fallback')
        self.create_subscription(Image,'/vayu/camera/image',self.image,qos_profile_sensor_data)
        self.create_subscription(Image,'/vayu/camera/depth_image',lambda m:setattr(self,'depth',m),qos_profile_sensor_data)
        self.create_subscription(CameraInfo,'/vayu/camera/camera_info',lambda m:setattr(self,'k',list(m.k)),qos_profile_sensor_data)

    def health(self):
        self.health_ok=time.monotonic()-self.image_seen<3
        super().health()

    def image(self,msg):
        self.image_seen=time.monotonic()
        ts=msg.header.stamp.sec+msg.header.stamp.nanosec/1e9
        if not self.poses or time.monotonic()-self.last_processed<.15:return
        f=min(self.poses,key=lambda f:abs((f.get('pose_timestamp') or f['timestamp'])-ts))
        pose_ts=f.get('pose_timestamp') or f['timestamp']
        if not f.get('valid') or not f.get('fresh') or abs(pose_ts-ts)>self.cfg['perception']['max_pose_age']:return
        if self.mode=='yolo' and abs((f.get('attitude_timestamp') or 0)-ts)>.3:return
        self.last_processed=time.monotonic();started=time.perf_counter()
        if self.mode=='simulated':obs=self.detector.observe(f['position'],ts,yaw=f['yaw'],image=True,reinspect_id=self.mission.get('active_target') if self.mission.get('state')=='REINSPECTION' else None)
        else:obs=self.detector.observe(f['position'],ts,image=msg,depth=self.depth,k=self.k,quaternion=f['quaternion'])
        for o in obs:
            if o['confidence']>=self.cfg['perception']['confidence_threshold'] and o['class'] in self.cfg['perception']['classes']:
                self.send('/vayu/detections',o)
        self.send('/vayu/perception_metrics',dict(timestamp=ts,source=self.mode,callback_ms=(time.perf_counter()-started)*1000,observations=len(obs)))


def main():spin(PerceptionNode)
