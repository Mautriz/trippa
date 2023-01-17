from figo import Figo
from tests.sample_features import ciao, first, second, uuid


def test_find_deps(figo: Figo):
    expected = [
        uuid.name,
    ]
    deps = [f.name for f in figo.find_deps(first)]
    assert deps == expected

    expected = [
        ciao.name,
        first.name,
        uuid.name,
    ]
    deps = [f.name for f in figo.find_deps(second)]
    assert deps == expected
