import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME = "SilRok AI server"
    PROJECT_VERSION = "0.1.0"

    THREAD_MAX_WORKERS = 8

    MODEL_SAMPLE_RATE = 16000  # 16kHz
    MIN_AUDIO_DURATION = 3 * MODEL_SAMPLE_RATE  # 3 seconds

    REDIS_LIST_TTL = 3600  # 1 hour

    HF_TOKEN = os.getenv("HF_TOKEN", None)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", None)

    DIARIZATION_MAX_REFER = 20

    SOCKET_UC_MAX_BUFFER = 20
    SOCKET_UC_MAX_CONNECTIONS = 1

    # Multi processing
    NUM_CONSUMERS = 4
    MAX_QUEUE_SIZE = 100
    MAX_STORAGE_SIZE = 1000

    MAX_CACHE_SIZE = 3_000

