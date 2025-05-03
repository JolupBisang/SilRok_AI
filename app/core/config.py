import os
from dotenv import load_dotenv

load_dotenv()


class settings:
    PROJECT_NAME = "SilRok AI server"
    PROJECT_VERSION = "0.1.0"

    THREAD_MAX_WORKERS = 8

    MODEL_SAMPLE_RATE = 16000  # 16kHz
    MIN_AUDIO_DURATION = 3 * MODEL_SAMPLE_RATE  # 3 seconds

    REDIS_STR_HOST = "redis_str"
    REDIS_STR_PORT = 6379
    REDIS_STR_DB = 0
    REDIS_STR_DECODE_RESPONSES = True
    REDIS_STR_TTL = 1000
    REDIS_STR_MAX_MEMORY = "10mb"
    REDIS_STR_MAX_MEMORY_POLICY = "noeviction"

    REDIS_BYTE_HOST = "redis_byte"
    REDIS_BYTE_PORT = 6379
    REDIS_BYTE_DB = 0
    REDIS_BYTE_DECODE_RESPONSES = False
    REDIS_BYTE_TTL = 1000
    REDIS_BYTE_MAX_MEMORY = "10mb"
    REDIS_STR_MAX_MEMORY_POLICY = "noeviction"

    REDIS_LIST_TTL = 3600  # 1 hour

    HF_TOKEN = os.getenv("HF_TOKEN", None)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", None)

    DIARIZATION_MAX_REFER = 20

    SOCKET_UC_MAX_BUFFER = 20
    SOCKET_UC_MAX_CONNECTIONS = 1
    SOCKET_UC_MAX_SPEAKS = 5
    SOCKET_UC_MAX_ALIGNED = 5000
