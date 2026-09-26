import pytest
from vayu_netra_sim.triage_engine import assess
from vayu_netra_sim.simulated_perception import SimulatedPerception


def observation(cfg):return SimulatedPerception(cfg).observe([-10,-9,12],3)[0]


@pytest.mark.parametrize('risk,priority',[(.9,'P0'),(.7,'P1'),(.5,'P2'),(.3,'P3'),(.1,'P4'),(.85,'P0'),(.65,'P1')])
def test_thresholds(cfg,risk,priority):
    o=observation(cfg);o['context']={k:risk for k in cfg['triage']['weights']}
    assert assess(o,cfg)['priority']==priority


def test_confidence_not_urgency(cfg):
    o=observation(cfg);first=assess(o,cfg)['risk_score'];o['confidence']=.2
    assert assess(o,cfg)['risk_score']==first


def test_unknown_context_not_low_priority(cfg):
    o=observation(cfg);o['context']=None
    assert assess(o,cfg)['priority']=='UNASSESSED'
