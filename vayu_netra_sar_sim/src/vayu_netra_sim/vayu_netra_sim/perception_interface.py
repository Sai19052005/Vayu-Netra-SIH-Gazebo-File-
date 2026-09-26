"""Versioned JSON envelope transported by std_msgs/String. Null context is never fabricated."""
import math
from typing import Protocol


class PerceptionInterface(Protocol):
    def observe(self, pose, timestamp, **kwargs): ...


def validate(o):
    for key in ('schema_version', 'id', 'class', 'confidence', 'timestamp', 'bbox',
                'uav_pose', 'local_position', 'source', 'observation_id'):
        if key not in o:
            raise ValueError('Missing observation field: '+key)
    if o['schema_version'] != 1 or not isinstance(o['id'], str):
        raise ValueError('Unsupported observation schema')
    if not math.isfinite(o['timestamp']) or not 0 <= o['confidence'] <= 1:
        raise ValueError('Invalid confidence/time')
    if len(o['bbox']) != 4 or not all(math.isfinite(x) for x in o['bbox']):
        raise ValueError('Invalid bounding box')
    if not (0 <= o['bbox'][0] < o['bbox'][2] and 0 <= o['bbox'][1] < o['bbox'][3]):
        raise ValueError('Bounding box must be xyxy pixels')
    for k in ('uav_pose', 'local_position'):
        if o[k] is not None and (len(o[k]) != 3 or not all(math.isfinite(x) for x in o[k])):
            raise ValueError('Invalid '+k)
    if o['source'] not in ('SIMULATED_PERCEPTION', 'REAL_YOLO_INFERENCE_SIMULATED_RGB', 'REAL_YOLO_INFERENCE_RGB'):
        raise ValueError('Unrecognized provenance')
    return o
