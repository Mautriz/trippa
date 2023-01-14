class MissingInputException(Exception):
    def __init__(self, input_name: str) -> None:
        super().__init__(
            f"Feature '{input_name}' missing, try adding it to the inputs."
        )


class UnknownFeature(Exception):
    def __init__(self, dependency_of: str, missing_feature: str) -> None:
        super().__init__(
            f"Feature '{missing_feature}' (dependency of '{dependency_of}'), is not defined."
        )
