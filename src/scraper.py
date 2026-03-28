from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://github.com"
TRENDING_PATH = "/trending"
VALID_SINCE = {"daily", "weekly", "monthly"}


@dataclass(slots=True)
class TrendingRepo:
    rank: int
    name: str
    url: str
    description: str
    language: str
    stars_total: int
    forks: int
    stars_today: int


def fetch_trending(
    language: str = "",
    since: str = "daily",
    top_n: int = 10,
) -> list[TrendingRepo]:
    if since not in VALID_SINCE:
        raise ValueError(f"Unsupported since value: {since}")
    if top_n <= 0:
        return []

    language_slug = language.strip().strip("/")
    path = f"{TRENDING_PATH}/{language_slug}" if language_slug else TRENDING_PATH
    url = urljoin(BASE_URL, path)
    response = requests.get(
        url,
        params={"since": since},
        headers={"Accept-Language": "en-US"},
        timeout=30,
    )
    response.raise_for_status()
    return _parse_trending_page(response.text, top_n=top_n)


def _parse_trending_page(html: str, top_n: int) -> list[TrendingRepo]:
    if top_n <= 0:
        return []

    soup = BeautifulSoup(html, "html.parser")
    repos: list[TrendingRepo] = []

    for rank, article in enumerate(soup.select("article.Box-row"), start=1):
        if len(repos) >= top_n:
            break

        title_link = article.select_one("h2 a")
        if title_link is None:
            continue

        href = title_link.get("href", "").strip()
        name = _normalize_repo_name(title_link.get_text(" ", strip=True))
        description = _clean_text(article.select_one("p"))
        language = _clean_text(article.select_one('[itemprop="programmingLanguage"]'))
        stars_total, forks = _extract_social_counts(article)
        stars_today = _extract_stars_today(article)

        repos.append(
            TrendingRepo(
                rank=rank,
                name=name,
                url=urljoin(BASE_URL, href),
                description=description,
                language=language,
                stars_total=stars_total,
                forks=forks,
                stars_today=stars_today,
            )
        )

    return repos


def format_markdown(
    repos: list[TrendingRepo],
    date_str: str,
    language: str = "",
) -> str:
    title = f"## GitHub Trending - {date_str}"
    if language:
        title = f"{title} ({language})"

    lines = [
        title,
        "",
        "| # | Repository | Stars | Today | Language | Description |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]

    for repo in repos:
        description = _escape_markdown(_truncate(repo.description, 80))
        language_value = _escape_markdown(repo.language or "-")
        repo_name = _escape_markdown(repo.name)
        lines.append(
            f"| {repo.rank} | [{repo_name}]({repo.url}) | {repo.stars_total:,} | "
            f"{repo.stars_today:,} | {language_value} | {description} |"
        )

    return "\n".join(lines)


def format_text(
    repos: list[TrendingRepo],
    date_str: str,
    language: str = "",
) -> str:
    header = f"GitHub Trending - {date_str}"
    if language:
        header = f"{header} ({language})"

    lines = [header]
    for repo in repos:
        lines.extend(
            [
                f"{repo.rank}. {repo.name}",
                (
                    f"Stars: {repo.stars_total:,} | Today: {repo.stars_today:,} | "
                    f"Language: {repo.language or '-'}"
                ),
                f"Description: {repo.description or '-'}",
                f"URL: {repo.url}",
                "",
            ]
        )

    return "\n".join(lines).rstrip()


def _extract_social_counts(article) -> tuple[int, int]:
    muted_links = article.select("a.Link--muted")
    stars_total = _parse_count(muted_links[0].get_text(strip=True)) if muted_links else 0
    forks = _parse_count(muted_links[1].get_text(strip=True)) if len(muted_links) > 1 else 0
    return stars_total, forks


def _extract_stars_today(article) -> int:
    stars_today_node = article.select_one("span.d-inline-block.float-sm-right")
    return _parse_count(stars_today_node.get_text(" ", strip=True)) if stars_today_node else 0


def _clean_text(node) -> str:
    if node is None:
        return ""
    return " ".join(node.get_text(" ", strip=True).split())


def _normalize_repo_name(raw_name: str) -> str:
    normalized = " ".join(raw_name.split())
    return normalized.replace(" / ", "/").replace(" /", "/").replace("/ ", "/")


def _parse_count(text: str) -> int:
    digits = "".join(char for char in text if char.isdigit())
    return int(digits) if digits else 0


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3].rstrip()}..."


def _escape_markdown(text: str) -> str:
    return text.replace("|", "\\|")
