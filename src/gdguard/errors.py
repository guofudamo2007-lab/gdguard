class GDGuardError(Exception):
    """User-facing error that should not dump a Python traceback by default."""

    def __init__(self, message: str, exit_code: int = 2) -> None:
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code
