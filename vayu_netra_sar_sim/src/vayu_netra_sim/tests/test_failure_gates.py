from vayu_netra_sim.mission_manager import Mission


def test_invalid_position_during_arming(cfg):
    m=Mission(cfg);m.state='VERIFY_ARMED';m.started=0
    out=m.tick(1,dict(fresh=True,valid=False,ready=True,offboard=True,armed=False))
    assert m.aborting and out['command']=='LAND'


def test_no_false_landing_complete(cfg):
    m=Mission(cfg);m.state='VERIFY_LANDED';m.started=0
    out=m.tick(2,dict(fresh=True,landed=True,armed=True))
    assert out['state']=='VERIFY_LANDED'


def test_no_stale_second_observation(cfg):
    m=Mission(cfg);m.active={'id':'x','observation_id':'x:1'};m.arrived_at=10
    m.observe(dict(id='x',observation_id='x:2',timestamp=9,priority='P1',**{'class':'person'},local_position=[0,0,0]))
    assert not m.reobserved
