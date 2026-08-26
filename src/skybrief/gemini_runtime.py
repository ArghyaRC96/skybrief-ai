import time
from collections.abc import Callable
from typing import TypeVar

from google import genai
from google.genai import types


GEMINI_MODEL = "gemini-3.6-flash"

GEMINI_TIMEOUT_MS = 45_000

GEMINI_MAX_ATTEMPTS = 2

GEMINI_RETRY_DELAY_SECONDS = 1.0


T = TypeVar("T")


def create_gemini_client(
    api_key: str,
):
    """
    Create the shared SkyBrief Gemini client.

    The SDK itself is configured for one attempt only.
    SkyBrief owns retry behavior explicitly through
    run_with_one_retry().
    """

    if not api_key:
        raise ValueError(
            "Gemini API key is required."
        )

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=GEMINI_TIMEOUT_MS,
            retry_options=types.HttpRetryOptions(
                attempts=1,
            ),
        ),
    )


def run_with_one_retry(
    operation: Callable[[], T],
    operation_name: str,
) -> T:
    """
    Run an operation with exactly two total attempts:

    attempt 1
    + one retry

    No additional application-level retries occur.
    """

    errors = []
    last_error = None

    for attempt_number in range(
        1,
        GEMINI_MAX_ATTEMPTS + 1,
    ):

        try:

            return operation()

        except Exception as error:

            last_error = error

            errors.append(
                f"attempt {attempt_number}: "
                f"{error}"
            )

            if (
                attempt_number
                < GEMINI_MAX_ATTEMPTS
            ):

                time.sleep(
                    GEMINI_RETRY_DELAY_SECONDS
                )


    error_summary = " | ".join(
        errors
    )

    raise RuntimeError(
        f"{operation_name} failed after "
        f"{GEMINI_MAX_ATTEMPTS} attempts. "
        f"{error_summary}"
    ) from last_error