import pytest

from figo import Figo
from tests.sample_features import ciao, first, uuid


@pytest.fixture
def figo() -> Figo:
    figo_store = Figo([first, ciao, uuid], {uuid: "uuid_prova"})

    return figo_store


@pytest.mark.asyncio
async def test_figo(
    figo: Figo,
) -> None:
    result = await figo.resolve(ciao)

    assert result == "firstuuid_provaciao"
