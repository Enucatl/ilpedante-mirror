"""
Blog Scraper

This script scrapes a blog's main page to gather links to posts and their metadata.
It then fetches the content of each post, converts it to Markdown, and saves the data in a CSV file.

Usage:
python ilpedante_mirror/bulk_download.py [root_url]

- root_url (optional): The root URL of the blog. Default is "http://ilpedante.info/home/loadArticoli".
"""

from typing import Generator
import locale
import sys

from bs4 import BeautifulSoup
from loguru import logger
from markdownify import markdownify
from tqdm import tqdm
import click
import pandas as pd
import requests


locale.setlocale(locale.LC_ALL, "it_IT.UTF-8")


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
            request = requests.get(current_url)
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
            logger.error(f"request failed for {current_url=}: {e}")
            break


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
def main(root_url: str, log_level: str) -> None:
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
    df = pd.DataFrame({"soup": soups})
    logger.debug(f"{df=}")
    df = df.apply(parse_link, axis=1)
    df = pd.concat(df.tolist())
    logger.debug(f"{df=}")
    # get all articles from the collected links
    tqdm.pandas(desc="requests.get")
    df["html"] = df["url"].progress_apply(lambda x: requests.get(x).content)
    df["soup"] = df["html"].apply(BeautifulSoup, features="html.parser")
    logger.debug(f"{df=}")
    tqdm.pandas(desc="parse_post")
    df = df.progress_apply(parse_post, axis=1)
    logger.debug(f"{df=}")
    df.to_csv("_posts/posts.csv.gz", index=False)


if __name__ == "__main__":
    main()
