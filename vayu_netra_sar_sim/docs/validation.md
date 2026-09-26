# Validation record —22September2026

## Actually executed on the authoring PC

| Check | Result | Evidence / scope |
|---|---|---|
| Python package/core tests |27 passed,2 skipped | `validation/pytest.txt`; tests run on Windows Python3.11 |
| Quick core mission | COMPLETE;6person+6hazard fixtures;3reinspections | `validation/software_quick/`;128.2 simulated seconds |
| Full core mission | COMPLETE;6person+6hazard fixtures;3reinspections | `validation/software_full/`;201.2 simulated seconds |
| Feedback, arming denial, pipeline failure | Abort behavior tested | `test_mission_state.py` |
| Coordinate axes and nadir depth projection | Passed | `test_coordinates.py` |
| Priority thresholds / confidence separation | Passed | `test_triage.py` |
| Reports / GeoJSON / source syntax / XML parsing | Passed | Core tests; XML parsing is not Gazebo SDF validation |
| Shell syntax | All supplied shell files passed `bash -n` | Git Bash on Windows; no Ubuntu installation executed |
| Pinned wire definitions |9/9 match | `validation/source_contract.json`; normalized fields/constants compared with official sources |
| Real YOLO adapter | One real-photo person detection on PC | `validation/yolo_adapter_pc_smoke.json`; NumPy image transport, not cv_bridge/ROS |
| Environment checker | Correctly rejects this Windows host | `validation/environment.json`; explicit missing runtime dependencies |

The single YOLO call is a cold-start smoke test including prediction setup; its
recorded timing is not a warmed benchmark, FPS measurement, accuracy evaluation
or a Jetson claim. The image came from the existing COCO128 smoke dataset, with
potential training overlap. No SAR accuracy statistic is inferred from it.

The software fixture's100%coverage result means all configured1m cells entered the
footprint proxy during the programmed route; it does not establish real visual
coverage, recall or rescue effectiveness.

## Not executed here

Ubuntu24.04 dependency installation; Agent/PX4 compilation; colcon build; native
ROS-node startup and QoS exchange; actual Gazebo SDF loading/rendering; PX4 flight,
simulator sensor timing; full-stack search/reinspection/landing; GPU performance;
actual target shutdown and restart. The two ROS-dependent tests are SKIPPED, not
passed. The package cannot be labelled target-runtime validated yet.

`validate_target.sh` and the checklist capture that evidence on your Ubuntu laptop.
They must be executed and failures resolved there. Source inspection and Windows
tests cannot close these acceptance items remotely without access to that environment.

## Hardware claims

The latest user brief states that a basic UAV, Jetson Nano, RGB/YOLOv8n pipeline and
Cube work have been validated by the team. That supersedes the earlier reported
hardware inventory, but no new hardware logs were independently inspected in this
turn. The simulator is not evidence of RB5 testing, real thermal/depth integration,
medical prioritization or a deployed autonomous SAR aircraft.
