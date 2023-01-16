import pytest

import tests.batch_features as batch_features
import tests.sample_features as sample_features
from figo import Figo


@pytest.fixture
def figo() -> Figo:
    figo_store = Figo.from_modules([sample_features, batch_features])
    return figo_store
