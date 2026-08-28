"""Build the checked-in Jekyll archive from the original CSV snapshot."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

INTERNAL_POST_RE = re.compile(
    r"(?:(?:https?:)?//(?:www\.)?ilpedante\.info/+(?:ilpedante/)?post/|"
    r"(?<![A-Za-z0-9./])/(?:ilpedante/)?post/)"
    r"(?P<slug>[a-zA-Z0-9_-]+)(?:/)?(?P<fragment>#[\w:.-]+)?"
)
MEDIA_URL_RE = re.compile(
    r"(?:(?:https?:)?//(?:www\.)?ilpedante\.info)?"
    r"(?:\.\.)?(?P<path>/(?:files|assets)/[^\s\"'<>\)]+)"
)


@dataclass(frozen=True)
class Post:
    """A normalized row from the source snapshot."""

    slug: str
    title: str
    author: str
    date: datetime
    markdown: str


def slug_from_url(url: str) -> str:
    """Preserve the final path component used by the original blog."""
    return urlparse(url).path.rstrip("/").rsplit("/", maxsplit=1)[-1]


def read_posts(source: Path) -> list[Post]:
    """Read posts from the compressed, original CSV export."""
    csv.field_size_limit(sys.maxsize)
    with gzip.open(source, mode="rt", encoding="utf-8", newline="") as stream:
        rows = csv.DictReader(stream)
        posts = [
            Post(
                slug=slug_from_url(row["url"]),
                title=row["title"],
                author=row["author"],
                date=datetime.fromisoformat(row["date"]),
                markdown=row["post_markdown"],
            )
            for row in rows
        ]
    return posts


def local_media_path(url: str) -> str | None:
    """Return the canonical local path for an original media URL."""
    absolute = urljoin("https://ilpedante.info/post/archive", url)
    parsed = urlparse(absolute)
    if parsed.hostname not in {"ilpedante.info", "www.ilpedante.info"}:
        return None
    if not parsed.path.startswith(("/files/", "/assets/")):
        return None
    return parsed.path


def rewrite_internal_links(markdown: str) -> str:
    """Point original-blog post links at Pages under the repository base path."""

    def replace(match: re.Match[str]) -> str:
        fragment = match.group("fragment") or ""
        return f"{{{{ site.baseurl }}}}/post/{match.group('slug')}/{fragment}"

    return INTERNAL_POST_RE.sub(replace, markdown)


def rewrite_media(markdown: str, available: set[str]) -> str:
    """Point recovered media at Pages and annotate unavailable media embeds."""

    def replace_missing_link(match: re.Match[str]) -> str:
        label, original = match.group("label"), match.group("url")
        path = local_media_path(original)
        if path is None or path in available:
            return match.group(0)
        original_url = urljoin("https://ilpedante.info/post/archive", original)
        return f"[{label}]({original_url}) *(media non recuperato; URL originale)*"

    markdown = re.sub(
        r"(?<!!)\[(?P<label>[^]]+)\]\((?P<url>(?:(?:https?:)?//(?:www\.)?"
        r"ilpedante\.info)?(?:\.\.)?/(?:files|assets)/[^)]+)\)",
        replace_missing_link,
        markdown,
    )

    def replace_image(match: re.Match[str]) -> str:
        label, original = match.group("label"), match.group("url")
        path = local_media_path(original)
        if path is None or path in available:
            return match.group(0)
        original_url = urljoin("https://ilpedante.info/post/archive", original)
        return (
            "\n\n> **Nota d'archivio:** media non recuperato: "
            f"[{label or 'URL originale'}]({original_url})\n\n"
        )

    markdown = re.sub(
        r"!\[(?P<label>[^]]*)\]\((?P<url>[^)]+)\)", replace_image, markdown
    )

    def replace_url(match: re.Match[str]) -> str:
        original = match.group(0)
        path = local_media_path(original)
        if path is None or path not in available:
            return original
        return f"{{{{ site.baseurl }}}}{path}"

    return MEDIA_URL_RE.sub(replace_url, markdown)


def front_matter(post: Post) -> str:
    """Create YAML with JSON-quoted strings, which are valid and safe YAML."""
    values = {
        "layout": "post",
        "title": post.title,
        "author": post.author,
        "date": post.date.isoformat(sep=" "),
        "permalink": f"/post/{post.slug}/",
    }
    lines = [
        "---",
        *(
            f"{key}: {json.dumps(value, ensure_ascii=False)}"
            for key, value in values.items()
        ),
        "---",
    ]
    return "\n".join(lines) + "\n\n"


def generate(
    source: Path,
    output: Path,
    site_root: Path,
) -> list[Path]:
    """Regenerate all Markdown posts, returning their paths."""
    media_directories = (site_root / "assets", site_root / "files")
    available = {
        "/" + path.relative_to(site_root).as_posix()
        for directory in media_directories
        if directory.exists()
        for path in directory.rglob("*")
        if path.is_file()
    }
    output.mkdir(parents=True, exist_ok=True)
    for old_post in output.glob("*.md"):
        old_post.unlink()

    generated = []
    for post in read_posts(source):
        body = rewrite_internal_links(post.markdown)
        body = rewrite_media(body, available).strip()
        destination = output / f"{post.date:%Y-%m-%d}-{post.slug}.md"
        content = (
            front_matter(post) + body + "\n"
            if body
            else front_matter(post).rstrip() + "\n"
        )
        destination.write_text(content, encoding="utf-8")
        generated.append(destination)
    return generated


def main() -> None:
    """Run the deterministic snapshot-to-Jekyll conversion."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("_posts/posts.csv.gz"))
    parser.add_argument("--output", type=Path, default=Path("_posts"))
    parser.add_argument("--site-root", type=Path, default=Path("."))
    args = parser.parse_args()
    generated = generate(args.source, args.output, args.site_root)
    print(f"Generated {len(generated)} posts")


if __name__ == "__main__":
    main()
