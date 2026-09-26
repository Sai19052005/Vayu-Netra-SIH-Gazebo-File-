from vayu_netra_sim.mission_manager import Mission
from vayu_netra_sim.software_test import run


def test_no_arm_from_sent_command(cfg):
    m=Mission(cfg);m.state='VERIFY_ARMED';m.started=0;m.entered=0
    f=dict(fresh=True,valid=True,armed=False,offboard=True,ready=True,landed=True,position=[0,0,0])
    assert m.tick(1,f)['state']=='VERIFY_ARMED'


def test_complete_closed_loop(cfg,tmp_path):
    r=run(cfg,tmp_path)
    assert r['status']=='COMPLETE'
    assert len([o for o in r['detections'] if o['class']=='person'])==6
    assert len([o for o in r['detections'] if o['class']!='person'])==6
    events=[e['event'] for e in r['events']]
    assert all(x in events for x in ['VERIFY_OFFBOARD','VERIFY_ARMED','VERIFY_ALTITUDE','REINSPECTION','SECOND_OBSERVATION','UPDATE','RESUME_SEARCH','RETURN_HOME','VERIFY_LANDED','COMPLETE'])
    assert r['coverage_estimate']>.9
    assert next(o for o in r['detections'] if o['id']=='SURVIVOR_01')['priority']=='P2'


def test_feedback_loss_aborts(cfg,tmp_path):
    assert run(cfg,tmp_path,fault='feedback')['status']=='ABORTED'


def test_arm_denial_aborts(cfg,tmp_path):
    assert run(cfg,tmp_path,fault='arm_denied')['status']=='ABORTED'


def test_pipeline_loss_aborts(cfg,tmp_path):
    assert run(cfg,tmp_path,fault='pipeline')['status']=='ABORTED'


def test_clock_reset(cfg):
    m=Mission(cfg);m.tick(10,{});m.tick(5,{})
    assert m.aborting
