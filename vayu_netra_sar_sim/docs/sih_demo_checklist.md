# Rehearsal and acceptance checklist

- [ ] Ubuntu24.04/Jazzy/Harmonic environment check passes and versions are saved.
- [ ] PX4/px4_msgs SHA and wire contract checks pass.
- [ ] Colcon build and installed executable discovery pass.
- [ ] All local tests pass; ROS-dependent tests are executed on target, not counted as passed when skipped.
- [ ] Cold start: Agent/world/PX4/ROS launch without manual file creation.
- [ ] RGB/depth topics receive frames; timestamps and sim clock agree.
- [ ] OFFBOARD, arming and altitude are confirmed from feedback.
- [ ] Both search modes complete with six survivors and six hazard fixtures.
- [ ] At least one fresh second observation, priority update and search resume is recorded.
- [ ] Return and native landing complete; landed AND disarmed feedback is observed.
- [ ] JSON/HTML/GeoJSON outputs match the runtime scene and unique track counters.
- [ ] `validate_target.sh` passes for the deterministic full-stack demo.
- [ ] Kill perception in a controlled SITL rehearsal: mission aborts and PX4 landing/fallback is checked.
- [ ] Stop Agent in a controlled SITL rehearsal: timeout is visible and no false completion is recorded.
- [ ] Pause simulation clock: mission progress does not advance; resume behavior is inspected.
- [ ] Ctrl+C/clean.sh removes this run's child processes; no lingering port8888/8080 owner.
- [ ] Repeat a second launch to catch persistent-state/resource errors.
- [ ] Disable internet after installation and repeat the demo.
- [ ] Test `--realtime --serve` fallback and state clearly that it is not flight dynamics.
- [ ] Check operator-facing mode labels and avoid unmeasured accuracy/power/endurance claims.

Each unchecked item remains a target-machine acceptance task. An unchecked runtime
item is not converted into a “passed” claim by unit tests or source inspection.
