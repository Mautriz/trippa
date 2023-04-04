import pytest

from tests.sample_features import ciao, first, missing_input, using_missing_input, uuid
from trippa import Trippa
from trippa.exceptions import MissingInputException
from trippa.results import ResultFailure, ResultSuccess


@pytest.mark.asyncio
async def test_input(
    trippa: Trippa,
) -> None:
    result = await trippa.start().input({uuid: "assurdo"}).resolve(uuid)
    assert result == "assurdo"


@pytest.mark.asyncio
async def test_input_as_string(
    trippa: Trippa,
) -> None:
    result = await trippa.start().input({"uuid": "assurdo"}).resolve(ciao)
    assert result == "firstassurdociao"


@pytest.mark.asyncio
async def test_input_as_feature(
    trippa: Trippa,
) -> None:
    result = await trippa.start().input({uuid: "assurdo"}).resolve(ciao)
    assert result == "firstassurdociao"


@pytest.mark.asyncio
async def test_resolve_many(
    trippa: Trippa,
) -> None:
    result = (
        await trippa.start().input({uuid: "assurdo"}).resolve_many([ciao, uuid, first])
    )

    assert result == {
        ciao: "firstassurdociao",
        first: "firstassurdo",
        uuid: "assurdo",
    }


@pytest.mark.asyncio
async def test_safe_resolve_many(
    trippa: Trippa,
) -> None:
    result = (
        await trippa.start()
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
    trippa: Trippa,
) -> None:
    with pytest.raises(MissingInputException):
        await trippa.start().resolve(ciao)
