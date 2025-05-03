DONE = "done"
ASR = "asr"
ASR_DONE = "asr_done"
DIARIZED = "diarized"
DIARIZED_DONE = "diarized_done"
REFER = "refer"
CONTEXT = "context"
CONTEXT_DONE = "context_done"
METADATA = "metadata"

FLAGS = [
    DONE,
    ASR,
    ASR_DONE,
    DIARIZED,
    DIARIZED_DONE,
    REFER,
    CONTEXT,
    CONTEXT_DONE,
    METADATA,
]

DATA_IS_AUDIO = [ASR, ASR_DONE, DIARIZED, DIARIZED_DONE]
DATA_IS_REFER = [REFER]
DATA_IS_METADATA = [METADATA]
DATA_IS_NOT_EXIST = [
    f for f in FLAGS if f not in [*DATA_IS_AUDIO, *DATA_IS_REFER, *DATA_IS_METADATA]
]
