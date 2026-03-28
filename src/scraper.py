"""Scrape GitHub Trending page for top repositories."""

import re
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

GITHUB_TRENDING_URL = "https://github.com/trending"


@dataclass
class TrendingRepo:
    rank: int
    name: str  # "owner/repo"
    url: str
    description: str
    language: str
    stars_total: str
    forks: str
    stars_today: str


def fetch_trending(language: str = "", since: str = "daily", top_n: int = 10) -> list[TrendingRepo]:
    """Fetch trending repositories from GitHub.

    Args:
        language: Filter by programming language (e.g. "python", "javascript"). Empty = all.
        since: Time range - "daily", "weekly", or "monthly".
        top_n: Number of repos to return.

    Returns:
        List of TrendingRepo objects.
    """
    params = {}
    if since:
        params["since"] = since

    url = GITHUB_TRENDING_URL
    if language:
        url = f"{url}/{language}"

    resp = requests.get(url, params=params, headers={"Accept-Language": "en-US,en"}, timeout=30)
    resp.raise_for_status()

    return _parse_trending_page(resp.text, top_n)


def _parse_trending_page(html: str, top_n: int) -> list[TrendingRepo]:
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.select("article.Box-row")

    repos = []
    for rank, article in enumerate(articles[:top_n], start=1):
        # Repo name and URL
        h2 = article.select_one("h2 a")
        if not h2:
            continue
        name = re.sub(r"\s+", "", h2.get_text()).strip("/")
        url = urljoin("https://github.com", h2["href"])

        # Description
        p = article.select_one("p")
        description = p.get_text(strip=True) if p else ""

        # Language
        lang_span = article.select_one("[itemprop='programmingLanguage']")
        language = lang_span.get_text(strip=True) if lang_span else ""

        # Stars and forks from the link elements
        links = article.select("a.Link--muted")
        stars_total = links[0].get_text(strip=True) if len(links) > 0 else ""
        forks = links[1].get_text(strip=True) if len(links) > 1 else ""

        # Stars today
        stars_today_span = article.select_one("span.d-inline-block.float-sm-right")
        stars_today = stars_today_span.get_text(strip=True) if stars_today_span else ""

        repos.append(TrendingRepo(
            rank=rank,
            name=name,
            url=url,
            description=description,
            language=language,
            stars_total=stars_total,
            forks=forks,
            stars_today=stars_today,
        ))

    return repos


def format_markdown(repos: list[TrendingRepo], date_str: str, language: str = "") -> str:
    """Format trending repos as a markdown report."""
    lang_label = language.capitalize() if language else "All Languages"
    lines = [
        f"# GitHub Trending Top {len(repos)} - {date_str}",
        f"",
        f"> Language: **{lang_label}** | Since: **daily**",
        "",
        "| # | Repository | Stars | Today | Language | Description |",
        "|---|-----------|-------|-------|----------|-------------|",
    ]

    for repo in repos:
        desc = repo.description[:80] + "..." if len(repo.description) > 80 else repo.description
        lines.append(
            f"| {repo.rank} "
            f"| [{repo.name}]({repo.url}) "
            f"| {repo.stars_total} "
            f"| {repo.stars_today} "
            f"| {repo.language} "
            f"| {desc} |"
        )

    lines.append("")
    return "\n".join(lines)


def format_text(repos: list[TrendingRepo], date_str: str, language: str = "") -> str:
    """Format trending repos as plain text for notifications."""
    lang_label = language.capitalize() if language else "All Languages"
    lines = [
        f"GitHub Trending Top {len(repos)} - {date_str}",
        f"Language: {lang_label} | Since: daily",
        "=" * 50,
    ]

    for repo in repos:
        desc = repo.description[:60] + "..." if len(repo.description) > 60 else repo.description
        lines.append(f"\n#{repo.rank} {repo.name}")
        lines.append(f"   {repo.stars_total} stars | {repo.stars_today}")
        if repo.language:
            lines.append(f"   Language: {repo.language}")
        if desc:
            lines.append(f"   {desc}")
        lines.append(f"   {repo.url}")

    return "\n".join(lines)
