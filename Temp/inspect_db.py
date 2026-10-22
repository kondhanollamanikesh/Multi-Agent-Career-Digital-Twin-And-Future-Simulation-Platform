"""Inspect stored Career Twins to see the exact data shape the frontend receives."""
import json
import os
import sys


_BACKEND = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "Backend")
)

sys.path.insert(0, _BACKEND)


from database import career_twins_collection, auth_users_collection


def main():

    docs = list(career_twins_collection.find({}))

    print(f"career_twins: {len(docs)}")

    for doc in docs:

        if doc.get("_id"):
            doc["_id"] = str(doc["_id"])

        state = doc.get("career_state") or {}

        jobs = doc.get("job_opportunities") or []

        gaps = state.get("prioritized_gaps") or []

        print(
            f'user={doc.get("user_id", "?"):16} '
            f'ready={state.get("readiness_score")} '
            f'market={state.get("market_alignment")} '
            f'req={state.get("total_required")} '
            f'miss={state.get("total_missing")} '
            f'gaps={len(gaps)} '
            f'jobs={len(jobs)} '
            f'has_rb={state.get("readiness_breakdown") is not None} '
            f'has_mb={state.get("market_alignment_breakdown") is not None} '
            f'twin={doc.get("profile", {}).get("target_role")}'
        )

    # The registered user's own twin.

    auth = dict(auth_users_collection.find_one({})) if auth_users_collection.find_one({}) else None

    if auth:

        auth["_id"] = str(auth["_id"])

        mine = career_twins_collection.find_one({"user_id": auth["_id"]}, {"_id": 0})

        print()
        print("=== twin shape for the registered user ===")

        if mine:

            print(json.dumps(mine, indent=2, default=str)[:200])

            state = mine.get("career_state") or {}

            jobs = mine.get("job_opportunities") or []

            print(
                json.dumps(
                    {
                        "profile": mine.get("profile"),
                        "readiness": state.get("readiness_score"),
                        "market": state.get("market_alignment"),
                        "readiness_breakdown": state.get("readiness_breakdown"),
                        "market_breakdown": state.get("market_alignment_breakdown"),
                        "gaps_count": len(state.get("prioritized_gaps") or []),
                        "jobs_count": len(jobs),
                        "first_job": jobs[0] if jobs else None,
                    },
                    indent=2,
                    default=str,
                )[:3000]
            )

        else:

            print("NO twin for the registered user.")

    print()
    print("=== grading keys across twins ===")

    for doc in docs:

        state = doc.get("career_state") or {}

        if doc.get("user_id"):
            print(f'uid={doc["user_id"][:12]} keys={sorted(state.keys())}')


if __name__ == "__main__":

    main()
