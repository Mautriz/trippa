import pytest

from tests.sample_features import ciao, first, missing_input, using_missing_input, uuid
from trippa import Trippa
from trippa.exceptions import MissingInputException
from trippa.results import ResultFailure, ResultSuccess


@pytest.mark.asyncio
async def test_input(
    figo: Trippa,
) -> None:
    result = await figo.start().input({uuid: "assurdo"}).resolve(uuid)
    assert result == "assurdo"


@pytest.mark.asyncio
async def test_input_as_string(
    figo: Trippa,
) -> None:
    result = await figo.start().input({"uuid": "assurdo"}).resolve(ciao)
    assert result == "firstassurdociao"


@pytest.mark.asyncio
async def test_input_as_feature(
    figo: Trippa,
) -> None:
    result = await figo.start().input({uuid: "assurdo"}).resolve(ciao)
    assert result == "firstassurdociao"


@pytest.mark.asyncio
async def test_resolve_many(
    figo: Trippa,
) -> None:
    result = (
        await figo.start().input({uuid: "assurdo"}).resolve_many([ciao, uuid, first])
    )

    assert result == {
        ciao: "firstassurdociao",
        first: "firstassurdo",
        uuid: "assurdo",
    }


@pytest.mark.asyncio
async def test_safe_resolve_many(
    figo: Trippa,
) -> None:
    result = (
        await figo.start()
        .input({uuid: "assurdo"})
        .safe_resolve_many([ciao, uuid, first, missing_input, using_missing_input])
    )

    assert result[ciao] == ResultSuccess("firstassurdociao")
    assert isinstance(res := result[missing_input], ResultFailure) and isinstance(
        res.error, MissingInputException
    )
    assert isinstance(res := result[using_missing_input], ResultFailure) and isinstance(
        res.error, MissingInputException
    )


@pytest.mark.asyncio
async def test_no_input_error(
    figo: Trippa,
) -> None:
    with pytest.raises(MissingInputException):
        await figo.start().resolve(ciao)
