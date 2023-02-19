import locale

from bs4 import BeautifulSoup
from markdownify import markdownify
from tqdm import tqdm
import click
import pandas as pd
import requests


locale.setlocale(locale.LC_ALL, "it_IT.UTF-8")


def parse_link(row):
    # parse the links in the blog main page to get the links to the posts and
    # their metadata
    post_previews = row["soup"].find_all("article", class_="articoli-item")

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


def parse_post(row):
    # get the actual post contents
    article = row["soup"].find("div", itemprop="articleBody")
    row["post"] = article.prettify()
    row["post_markdown"] = markdownify(row["post"])
    return row


def page_url(root_url: str, i: int) -> str:
    return f"{root_url}/{i}"


def page_generator(root_url):
    page = 1
    while (page_content := requests.get(page_url(root_url, page)).content):
        soup = BeautifulSoup(page_content, features="html.parser")
        page += 1
        yield soup


@click.command()
@click.argument("root_url", default="http://ilpedante.info/home/loadArticoli")
def main(root_url):
    soups = [soup for soup in page_generator(root_url)]
    df = pd.DataFrame({"soup": soups})
    df = df.apply(parse_link, axis=1)
    df = pd.concat(df.tolist())
    # get all articles from the collected links
    tqdm.pandas(desc="requests.get")
    df["html"] = df["url"].progress_apply(lambda x: requests.get(x).content)
    df["soup"] = df["html"].apply(BeautifulSoup, features="html.parser")
    tqdm.pandas(desc="parse_post")
    df = df.progress_apply(parse_post, axis=1)
    df.to_csv("_posts/posts.csv.gz", index=False)


if __name__ == "__main__":
    main()
