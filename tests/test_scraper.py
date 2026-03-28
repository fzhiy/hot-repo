from unittest.mock import MagicMock, patch

from src.scraper import (
    _parse_trending_page,
    fetch_trending,
    format_markdown,
    format_text,
)


FIXTURE_HTML = """
<html>
  <body>
    <article class="Box-row">
      <h2>
        <a href="/psf/requests">
          psf / requests
        </a>
      </h2>
      <p>
        A simple, yet elegant HTTP library for Python with a description that is intentionally
        long enough to exercise truncation behaviour in markdown output formatting.
      </p>
      <div>
        <span itemprop="programmingLanguage">Python</span>
        <a class="Link--muted" href="/psf/requests/stargazers">52,341</a>
        <a class="Link--muted" href="/psf/requests/forks">9,412</a>
        <span class="d-inline-block float-sm-right">312 stars today</span>
      </div>
    </article>
    <article class="Box-row">
      <h2>
        <a href="/pallets/flask">
          pallets / flask
        </a>
      </h2>
      <p>A lightweight WSGI web application framework.</p>
      <div>
        <span itemprop="programmingLanguage">Python</span>
        <a class="Link--muted" href="/pallets/flask/stargazers">67,890</a>
        <a class="Link--muted" href="/pallets/flask/forks">16,543</a>
        <span class="d-inline-block float-sm-right">128 stars today</span>
      </div>
    </article>
    <article class="Box-row">
      <h2>
        <a href="/astral-sh/uv">
          astral-sh / uv
        </a>
      </h2>
      <p>An extremely fast Python package and project manager.</p>
      <div>
        <span itemprop="programmingLanguage">Rust</span>
        <a class="Link--muted" href="/astral-sh/uv/stargazers">21,111</a>
        <a class="Link--muted" href="/astral-sh/uv/forks">654</a>
        <span class="d-inline-block float-sm-right">999 stars today</span>
      </div>
    </article>
  </body>
</html>
"""


def test_parse_trending_page_returns_repositories() -> None:
    repos = _parse_trending_page(FIXTURE_HTML, top_n=2)

    assert len(repos) == 2
    assert repos[0].rank == 1
    assert repos[0].name == "psf/requests"
    assert repos[0].url == "https://github.com/psf/requests"
    assert repos[0].language == "Python"
    assert repos[0].stars_total == 52341
    assert repos[0].forks == 9412
    assert repos[0].stars_today == 312
    assert repos[1].rank == 2
    assert repos[1].name == "pallets/flask"


def test_format_markdown_outputs_expected_table() -> None:
    repos = _parse_trending_page(FIXTURE_HTML, top_n=2)

    output = format_markdown(repos, date_str="2026-03-28", language="python")

    assert output.startswith("## GitHub Trending - 2026-03-28 (python)")
    assert "| # | Repository | Stars | Today | Language | Description |" in output
    assert "| 1 | [psf/requests](https://github.com/psf/requests) | 52,341 | 312 | Python |" in output
    assert "..." in output


def test_format_text_outputs_expected_sections() -> None:
    repos = _parse_trending_page(FIXTURE_HTML, top_n=2)

    output = format_text(repos, date_str="2026-03-28", language="python")

    assert output.startswith("GitHub Trending - 2026-03-28 (python)")
    assert "1. psf/requests" in output
    assert "Stars: 52,341 | Today: 312 | Language: Python" in output
    assert "Description: A lightweight WSGI web application framework." in output
    assert "URL: https://github.com/pallets/flask" in output


@patch("src.scraper.requests.get")
def test_fetch_trending_uses_requests_get(mock_get: MagicMock) -> None:
    response = MagicMock()
    response.text = FIXTURE_HTML
    response.raise_for_status = MagicMock()
    mock_get.return_value = response

    repos = fetch_trending(language="python", since="weekly", top_n=1)

    assert len(repos) == 1
    assert repos[0].name == "psf/requests"
    mock_get.assert_called_once_with(
        "https://github.com/trending/python",
        params={"since": "weekly"},
        headers={"Accept-Language": "en-US"},
        timeout=30,
    )
    response.raise_for_status.assert_called_once_with()
