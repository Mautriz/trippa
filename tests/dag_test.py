from tests.sample_features import ciao, first, second, uuid
from trippa import Trippa


def test_find_deps(figo: Trippa) -> None:
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
