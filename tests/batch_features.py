import pandas as pd

from figo.batch_feature import batch_feature


@batch_feature()
def uuids() -> pd.Series:
    ...


@batch_feature()
def other_feature(uuids: pd.Series) -> pd.Series:
    return uuids + uuids
