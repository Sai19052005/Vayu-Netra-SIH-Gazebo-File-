import sys
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P))
from vayu_netra_sim.configuration import load


@pytest.fixture
def cfg():return load(P/'config/quick.yaml')
