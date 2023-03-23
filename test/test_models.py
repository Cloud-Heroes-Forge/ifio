import pytest
from utils import FioOptimizer, FioBase

# region test models

@pytest.fixture
def empty_fio_base():
    return FioBase()

# endregion test models
@pytest
def test_fio_base():
    fio_base = empty_fio_base()
    assert fio_base.iops_latency_ratio == 0
    assert fio_base.read_iops == 0
    assert fio_base.read_throughput == 0
    assert fio_base.read_latency == 0

@pytest
def test_fio_summarize():
    fio_base = empty_fio_base()
    fio_base.read_iops = 100
    fio_base.read_latency = 100
    fio_base.summarize()
    assert fio_base.iops_latency_ratio == 1

def test_fio_optimizer():
    fio_optimizer = FioOptimizer()
    fio_optimizer.find_optimal_iodepth()
    