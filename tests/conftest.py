import pytest

import tests.sample_features as sample_features
from trippa import Trippa


@pytest.fixture
def trippa() -> Trippa:
    trippa_store = Trippa.from_modules([sample_features])
    return trippa_store
