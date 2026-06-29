from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from app.ai.models import AIResponse
from app.leetcode.models import Submission

SUPPORTED_TOPICS = ("Arrays", "Graphs", "DP", "Trees", "Stack", "Queue", "Binary Search")
TOPIC_PATTERNS = {
    "Graphs": ("graph", "bfs", "dfs", "adjacency", "visited", "topological"),
    "DP": ("dp", "memo", "memoization", "tabulation", "dynamic programming"),
    "Trees": ("tree", "trie", "bst", "binary tree", "segment tree", "fenwick"),
    "Stack": ("stack", "monotonic", "parentheses"),
    "Queue": ("queue", "deque", "sliding window"),
    "Binary Search": ("binary search", "bisect", "lower bound", "upper bound"),
}


def classify_topic(submission: Submission, response: AIResponse | None = None) -> str:
    searchable_text = " ".join(
        part
        for part in (
            submission.title,
            submission.slug,
            submission.code,
            submission.difficulty,
            response.summary if response else "",
            response.approach if response else "",
            response.topic if response else "",
        )
        if part
    ).lower()

    for topic in ("Graphs", "DP", "Trees", "Stack", "Queue", "Binary Search"):
        if any(pattern in searchable_text for pattern in TOPIC_PATTERNS[topic]):
            return topic
    return "Arrays"


def build_markdown_filename(submission: Submission) -> str:
    return f"{_slugify(submission.title)}.md"


def render_markdown_document(submission: Submission, response: AIResponse) -> str:
    topic = response.topic.strip() if response.topic.strip() in SUPPORTED_TOPICS else classify_topic(submission, response)
    body = response.markdown.strip()
    if not body:
        body = dedent(
            f"""
            # {submission.title}

            Difficulty

            {submission.difficulty}

            Problem

            {submission.url}

            Topic

            {topic}

            Summary

            {response.summary}

            Approach

            {response.approach}

            Complexity

            Time: {response.time_complexity}

            Space: {response.space_complexity}

            Code

            ```{submission.language.lower()}
            {submission.code}
            ```
            """
        ).strip()
    return body


def _slugify(title: str) -> str:
    return "-".join(part.lower() for part in title.replace("/", " ").split() if part)
