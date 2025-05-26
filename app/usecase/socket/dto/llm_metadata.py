from dataclasses import dataclass, field

from .metadata import Metadata


@dataclass(slots=True)
class LLMMetadata:
    metadata: Metadata

    @property
    def flag(self):
        return self.metadata.flag

    @property
    def group_id(self):
        return self.metadata.group_id

    @property
    def user_id(self):
        return self.metadata.header["user_id"]

    @property
    def agenda(self):
        return self.metadata.header.get("agenda", None)

    @property
    def num_people(self):
        return self.metadata.header.get("num_people", None)

    @property
    def meeting_topic(self):
        return self.metadata.header.get("meeting_topic", None)

    @staticmethod
    def from_metadata(metadata: Metadata):
        return LLMMetadata(
            metadata  = metadata,
        )
