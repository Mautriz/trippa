import pytest

from figo import Figo
from figo.errors import MissingInputException
from figo.results import ResultFailure, ResultSuccess
from tests.sample_features import ciao, first, missing_input, using_missing_input, uuid


@pytest.mark.asyncio
async def test_input(
    figo: Figo,
) -> None:
    result = await figo.start().input({uuid: "assurdo"}).resolve(uuid)
    assert result == "assurdo"


@pytest.mark.asyncio
async def test_input_as_string(
    figo: Figo,
) -> None:
    result = await figo.start().input({uuid: "assurdo"}).resolve(ciao)
    assert result == "firstassurdociao"


@pytest.mark.asyncio
async def test_input_as_feature(
    figo: Figo,
) -> None:
    result = await figo.start().input({uuid: "assurdo"}).resolve(ciao)
    assert result == "firstassurdociao"


@pytest.mark.asyncio
async def test_resolve_many(
    figo: Figo,
) -> None:
    result = (
        await figo.start().input({uuid: "assurdo"}).resolve_many([ciao, uuid, first])
    )

    assert result == {
        "ciao": "firstassurdociao",
        "first": "firstassurdo",
        "uuid": "assurdo",
    }


@pytest.mark.asyncio
async def test_safe_resolve_many(
    figo: Figo,
) -> None:
    result = (
        await figo.start()
        .input({uuid: "assurdo"})
        .safe_resolve_many([ciao, uuid, first, missing_input, using_missing_input])
    )

    assert result["ciao"] == ResultSuccess("firstassurdociao")
    assert isinstance(result["missing_input"], ResultFailure) and isinstance(
        result["missing_input"].error, MissingInputException
    )
    assert isinstance(result["using_missing_input"], ResultFailure) and isinstance(
        result["using_missing_input"].error, MissingInputException
    )


@pytest.mark.asyncio
async def test_no_input_error(
    figo: Figo,
) -> None:
    with pytest.raises(MissingInputException):
        await figo.start().resolve(ciao)
