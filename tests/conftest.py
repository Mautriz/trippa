import pytest

import tests.sample_features as sample_features
from trippa import Trippa


@pytest.fixture
def figo() -> Trippa:
    figo_store = Trippa.from_modules([sample_features])
    return figo_store
