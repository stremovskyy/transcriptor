
class CodedError(Exception):
    """Base class for exceptions with error codes."""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(self.message)

    def to_dict(self):
        return {"code": self.code, "error": self.message}


class SilenceError(CodedError):
    """Exception raised for silent audio errors."""
    def __init__(self):
        super().__init__(1001, "Audio appears to be silent - transcription may not be meaningful")
