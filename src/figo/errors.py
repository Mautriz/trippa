class MissingInputException(Exception):
    def __init__(self, input_name: str) -> None:
        super().__init__(
            f"Feature '{input_name}' missing, try adding it to the inputs."
        )
