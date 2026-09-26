# SIH live demonstration — approximately3–5minutes

Before the presentation, complete target-machine acceptance, warm the laptop,
confirm graphics and run the exact same package/configuration offline. Do not install
dependencies or download weights in front of judges.

| Approximate time | Action / honest narration |
|---|---|
| 00:00 | Show the disaster world and dashboard. “This is our autonomous SAR software demonstrator in PX4/Gazebo.” |
| 00:20 | Observe readiness, OFFBOARD and arming verification. “The controller advances from aircraft feedback.” |
| 00:40 | Show takeoff and cyan search grid. “The vehicle follows an altitude-separated rectangular search.” |
| 01:00 | Highlight a survivor and hazard entry. “This run uses explicitly simulated perception; it is not YOLO accuracy evidence.” |
| 01:20 | Point to the P0/P1 entry. “Priority uses scene risk and context, independently of detection confidence.” |
| 01:40 | Show REINSPECTION and saved search index. “A high-priority observation changes the route.” |
| 02:00 | Show SECOND_OBSERVATION, UPDATE and priority change. “The scenario supplies new context; the software updates its record.” |
| 02:20 | Show resumed search and trajectory. Explain remaining detections and optional perception adapter. |
| 03:00 | Show RETURN_HOME, then LAND/VERIFY_LANDED. Never narrate completion before feedback confirms it. |
| 03:30–04:30 | Open mission_report.html/GeoJSON and explain offline responder information. |

These are presentation cues, not asserted runtime timestamps. Startup and real-time
factor vary. If a stage has not happened, explain its actual current state.

## Backup route

Stop the3D session with Ctrl+C and confirm shutdown. Run:

```bash
./run_test_mode.sh --realtime --serve
```

Say: “This backup exercises the same mission software with a deterministic
kinematic fixture. PX4 and Gazebo are not running in this mode.” Show the browser
map, priorities, reinspection and generated report. If no live run is possible,
show saved validation reports, explicitly calling them recorded software-test output.

## Real YOLO demonstration

Keep it separate from the reliable symbolic-world walkthrough. Show actual RGB
input, resulting boxes and measured software timings from your real-data pipeline,
or launch the optional adapter after testing it on the laptop. A failure to recognize
primitive Gazebo figures must remain visible, not replaced by oracle coordinates
under a YOLO label. Do not claim hazard detection from a person-only pretrained model.

## Allowed claims

“We implemented a closed-loop SAR simulation architecture and tested its core state
machine.” After actual target acceptance, add the exact demonstrated PX4/Gazebo
capabilities and logs. Hardware status is team-reported unless supported by supplied
test evidence. RB5, thermal hardware and full physical SAR deployment remain future work.
