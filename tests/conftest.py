import pytest
from figo import Figo
import tests.sample_features as sample_features
import tests.batch_features as batch_features


@pytest.fixture
def figo() -> Figo:
    figo_store = Figo.from_modules([sample_features, batch_features])
    return figo_store
