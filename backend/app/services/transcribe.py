import os
import tempfile
import uuid
from typing import Dict, Iterable, List, Optional, Tuple

import requests
from faster_whisper import WhisperModel

from app import repo_transcriptions, repo_segments, repo_audio_files


def _download_http(url: str) -> str:
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    suffix = os.path.splitext(url.split("?")[0].split("#")[0])[-1] or ".bin"
    fd, path = tempfile.mkstemp(prefix="s2x_", suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    except Exception:
        try:
            os.remove(path)
        except OSError:
            pass
        raise
    return path


def _download_local(path_like: str) -> str:
    if not os.path.exists(path_like):
        raise FileNotFoundError(f"No existe el archivo local: {path_like}")
    suffix = os.path.splitext(path_like)[-1] or ".bin"
    fd, tmp_path = tempfile.mkstemp(prefix="s2x_", suffix=suffix)
    with open(path_like, "rb") as src, os.fdopen(fd, "wb") as dst:
        while True:
            chunk = src.read(1024 * 1024)
            if not chunk:
                break
            dst.write(chunk)
    return tmp_path


def download_audio_to_temp(uri: str) -> str:
    if uri.startswith("http://") or uri.startswith("https://"):
        return _download_http(uri)
    return _download_local(uri)


def _format_timestamp_srt(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02}:{mins:02}:{secs:02},{millis:03}"


def _format_timestamp_vtt(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02}:{mins:02}:{secs:02}.{millis:03}"


def build_srt(segments: Iterable[Dict]) -> str:
    lines: List[str] = []
    idx = 1
    for s in segments:
        start_s = s["start_ms"] / 1000.0
        end_s = s["end_ms"] / 1000.0
        lines.append(str(idx))
        lines.append(f"{_format_timestamp_srt(start_s)} --> {_format_timestamp_srt(end_s)}")
        lines.append(s["text"].strip())
        lines.append("")
        idx += 1
    return "\n".join(lines).strip() + "\n"


def build_vtt(segments: Iterable[Dict]) -> str:
    lines: List[str] = ["WEBVTT", ""]
    for s in segments:
        start_s = s["start_ms"] / 1000.0
        end_s = s["end_ms"] / 1000.0
        lines.append(f"{_format_timestamp_vtt(start_s)} --> {_format_timestamp_vtt(end_s)}")
        lines.append(s["text"].strip())
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _load_model() -> WhisperModel:
    model_name = os.getenv("WHISPER_MODEL", "small")
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    return WhisperModel(model_name, device="cpu", compute_type=compute_type)


def _run_whisper(
    audio_path: str,
    language_hint: Optional[str],
    temperature: Optional[float],
    beam_size: Optional[int],
) -> Tuple[List[Dict], str, Optional[float], str]:
    model = _load_model()
    temp_value = 0.0 if temperature is None else float(temperature)
    beam_value = 5 if beam_size is None else int(beam_size)
    segments_iter, info = model.transcribe(
        audio_path,
        language=language_hint,
        temperature=temp_value,
        beam_size=beam_value,
    )
    segments: List[Dict] = []
    text_full_parts: List[str] = []
    for seg in segments_iter:
        text = seg.text or ""
        text_full_parts.append(text.strip())
        segments.append(
            {
                "start_ms": int(seg.start * 1000),
                "end_ms": int(seg.end * 1000),
                "text": text.strip(),
                "confidence": None,
                "speaker_label": None,
            }
        )
    text_full = " ".join([t for t in text_full_parts if t])
    detected_language = getattr(info, "language", None) or (language_hint or "")
    language_probability = getattr(info, "language_probability", None)
    return segments, detected_language, language_probability, text_full


def process_transcription(transcription_id: str) -> None:
    moved = repo_transcriptions.mark_running(transcription_id)
    if not moved:
        return

    if os.getenv("S2X_DISABLE_WHISPER") == "1":
        try:
            repo_transcriptions.mark_succeeded(
                transcription_id,
                language_detected="",
                confidence=None,
                text_full="",
                artifacts={"srt": "", "vtt": "", "num_segments": 0},
            )
        except Exception:
            repo_transcriptions.mark_failed(transcription_id)
            raise
        return

    audio_path: Optional[str] = None
    try:
        t = repo_transcriptions.get_transcription(transcription_id)
        if not t:
            raise RuntimeError("Transcripción no encontrada")

        audio = repo_audio_files.get_audio(t["audio_id"])
        if not audio:
            raise RuntimeError("Archivo de audio no encontrado")

        uri = audio["s3_uri"]
        audio_path = download_audio_to_temp(uri)

        segments, lang, lang_prob, text_full = _run_whisper(
            audio_path=audio_path,
            language_hint=t.get("language_hint"),
            temperature=t.get("temperature"),
            beam_size=t.get("beam_size"),
        )

        if segments:
            repo_segments.bulk_insert_segments(transcription_id, segments)

        srt = build_srt(segments)
        vtt = build_vtt(segments)
        artifacts = {
            "srt": srt,
            "vtt": vtt,
            "num_segments": len(segments),
        }

        repo_transcriptions.mark_succeeded(
            transcription_id,
            language_detected=lang or "",
            confidence=float(lang_prob) if lang_prob is not None else None,
            text_full=text_full,
            artifacts=artifacts,
        )
    except Exception:
        repo_transcriptions.mark_failed(transcription_id)
        raise
    finally:
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except OSError:
                pass

