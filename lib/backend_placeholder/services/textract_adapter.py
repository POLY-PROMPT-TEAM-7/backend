from ..models import TextractAdapterResult
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError


def _classify_shell_error(message: str) -> str:
  lowered = message.lower()
  if "not found" in lowered or "no such file" in lowered or "command not found" in lowered:
    return "missing_parser_dependency"
  return "shell_error"


def extract_text(file_path: Path, timeout_seconds: int = 45) -> TextractAdapterResult:
  try:
    import textract  # type: ignore
    from textract import exceptions as textract_exceptions  # type: ignore
  except Exception as exc:
    return TextractAdapterResult(
      text="",
      metadata_status="error",
      error_code="textract_unavailable",
      error_message=str(exc),
    )

  if not file_path.exists() or not file_path.is_file():
    return TextractAdapterResult(
      text="",
      metadata_status="error",
      error_code="missing_file",
      error_message=f"file does not exist: {file_path}",
    )

  try:
    with ThreadPoolExecutor(max_workers=1) as executor:
      future = executor.submit(textract.process, str(file_path))
      raw_bytes = future.result(timeout=timeout_seconds)
    text = raw_bytes.decode("utf-8", errors="replace")
    return TextractAdapterResult(text=text, metadata_status="ok")
  except FutureTimeoutError:
    return TextractAdapterResult(
      text="",
      metadata_status="error",
      error_code="textract_timeout",
      error_message=f"textract timed out after {timeout_seconds}s",
    )
  except textract_exceptions.MissingFileError as exc:
    return TextractAdapterResult(
      text="",
      metadata_status="error",
      error_code="missing_file",
      error_message=str(exc),
    )
  except textract_exceptions.ExtensionNotSupported as exc:
    return TextractAdapterResult(
      text="",
      metadata_status="error",
      error_code="extension_not_supported",
      error_message=str(exc),
    )
  except textract_exceptions.UnknownMethod as exc:
    return TextractAdapterResult(
      text="",
      metadata_status="error",
      error_code="unknown_method",
      error_message=str(exc),
    )
  except textract_exceptions.ShellError as exc:
    message = str(exc)
    return TextractAdapterResult(
      text="",
      metadata_status="error",
      error_code=_classify_shell_error(message),
      error_message=message,
    )
  except Exception as exc:
    return TextractAdapterResult(
      text="",
      metadata_status="error",
      error_code="textract_failed",
      error_message=str(exc),
    )
