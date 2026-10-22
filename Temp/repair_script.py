"""Repair script.js after an accidental duplicate-insert.

The corrupting write transformed original A X B into A X X B, where

  X = text from the first top-level '/* ===' header (DOM ELEMENTS)
      up to the first '// ===' header (EXISTING CODE comment).

Removing the FIRST copy of X restores A X B.
"""

PATH = "script.js"

X_START_SNIFF = "/* ===="

PAGE_SNIPPET = 'const page = document.getElementById("page");'

EXISTING_SNIFF = "// EXISTING CODE"

LOAD_MARKER = "INITIAL PAGE LOAD"


def main():

    with open(PATH, "r", encoding="utf-8") as file:

        corrupted = file.read()

    first = corrupted.find(PAGE_SNIPPET)

    second = corrupted.find(PAGE_SNIPPET, first + 1)

    if second == -1:

        print("No duplication detected - leaving file as is.")

        return

    x_start_first = corrupted.rfind(X_START_SNIFF, 0, first)

    x_start_second = corrupted.rfind(X_START_SNIFF, 0, second)

    existing = corrupted.find(EXISTING_SNIFF, x_start_first)

    assert -1 not in (
        x_start_first,
        x_start_second,
        existing,
    ), "unexpected structure"

    assert (
        x_start_first < x_start_second < existing
    ), f"ordering wrong: {x_start_first} < {x_start_second} < {existing}"

    removed = corrupted[x_start_first:x_start_second]

    stripped = [
        line[:70]
        for line in removed.splitlines()
        if line.strip()
    ]

    print(f"Removing {len(removed)} chars (first copy of X)")

    print("  starts:", stripped[:2])

    print("  ends:", stripped[-2:])

    fixed = corrupted[:x_start_first] + corrupted[x_start_second:]

    assert fixed.count(PAGE_SNIPPET) == 1, "page snippet should be unique"

    assert fixed.count(LOAD_MARKER) == 1, "initial load block must exist once"

    with open(
        PATH,
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        file.write(fixed)

    print(f"Wrote {len(fixed)} chars (corrupted had {len(corrupted)})")


if __name__ == "__main__":

    main()
