import pytest
from vayu_netra_sim.coordinates import *


def test_axes():
    assert ned_to_enu([2,3,-4])==[3,2,4]
    assert enu_to_ned(ned_to_enu([2,3,-4]))==[2,3,-4]


def test_geolocation():
    origin=[18.5204,73.8567,560]
    assert geodetic([0,0,0],origin)==[origin[1],origin[0],origin[2]]
    assert geodetic([100,0,0],origin)[0]>origin[1]
    assert geodetic([0,100,0],origin)[1]>origin[0]


def test_nadir_depth():
    p=depth_to_world(320,240,10,[400,0,320,0,400,240,0,0,1],[0,0,10.12],[1,0,0,0])
    assert p==pytest.approx([0,0,0])
    assert depth_to_world(0,0,float('nan'),[],[],[]) is None
