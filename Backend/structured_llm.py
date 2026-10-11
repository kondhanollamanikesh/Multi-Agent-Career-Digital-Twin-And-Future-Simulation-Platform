# ==========================================
# Structured LLM Helper
# ==========================================
#
# ChatNVIDIA.with_structured_output() tries three request
# formats. The NVIDIA API rejects the last one
# (nvext.guided_json) with HTTP 400 "unknown field
# guided_json", so whenever the two supported formats fail
# (transient 503 overload, truncated or non-JSON output)
# that misleading 400 is the only error the caller sees -
# which is what turned /career-twin into a 500.
#
# StructuredLLM only uses formats the API accepts, retries
# the call before giving up and parses the JSON defensively.

import json

import re

import time


def _extract_json(
    text
):
    """Return the first JSON object found in an LLM response."""

    text = (
        text or ""
    ).strip()

    text = re.sub(
        r"^```[a-zA-Z0-9_-]*",
        "",
        text
    ).strip()

    text = re.sub(
        r"```$",
        "",
        text
    ).strip()

    try:

        return json.loads(
            text
        )

    except ValueError:

        pass

    start = text.find(
        "{"
    )

    end = text.rfind(
        "}"
    )

    if start != -1 and end > start:

        return json.loads(
            text[start:end + 1]
        )

    raise ValueError(
        "LLM response does not contain JSON"
    )


class StructuredLLM:
    """Runs schema-constrained calls against ChatNVIDIA."""

    def __init__(
        self,
        client,
        schema,
        attempts=3,
        delay=2.0
    ):

        self.client = client

        self.schema = schema

        self.attempts = attempts

        self.delay = delay

        json_schema = schema.model_json_schema()

        # Only formats the NVIDIA API accepts.
        # nvext.guided_json always returns HTTP 400.

        self.request_formats = [

            {
                "response_format":
                    {
                        "type":
                            "json_schema",
                        "json_schema":
                            {
                                "name":
                                    schema.__name__,
                                "schema":
                                    json_schema,
                                "strict":
                                    True,
                            },
                    }
            },

            {
                "guided_json":
                    json_schema
            },

        ]

    def invoke(
        self,
        prompt
    ):

        errors = []

        empty_result = None

        for attempt in range(
            1,
            self.attempts + 1
        ):

            for request_format in self.request_formats:

                try:

                    message = self.client.bind(
                        **request_format
                    ).invoke(
                        prompt
                    )

                    data = _extract_json(
                        getattr(
                            message,
                            "content",
                            ""
                        ) or ""
                    )

                    result = self.schema.model_validate(
                        data
                    )

                except Exception as exc:

                    errors.append(
                        f"{type(exc).__name__}: {exc}"
                    )

                    continue

                # An all-empty extraction usually means the
                # model answered without the constrained JSON.
                # Retry, but accept it if nothing better
                # ever comes back.

                if self._is_empty(
                    result
                ):

                    empty_result = result

                    continue

                return result

            if attempt < self.attempts:

                print(
                    f"[StructuredLLM] {self.schema.__name__} "
                    f"attempt {attempt} failed, "
                    "retrying..."
                )

                print(
                    "[StructuredLLM]",
                    errors[-1]
                    if errors
                    else "empty result"
                )

                time.sleep(
                    self.delay * attempt
                )

        if empty_result is not None:

            return empty_result

        raise RuntimeError(
            f"{self.schema.__name__} extraction failed "
            f"after {self.attempts} attempts: "
            + " | ".join(
                errors[-3:]
            )
        )

    @staticmethod
    def _is_empty(
        result
    ):
        """True when no list field of the result holds data."""

        for value in vars(
            result
        ).values():

            if isinstance(
                value,
                list
            ) and value:

                return False

        return True
