"""
Blog Scraper

This script scrapes a blog's main page to gather links to posts and their metadata.
It then fetches the content of each post, converts it to Markdown, and saves the data in a CSV file.

Usage:
python ilpedante_mirror/bulk_download.py [root_url]

- root_url (optional): The root URL of the blog. Default is "http://ilpedante.info/home/loadArticoli".
"""

import sys
from pathlib import Path
from typing import Generator

from bs4 import BeautifulSoup
from loguru import logger
from markdownify import markdownify
from tqdm import tqdm
import click
import pandas as pd
import requests


def parse_link(row: pd.Series) -> pd.DataFrame:
    """
    Parse the links in the blog main page to get the links to the posts and their metadata.

    Parameters:
    - row (pd.Series): A Pandas Series containing the 'soup' column.

    Returns:
    - pd.DataFrame: A DataFrame with post metadata.
    """
    post_previews = row["soup"].find_all("article", class_="articoli-item")  # type: ignore
    logger.debug(f"{post_previews=}")
    posts = [
        {
            "url": post_preview.find("h1", class_="titolo").a.get("href"),
            "title": post_preview.find("h1", class_="titolo").text.strip(),
            "author": post_preview.find("meta", itemprop="author").get("content"),
            "date": post_preview.find("meta", itemprop="datePublished").get("content"),
        }
        for post_preview in post_previews
    ]
    df = pd.DataFrame.from_records(posts)
    df["date"] = pd.to_datetime(df["date"])
    return df


def parse_post(row: pd.Series) -> pd.Series:
    """
    Get the actual post contents.

    Parameters:
    - row (pd.Series): A Pandas Series containing the 'soup' column.

    Returns:
    - pd.Series: The input row with additional 'post' and 'post_markdown' columns.
    """
    article = row["soup"].find("div", itemprop="articleBody")  # type: ignore
    row["post"] = article.prettify()
    row["post_markdown"] = markdownify(row["post"])
    return row


def page_url(root_url: str, i: int) -> str:
    """
    Generate the URL for a specific page.

    Parameters:
    - root_url (str): The root URL of the blog.
    - i (int): The page number.

    Returns:
    - str: The URL for the specified page.
    """
    return f"{root_url}/{i}"


def page_generator(root_url: str) -> Generator[BeautifulSoup, None, None]:
    """
    Generate BeautifulSoup objects for each page.

    Parameters:
    - root_url (str): The root URL of the blog.

    Yields:
    - BeautifulSoup: The parsed HTML content of each page.
    """
    page = 1
    while True:
        try:
            current_url = page_url(root_url, page)
            request = requests.get(current_url, timeout=30)
            request.raise_for_status()
            page_content = request.content
            if not page_content:
                break
            soup = BeautifulSoup(page_content, features="html.parser")
            logger.debug(f"{soup=}")
            number_of_tags = len(soup.find_all(True))
            logger.debug(f"{number_of_tags=}")
            if number_of_tags == 1:
                break
            page += 1
            yield soup
        except requests.exceptions.RequestException as e:
            raise click.ClickException(f"request failed for {current_url}: {e}") from e


def download_posts(df: pd.DataFrame) -> pd.DataFrame:
    """Download and convert the article pages listed in a DataFrame."""

    def fetch(url: str) -> bytes:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content

    tqdm.pandas(desc="requests.get")
    df = df.copy()
    df["html"] = df["url"].progress_apply(fetch)
    df["soup"] = df["html"].apply(BeautifulSoup, features="html.parser")
    logger.debug(f"{df=}")
    tqdm.pandas(desc="parse_post")
    return df.progress_apply(parse_post, axis=1)


def merge_with_snapshot(
    links: pd.DataFrame, snapshot: Path, incremental: bool
) -> pd.DataFrame:
    """Reuse stored article pages when incremental downloading is enabled."""
    if not snapshot.exists():
        return download_posts(links)

    previous = pd.read_csv(snapshot, compression="gzip", keep_default_na=False)
    content_columns = ["html", "soup", "post", "post_markdown"]
    existing_content = previous[["url", *content_columns]]
    if incremental:
        current = links.merge(existing_content, on="url", how="left")
        new_posts = current[current["post_markdown"].isna()][links.columns]
        if new_posts.empty:
            logger.info("No new articles; reusing the existing article content.")
            downloaded = current
        else:
            downloaded = download_posts(new_posts).set_index("url")
            current = current.set_index("url")
            current.loc[downloaded.index, content_columns] = downloaded[content_columns]
            downloaded = current.reset_index()
    else:
        downloaded = download_posts(links)

    missing = previous[~previous["url"].isin(links["url"])]
    if not missing.empty:
        logger.warning(
            "Retaining {} archived articles missing from the live listing.",
            len(missing),
        )
        downloaded = pd.concat([downloaded, missing], ignore_index=True)
    return downloaded


@click.command()
@click.argument("root_url", default="http://ilpedante.info/home/loadArticoli")
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(
        ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"],
        case_sensitive=False,
    ),
    show_default=True,
)
@click.option(
    "--incremental/--full",
    default=False,
    help="Reuse article content from the existing snapshot when possible.",
)
def main(root_url: str, log_level: str, incremental: bool) -> None:
    """
    Main function to scrape and save blog post data.

    Parameters:
    - root_url (str): The root URL of the blog.
    """

    logger.remove()
    logger.add(
        sys.stderr,
        level=log_level.upper(),
        format="{time:YYYY-MM-DD HH:mm} | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        colorize=True,
    )
    soups = [soup for soup in page_generator(root_url)]
    if not soups:
        raise click.ClickException("the live site returned no archive pages")
    df = pd.DataFrame({"soup": soups})
    logger.debug(f"{df=}")
    df = df.apply(parse_link, axis=1)
    df = pd.concat(df.tolist())
    if df.empty:
        raise click.ClickException("the live site returned no articles")
    logger.debug(f"{df=}")
    df = merge_with_snapshot(df, Path("_posts/posts.csv.gz"), incremental)
    logger.debug(f"{df=}")
    df.to_csv("_posts/posts.csv.gz", index=False)


if __name__ == "__main__":
    main()
