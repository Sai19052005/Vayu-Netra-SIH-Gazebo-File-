# Architecture and engineering contract

## System layout

```text
Gazebo Harmonic: disaster_zone + X500-derived vayu_netra_0
  ├─ native simulated IMU / GNSS / pressure → PX4 gz_bridge → PX4 SITL
  └─ nadir RGBD → ros_gz_bridge → ROS Image / CameraInfo
PX4 SITL ↔ Micro XRCE-DDS Agent2.4.3 ↔ ROS2 Jazzy
  └─ offboard_controller: feedback, commands, rate-limited setpoints, watchdog
      ↔ mission_manager: planner + verified state machine + reinspection queue
RGB image + time-matched flight pose
  ├─ SimulatedPerception: explicit scenario oracle
  └─ YOLOPerception: genuine CPU inference, no scenario coordinates
        ↓ common observation schema
  thermal_simulator → separate thermal fixture topic
        ↓ ID/time association
  fusion_triage → mission_manager + mapping
  mapping → GeoJSON / JSON / HTML + RViz markers + dashboard
```

Flight control, image inference, fusion, recording and web serving are separate
processes. Slow inference cannot directly block the20Hz offboard publisher.
The web server does not command flight. The coordinator uses a pure Python engine
also executed in the software fixtures and tests.

## Source compatibility

PX4v1.17.0 and the pinned release/1.17 message snapshot share the nine wire schemas
used here. The build repeats a normalized field/constant comparison. Changing a
tag, branch or Python message package without passing that comparison is rejected.
The runtime topic helper adds `_vN` when `MESSAGE_VERSION` is nonzero, as required
by versioned PX4 messages. We do not require a translation node for matching schemas.
Read [message versioning](https://docs.px4.io/main/en/ros2/px4_ros2_msg_translation_node).

## Important topics

| Topic | Type / ownership |
|---|---|
| `/clock` | rosgraph_msgs/Clock, bridged from `/world/disaster_zone/clock` |
| `/fmu/out/vehicle_status_v1` | px4_msgs/VehicleStatus |
| `/fmu/out/vehicle_local_position_v1` | px4_msgs/VehicleLocalPosition |
| `/fmu/out/battery_status_v1` | px4_msgs/BatteryStatus |
| `/fmu/out/vehicle_attitude` | px4_msgs/VehicleAttitude |
| `/fmu/out/vehicle_land_detected` | px4_msgs/VehicleLandDetected |
| `/fmu/out/vehicle_command_ack` | px4_msgs/VehicleCommandAck |
| `/fmu/in/offboard_control_mode` | px4_msgs/OffboardControlMode |
| `/fmu/in/trajectory_setpoint` | px4_msgs/TrajectorySetpoint |
| `/fmu/in/vehicle_command` | px4_msgs/VehicleCommand |
| `/vayu/camera/image`, `/vayu/camera/depth_image` | sensor_msgs/Image, Gazebo RGBD |
| `/vayu/camera/camera_info` | sensor_msgs/CameraInfo |
| `/vayu/flight`, `/vayu/control`, `/vayu/mission` | version-controlled application JSON, std_msgs/String |
| `/vayu/detections`, `/vayu/thermal_observations`, `/vayu/triage` | observation / fixture / assessment JSON |
| `/vayu/map`, `/vayu/events`, `/vayu/health`, `/vayu/perception_metrics` | runtime application JSON |
| `/vayu/map_markers` | visualization_msgs/MarkerArray |

PX4 output subscriptions and camera streams use sensor-data QoS: best effort,
volatile. Command publishers and application JSON use reliable volatile queues.
Application messages are JSON to avoid another custom message build package; the
perception envelope is validated, but this is not a full ROS IDL schema system.

## Mission state machine

```text
INIT → WAIT_FOR_PX4 → WAIT_FOR_LOCAL_POSITION
→ PUBLISH_OFFBOARD_HEARTBEAT (>=2s)
→ REQUEST_OFFBOARD → VERIFY_OFFBOARD
→ REQUEST_ARM → VERIFY_ARMED
→ TAKEOFF → VERIFY_ALTITUDE → SEARCH
→ REINSPECTION → UPDATE → RESUME_SEARCH → SEARCH
→ RETURN_HOME → LAND → VERIFY_LANDED → COMPLETE
Any operational fault → LAND → VERIFY_LANDED → ABORTED
```

Commands are retried at1Hz, with configurable state deadlines. ACKs are logged;
actual mode/arming feedback determines progression. No forced-arm magic number
or airborne disarm is used. Landing completion requires fresh landed feedback AND
disarmed state. If landing cannot be confirmed, result is ABORTED, not COMPLETE.

Missing valid position, stale feedback, lost OFFBOARD/arming, stopped pipeline
heartbeats or mission timeout aborts search. A controller-local wall-clock watchdog
stops heartbeat transmission if mission commands or flight feedback become stale.
PX4's configured offboard-loss fallback is Land after1s. This is SITL-specific;
loss of estimator position may change what PX4 can safely accomplish physically.
Clock pause stops mission progression; no fake frames or simulated time are added
to keep an apparently successful demo running.

## Planner and restricted areas

The supported search polygon is an axis-aligned rectangle. Alternating horizontal
passes include the final boundary even when spacing does not divide its height.
Every segment is checked against configured restricted rectangles with a0.5m
margin. A conflicting configuration fails; arbitrary polygon clipping and obstacle
avoidance are not implemented. Reinspection and resume segments use the same check.

Scene obstacles are at most7m; survey altitude is12m. Routes use altitude separation,
not learned collision avoidance. The restriction is outside the default search box.
Do not lower altitude into scene obstacles or claim safe routing around unknown debris.

## Sensor and perception flows

RGB/depth are real Gazebo sensor outputs. Thermal is a separately labelled fixture
with `temperature_c:null`; it is not simulated radiometric imagery. IMU/GNSS feed
PX4 through its native simulator bridge and reach ROS through the resulting estimator
messages. There is no artificial battery drain function; unavailable battery is null.

Default simulated perception waits for actual RGB messages, a fresh pose and a
valid projected view before emitting an authored target. Bounding boxes are derived
from projection; confidence0.90 is a fixed fixture value, not a measured probability.
Its exact local position is labelled `SCENARIO_ORACLE_NOT_MEASURED`. Occlusion is not
checked. Humanoid primitives are chosen for stable offline visualization, not to
make a pretrained neural network magically recognize them.

Real YOLO takes pixel arrays, filters class0/person and records elapsed inference
call time. It never imports the scenario target list. Model download is an explicit
installation step. CPU execution is the laptop target; no GPU/Jetson timing claim
is made. Depth association uses a valid3x3 region at box centre, intrinsics and a
time-matched attitude. Depth must be32FC1 metres or16UC1 millimetres; invalid depth
leaves position null. Median box-centre depth may belong to background, so it is
only a demonstrative association, not a validated survivor range estimator.

Image and pose timestamps must agree within0.3s; depth within0.10s. Queues are
bounded. Latest image callbacks are throttled to avoid unnecessary compute load.
Real YOLO tracks use proximity plus an age limit and are not guaranteed unique-person
IDs. Local position absent means no geolocation or automatic revisit for that box.

## Observation contract

```json
{"schema_version":1,"id":"SURVIVOR_01","observation_id":"SURVIVOR_01:2",
 "class":"person","confidence":0.9,"timestamp":12.0,"bbox":[10,20,30,60],
 "uav_pose":[0,0,12],"local_position":[-10,-9,0.8],
 "source":"SIMULATED_PERCEPTION","position_method":"SCENARIO_ORACLE_NOT_MEASURED",
 "context":{"hazard_severity":0.9,"victim_context":0.9,"accessibility_risk":0.9},
 "context_source":"AUTHORED_SCENARIO","thermal":null,"depth":null,"inference_ms":null}
```

This is an illustrative envelope, not a captured detection. Nullable modalities are
preserved. The fusion node associates explicit ID and observation ID within0.2s,
waiting at most0.3wall-seconds; missing thermal does not block detections forever.
It does not associate anonymous thermal blobs to RGB boxes or infer physiology.

## Triage

`risk = 0.45*hazard_severity + 0.30*victim_context + 0.25*accessibility_risk`.
Inputs are normalized0..1. Defaults: P0>=0.85 Critical; P1>=0.65 Very High;
P2>=0.45 High; P3>=0.25 Moderate; otherwise P4 Low/Monitor.
All values are configurable and validated in YAML.

Detection confidence is stored separately and used for detection filtering, never
as a medical urgency surrogate. Missing context yields UNASSESSED. Thus real YOLO
does not automatically manufacture priorities or patient status. Thermal fixture
corroboration is stored but does not raise medical urgency. The framework is a team
engineering demonstration, not an official universal or clinically validated standard.

## Reinspection

P0/P1 persons with positions enter a queue. The engine saves the current search
index, chooses a permitted target, moves to its location at survey altitude, and
waits for a new observation AFTER arrival within the configured radius. It then
records UPDATE and resumes the saved waypoint. There is one attempt per incident
to prevent endless revisits. Timeout resumes search with an explicit failed-review
event; no second observation is fabricated to force completion.

The authored scenario changes context for three targets only during a close
reinspection and retains that change thereafter. It demonstrates software updating
an assessment; it is not evidence of a medical change or real sensor fusion.

## Frames, mapping and timing

Gazebo/world and mission `map` are ENU: X east, Y north, Z up, metres. PX4 is NED;
conversion is `[E,N,U] = [y,x,-z]` plus the EKF reference-origin offset. PX4 body is
FRD and its quaternion is wxyz. The nadir camera is0.12m below the body, pitched90°
in FLU; optical right maps to FRD+y and optical down maps to FRD−x. Controller heading
is fixed east for stable demonstration geometry.

The reference is18.5204°N,73.8567°E,560m AMSL in the world and both mission configs.
Local estimator reference latitude/longitude/altitude is converted to this tangent
frame before coordinates are used. Estimator reset counters changing while armed
invalidate control and trigger abort. GeoJSON uses `[longitude,latitude,altitude]`;
a WGS84 small-area tangent approximation is used, not RTK or a geodetic survey.

Application clocks use bridged Gazebo `/clock`; PX4 time synchronization is disabled
with `UXRCE_DDS_SYNCT=0` for this common simulation-time arrangement. Wall-monotonic
time is used for watchdogs and inference durations. The ROS graph uses domain42;
the supervisor creates a unique Gazebo partition. Never run another publisher on
the same `/fmu/in` channels during a demonstration.

Coverage is the fraction of1m grid cells inside a nadir footprint proxy while
searching with recent RGB. It does not prove unoccluded observation or detector
recall. Reported path length comes from received positions, not planned waypoints.

## Packaging and extension points

`launch/sar.launch.py` installs with all resources. Each console entry point maps to
an existing module. `scripts/supervisor.py` owns child groups and retains logs;
`clean.sh` only signals that registered supervisor after PID/start-time validation.
The default world uses no internet/Fuel assets: upstream X500 resources are installed
with the pinned PX4 submodule during setup. No existing project files are modified.

Future GPS-denied navigation, obstacle-aware planning, thermal radiometry, full
RGB/thermal/depth fusion, field priority validation and RB5 deployment are separate
workstreams. Neither this simulated X500's mass nor its battery model represents
the earlier proposed4.1kg hardware BOM.
