from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from xtb_lab_harness.config.env import load_project_env

CheckStatus = Literal["ok", "missing_key", "missing_package", "auth_error", "quota_exceeded", "unavailable", "error"]


@dataclass(frozen=True)
class GeminiHealthResult:
    status: CheckStatus
    message: str
    model: str | None = None
    key_source: str | None = None
    response_preview: str | None = None
    models_tried: tuple[str, ...] = ()


def _resolve_api_key() -> tuple[str | None, str | None]:
    if key := os.environ.get("GEMINI_API_KEY"):
        return key, "GEMINI_API_KEY"
    if key := os.environ.get("GOOGLE_API_KEY"):
        return key, "GOOGLE_API_KEY"
    return None, None


def _candidate_models(preferred: str | None) -> list[str]:
    seen: set[str] = set()
    models: list[str] = []
    for name in (preferred, "gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash"):
        if name and name not in seen:
            seen.add(name)
            models.append(name)
    return models


def _classify_error(exc: Exception) -> tuple[CheckStatus, str]:
    name = type(exc).__name__
    text = str(exc)

    if "ClientError" in name or "401" in text or "403" in text or "API key not valid" in text:
        return "auth_error", "API 키가 유효하지 않습니다. GEMINI_API_KEY 값을 확인하세요."
    if "429" in text or "RESOURCE_EXHAUSTED" in text or "quota" in text.lower():
        return (
            "quota_exceeded",
            "API 키는 인식되지만 할당량(quota)이 초과되었습니다. "
            "Google AI Studio 사용량·요금제를 확인하거나 잠시 후 다시 시도하세요.",
        )
    if "503" in text or "UNAVAILABLE" in text:
        return (
            "unavailable",
            "API 키는 유효하지만 모델이 일시적으로 과부하 상태입니다. "
            "잠시 후 다시 시도하거나 GEMINI_MODEL을 변경하세요.",
        )
    return "error", f"Gemini 호출 실패: {text[:300]}"


def check_gemini(*, model: str | None = None) -> GeminiHealthResult:
    """Verify Gemini API key, package, and a minimal generate_content call."""
    load_project_env()

    try:
        from google import genai
        from google.genai import errors as genai_errors
    except ImportError:
        return GeminiHealthResult(
            status="missing_package",
            message="google-genai 패키지가 없습니다. `uv sync --extra llm` 실행 후 다시 시도하세요.",
        )

    api_key, key_source = _resolve_api_key()
    if not api_key:
        return GeminiHealthResult(
            status="missing_key",
            message=(
                "GEMINI_API_KEY 또는 GOOGLE_API_KEY가 설정되지 않았습니다. "
                ".env.local 파일에 키를 추가하세요."
            ),
        )

    preferred = model or os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    models = _candidate_models(preferred)
    client = genai.Client(api_key=api_key)
    last_result: GeminiHealthResult | None = None

    for candidate_model in models:
        try:
            response = client.models.generate_content(
                model=candidate_model,
                contents='Reply with exactly the word "OK" and nothing else.',
            )
            preview = (response.text or "").strip()
            if not preview:
                last_result = GeminiHealthResult(
                    status="error",
                    message=f"모델 `{candidate_model}` 응답이 비어 있습니다.",
                    model=candidate_model,
                    key_source=key_source,
                    models_tried=tuple(models),
                )
                continue
            return GeminiHealthResult(
                status="ok",
                message="Gemini API 연결 및 generate_content 호출이 정상입니다.",
                model=candidate_model,
                key_source=key_source,
                response_preview=preview[:120],
                models_tried=tuple(models),
            )
        except genai_errors.ClientError as exc:
            status, message = _classify_error(exc)
            last_result = GeminiHealthResult(
                status=status,
                message=f"[{candidate_model}] {message}",
                model=candidate_model,
                key_source=key_source,
                models_tried=tuple(models),
            )
            if status in ("auth_error", "missing_key"):
                return last_result
        except genai_errors.ServerError as exc:
            status, message = _classify_error(exc)
            last_result = GeminiHealthResult(
                status=status,
                message=f"[{candidate_model}] {message}",
                model=candidate_model,
                key_source=key_source,
                models_tried=tuple(models),
            )
        except Exception as exc:
            status, message = _classify_error(exc)
            last_result = GeminiHealthResult(
                status=status,
                message=f"[{candidate_model}] {message}",
                model=candidate_model,
                key_source=key_source,
                models_tried=tuple(models),
            )

    return last_result or GeminiHealthResult(
        status="error",
        message="Gemini API 확인에 실패했습니다.",
        model=preferred,
        key_source=key_source,
        models_tried=tuple(models),
    )


def format_health_report(result: GeminiHealthResult) -> str:
    icon = {
        "ok": "✅",
        "missing_key": "❌",
        "missing_package": "❌",
        "auth_error": "❌",
        "quota_exceeded": "⚠️",
        "unavailable": "⚠️",
        "error": "❌",
    }[result.status]

    lines = [
        f"{icon} Gemini API 상태: {result.status}",
        f"- {result.message}",
    ]
    if result.key_source:
        lines.append(f"- 키 출처: `{result.key_source}`")
    if result.model:
        lines.append(f"- 사용 모델: `{result.model}`")
    if result.models_tried:
        lines.append(f"- 시도한 모델: {', '.join(f'`{m}`' for m in result.models_tried)}")
    if result.response_preview:
        lines.append(f"- 응답 미리보기: {result.response_preview!r}")
    return "\n".join(lines)


def main() -> int:
    result = check_gemini()
    print(format_health_report(result))
    return 0 if result.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
