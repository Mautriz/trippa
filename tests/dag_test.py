from figo import Figo
from tests.sample_features import ciao, first, second, uuid


def test_find_deps(figo: Figo) -> None:
    expected = set([uuid.name])
    deps = set(f.name for f in figo.find_deps(first))
    assert deps == expected

    expected = set(
        [
            ciao.name,
            first.name,
            uuid.name,
        ]
    )
    deps = set(f.name for f in figo.find_deps(second))
    assert deps == expected
