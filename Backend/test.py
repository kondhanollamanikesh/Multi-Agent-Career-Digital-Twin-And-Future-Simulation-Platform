import sys

sys.stdout.reconfigure(
    encoding="utf-8", errors="replace"
)

from agents.skill_gap_agent import calculate_skill_gap


current_skills = [
    "Python",
    "Machine Learning",
    "Deep Learning",
    "Natural Language Processing",
    "LLMs",
    "LangChain",
    "LangGraph",
    "FastAPI",
    "REST APIs",
    "MongoDB"
]


result = calculate_skill_gap(
    current_skills,
    "AI Engineer"
)


print(result)