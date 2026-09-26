import ast,json,xml.etree.ElementTree as E
from pathlib import Path
import pytest
from vayu_netra_sim.perception_interface import validate
from vayu_netra_sim.simulated_perception import SimulatedPerception
from vayu_netra_sim.report_generator import Recorder
from vayu_netra_sim.search_planner import plan
P=Path(__file__).resolve().parents[1]


def test_imports():
    import vayu_netra_sim
    assert vayu_netra_sim.__version__=='1.0.0'


def test_message_format(cfg):
    o=SimulatedPerception(cfg).observe([-10,-9,12],3)[0]
    assert validate(o)['source']=='SIMULATED_PERCEPTION'
    assert o['inference_ms'] is None
    o['confidence']=2
    with pytest.raises(ValueError):validate(o)


def test_report(cfg,tmp_path):
    r=Recorder(cfg);r.pose(1,[0,0,0]);r.pose(3,[3,4,0]);r.save(tmp_path)
    data=json.loads((tmp_path/'mission_report.json').read_text())
    assert data['distance_m']==5
    assert (tmp_path/'mission_report.html').is_file()
    assert json.loads((tmp_path/'incidents.geojson').read_text())['type']=='FeatureCollection'


def test_source_and_launch_parse():
    for p in P.rglob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
    for p in P.rglob('*.sdf'):E.parse(p)
    E.parse(P/'package.xml')


def test_restricted_zone_rejected(cfg):
    with pytest.raises(ValueError):plan(cfg['mission'],[[-15,15,-11,11]])


def test_bridge_and_model_contract():
    bridge=json.loads((P/'config/bridge.yaml').read_text())
    assert {b['ros_topic_name'] for b in bridge}=={'/clock','/vayu/camera/image','/vayu/camera/depth_image','/vayu/camera/camera_info'}
    model=E.parse(P/'models/vayu_netra/model.sdf')
    assert model.find('.//sensor/topic').text=='/vayu/camera'


def test_ros_launch_instantiates_when_available():
    pytest.importorskip('launch')
    pytest.importorskip('launch_ros')
    import runpy
    namespace=runpy.run_path(str(P/'launch/sar.launch.py'))
    assert namespace['generate_launch_description']() is not None
