"""Fast, targeted NVIDIA model probe.

1. Dumps the full /models catalog to stdout.
2. Probes only plausible text-generation models, each with a
   short timeout, and prints progress as it goes.
"""

import os
import json
import sys

import requests
from dotenv import load_dotenv


load_dotenv(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        ".env",
    )
)

API_KEY = os.getenv("NVIDIA_API_KEY", "")

BASE_URL = "https://integrate.api.nvidia.com/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def out(*parts):

    print(*parts)

    sys.stdout.flush()


def probe(model: str, timeout: int = 25, structured: bool = False) -> str:

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Return JSON with this exact shape: "
                    '{"name": "Ada Lovelace", "skills": ["math"]}'
                ),
            }
        ],
        "max_tokens": 200,
        "temperature": 0,
    }

    if structured:

        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "Probe",
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "skills": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["name", "skills"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        }

    try:

        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=HEADERS,
            json=payload,
            timeout=timeout,
        )

        if response.status_code != 200:
            return f"FAIL {response.status_code}: {response.text[:110]}"

        body = response.json()

        text = (
            body.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        if structured:

            stripped = text.strip()

            looks_json = stripped.startswith("{")

            return (
                f"OK-STRUCTURED ({'json' if looks_json else text[:40]!r})"
            )

        return f"OK ({text.strip()[:24]!r})"

    except requests.exceptions.Timeout:

        return "FAIL timeout"

    except Exception as exc:

        return f"FAIL {type(exc).__name__}: {str(exc)[:90]}"


def main():

    response = requests.get(
        f"{BASE_URL}/models",
        headers=HEADERS,
        timeout=30,
    )

    if response.status_code != 200:

        out("models list failed:", response.status_code)

        return

    names = [
        m.get("id", "")
        for m in response.json().get("data", [])
        if m.get("id")
    ]

    out(f"CATALOG ({len(names)}):")

    for name in names:
        out("  ", name)

    out()

    # Only text-generation style entries. Exclude embeds,
    # safety guards, reward models, parsing/vision tools.

    skip_words = [
        "embed",
        "guard",
        "reward",
        "content-safety",
        "parse",
        "ocr",
        "rerank",
        "vlm",
    ]

    candidates = [
        n
        for n in names
        if not any(word in n for word in skip_words)
    ]

    out(f"PROBING {len(candidates)} CANDIDATES:")

    usable = []

    for name in candidates:

        result = probe(name)

        out(f"  {name:60} {result[:120]}")

        if result.startswith("OK"):

            usable.append(name)

    out()

    out("USABLE (plain chat):", json.dumps(usable))

    out()

    # Confirm structured output works on the winners - the
    # resume pipeline depends on response_format json_schema.

    out("STRUCTURED OUTPUT CHECK:")

    for name in usable[:8]:

        result = probe(name, structured=True)

        out(f"  {name:60} {result[:120]}")


if __name__ == "__main__":

    main()
