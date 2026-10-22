"""Diagnose the NVIDIA LLM 404: reproduce it, then find valid model names."""

import os
import json

import requests
from dotenv import load_dotenv


# database.py loads dotenv relative to Backend, so replicate that here.

load_dotenv(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        ".env",
    )
)

API_KEY = os.getenv("NVIDIA_API_KEY", "")

BASE_URL = "https://integrate.api.nvidia.com/v1"

MODEL = os.getenv("NVIDIA_LLM_MODEL", "")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def check_model(model: str) -> str:

    try:

        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=HEADERS,
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Reply with the single word OK.",
                    }
                ],
                "max_tokens": 8,
                "temperature": 0,
            },
            timeout=60,
        )

        if response.status_code == 200:

            body = response.json()

            text = (
                body.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            return f"OK ({text.strip()[:20]!r})"

        return f"HTTP {response.status_code}: {response.text[:180]}"

    except Exception as exc:

        return f"ERROR: {exc}"


def main():

    print("Configured model:", MODEL)

    print("Configured model check:", check_model(MODEL))

    print()

    # List which models this key can actually see.

    names = []

    try:

        response = requests.get(
            f"{BASE_URL}/models",
            headers=HEADERS,
            timeout=60,
        )

        print("models list HTTP:", response.status_code)

        if response.status_code == 200:

            models = response.json().get("data", [])

            names = [
                m.get("id", "")
                for m in models
            ]

            print(f"total models: {len(names)}")

            for name in names:

                print("  ", name)

        else:

            print(response.text[:300])

    except Exception as exc:

        print("models list failed:", exc)

    print()

    # Probe every non-routing-looking model that might still
    # be invocable with this key.

    usable = []

    for name in names:

        if not name:
            continue

        result = check_model(name)

        print(f"{name:55} {result[:70]}")

        if result.startswith("OK"):
            usable.append(name)

    print()
    print("INVOCABLE WITH THIS KEY:")
    print(json.dumps(usable, indent=2))


if __name__ == "__main__":

    main()
