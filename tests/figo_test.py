from typing import Any

import pytest

from figo import Figo
from tests.sample_features import ciao


@pytest.fixture
def figo() -> Figo[Any]:
    figo_store = Figo[Any]({})

    return figo_store


@pytest.mark.asyncio
async def test_figo(
    figo: Figo[Any],
) -> None:  # pylint: disable=redefined-outer-name
    result = await figo.resolve(ciao, ("quote", "id"))

    assert result == "first('quote', 'id')first('boh', 'ciaoo')"
