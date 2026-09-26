"""Real pixel inference. Never imports the scenario oracle or reads target coordinates."""
import time
from pathlib import Path
from .coordinates import depth_to_world
from .perception_interface import validate


class YOLOPerception:
    def __init__(self,cfg,model,bridge=None):
        if not model or not Path(model).is_file():raise FileNotFoundError('Provide local --model yolov8n.pt; downloads are forbidden during missions')
        from ultralytics import YOLO
        if bridge is None:
            from cv_bridge import CvBridge
            bridge=CvBridge()
        self.model,self.bridge,self.cfg=YOLO(model),bridge,cfg
        self.tracks,self.sequence={},0

    def observe(self,pose,timestamp,**kwargs):
        import numpy as np
        image=self.bridge.imgmsg_to_cv2(kwargs['image'],'bgr8')
        start=time.perf_counter()
        result=self.model.predict(image,classes=[0],conf=self.cfg['perception']['confidence_threshold'],imgsz=640,device='cpu',verbose=False)[0]
        elapsed=(time.perf_counter()-start)*1000
        depth=kwargs.get('depth');array=None
        if depth is not None and abs(depth.header.stamp.sec+depth.header.stamp.nanosec/1e9-timestamp)<=self.cfg['perception']['max_depth_age']:
            array=self.bridge.imgmsg_to_cv2(depth,'passthrough')
            if depth.encoding=='16UC1':array=array.astype(float)*.001
            elif depth.encoding!='32FC1':array=None
        out=[];assigned=set()
        for b in result.boxes:
            box=b.xyxy[0].tolist();confidence=float(b.conf[0]);u=int((box[0]+box[2])/2);v=int((box[1]+box[3])/2)
            point=None
            if array is not None and kwargs.get('k') and kwargs.get('quaternion') and 1<=v<array.shape[0]-1 and 1<=u<array.shape[1]-1:
                crop=array[v-1:v+2,u-1:u+2];good=crop[np.isfinite(crop)&(crop>.2)&(crop<50)]
                if len(good)>=5:point=depth_to_world(u,v,float(np.median(good)),kwargs['k'],pose,kwargs['quaternion'])
            matches=[(np.linalg.norm(np.array(point)-np.array(p)),id) for id,(p,t) in self.tracks.items()
                     if point is not None and id not in assigned and timestamp-t<30]
            match=min(matches,default=(float('inf'),None))
            self.sequence+=1
            id=match[1] if match[0]<1.5 else f'YOLO_TRACK_{self.sequence:05}'
            if point is not None:self.tracks[id]=(point,timestamp)
            assigned.add(id)
            out.append(validate(dict(schema_version=1,id=id,observation_id=f'{id}:{self.sequence}',
                **{'class':'person'},confidence=confidence,timestamp=timestamp,bbox=box,uav_pose=pose,
                local_position=point,position_method='GAZEBO_DEPTH_CENTRE_ASSOCIATION' if point else 'UNAVAILABLE',
                source='REAL_YOLO_INFERENCE_SIMULATED_RGB' if kwargs.get('sensor_source','GAZEBO_CAMERA')=='GAZEBO_CAMERA' else 'REAL_YOLO_INFERENCE_RGB',sensor_source=kwargs.get('sensor_source','GAZEBO_CAMERA'),
                context=None,context_source=None,thermal=None,depth={'associated':point is not None},inference_ms=elapsed)))
        self.tracks={id:(p,t) for id,(p,t) in self.tracks.items() if timestamp-t<30}
        return out
