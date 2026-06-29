from __future__ import annotations

from app.leetcode.models import Submission

SYSTEM_PROMPT = (
    "You are Leetbit, a technical writing assistant that transforms accepted LeetCode solutions into precise, "
    "concise documentation. Do not invent algorithms, data structures, constraints, or complexity claims. "
    "Infer the solution strictly from the provided code. Respond with valid JSON only."
)


def build_user_prompt(submission: Submission) -> str:
    return (
        f"Problem title: {submission.title}\n"
        f"Problem slug: {submission.slug}\n"
        f"Problem id: {submission.problem_id or 'unknown'}\n"
        f"Difficulty: {submission.difficulty}\n"
        f"Language: {submission.language}\n"
        f"Problem URL: {submission.url}\n\n"
        f"Solution code:\n{submission.code}\n"
    )
