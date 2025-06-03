import io
import math
import re
import tempfile
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
import subprocess


def camel_to_snake(name: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def compress_to_opus(bytes: bytes):
    process = subprocess.Popen(
        ["ffmpeg", "-i", "pipe:0", "-c:a", "libopus", "-f", "opus", "pipe:1"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,  # subprocess.DEVNULL 하면 속도 조금 더 빨라짐
    )

    out, err = process.communicate(input=bytes)
    return out, err


def mp4_bytes_to_ndarray(mp4_bytes: bytes, sr: int = 16000) -> np.ndarray:
    with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp_in:
        tmp_in.write(mp4_bytes)
        tmp_in.flush()

        process = subprocess.Popen(
            [
                "ffmpeg",
                "-i",
                tmp_in.name,  # ← 파일 기반 입력
                "-f",
                "f32le",  # 출력 포맷: float32 PCM
                "-acodec",
                "pcm_f32le",  # codec: float32 PCM
                "-ac",
                "1",  # mono
                "-ar",
                str(sr),  # sample rate
                "pipe:1",  # 출력: stdout
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        out, _ = process.communicate()
        return np.frombuffer(out, dtype=np.float32)


def ndarray_to_mp4_bytes(audio: np.ndarray, sr: int = 16000) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp_out:
        process = subprocess.Popen(
            [
                "ffmpeg",
                "-f",
                "f32le",
                "-ac",
                "1",
                "-ar",
                str(sr),
                "-i",
                "pipe:0",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-y",  # overwrite
                tmp_out.name,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        in_bytes = audio.astype(np.float32).tobytes()
        process.communicate(input=in_bytes)
        tmp_out.seek(0)
        return tmp_out.read()


def decompress_from_opus(bytes: bytes):
    process = subprocess.Popen(
        ["ffmpeg", "-i", "pipe:0", "-f", "wav", "pipe:1"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = process.communicate(input=bytes)
    return out, err


def bytes_to_np(bt: bytes, sample_rate: int) -> np.ndarray:
    with io.BytesIO(bt) as buffer:
        audio, sr = sf.read(buffer, dtype="float32")
    if sr != sample_rate:
        audio = resample_poly(audio, sample_rate, sr)
    return audio


def np_to_wav(audio: np.ndarray, sample_rate: int) -> bytes:
    buffer = io.BytesIO()
    sf.write(buffer, audio, sample_rate, format="wav")
    return buffer.getvalue()


def update_mean_std(
    old_mean: float,
    old_std: float,
    old_count: int,
    new_mean: float,
    new_std: float,
    new_count: int,
) -> tuple[float, float]:
    if old_count == 0:
        return new_mean, new_std
    if new_count == 0:
        return old_mean, old_std

    total_count = old_count + new_count
    updated_mean = (old_mean * old_count + new_mean * new_count) / total_count

    updated_std = math.sqrt(
        (
            old_count * (old_std**2 + (old_mean - updated_mean) ** 2)
            + new_count * (new_std**2 + (new_mean - updated_mean) ** 2)
        )
        / total_count
    )

    return updated_mean, updated_std
