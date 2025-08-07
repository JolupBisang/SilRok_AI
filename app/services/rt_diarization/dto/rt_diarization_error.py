class RTDiarizationError:
    def __init__(self, uuid: str, e: Exception):
        self.uuid = uuid
        self.error = e

    def __repr__(self):
        return self.error.__repr__()

    def __str__(self):
        return self.error.__str__()

__all__ = ["RTDiarizationError"]
