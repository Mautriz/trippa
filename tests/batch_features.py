import pandas as pd

from figo.batch_feature import batch_feature, batch_row_feature


@batch_feature()
def uuids() -> pd.Series:
    ...


@batch_feature()
def other_feature(uuids: pd.Series) -> pd.Series:
    return uuids + uuids


@batch_row_feature()
def other_row_feature(uuids: str) -> str:
    return f"roberto {uuids}"
