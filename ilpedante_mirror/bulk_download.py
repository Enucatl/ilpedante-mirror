import locale

from bs4 import BeautifulSoup
from markdownify import markdownify
from tqdm import tqdm
import click
import pandas as pd
import requests


locale.setlocale(locale.LC_ALL, "it_IT.UTF-8")


def find_next(url):
    # find the link to the next pagination page
    page = requests.get(url).content
    soup = BeautifulSoup(page, features="html.parser")
    next_page = soup.find("li", class_="next").a.get("href")
    return next_page


def parse_link(row):
    # parse the links in the blog main page to get the links to the posts and
    # their metadata
    post_previews = row["soup"].find_all(class_="post-preview")
    posts = [
        {
            "url": post_preview.a.get("href"),
            "title": post_preview.find("h2", class_="post-title").text.strip(),
            "subtitle": post_preview.find("h3", class_="post-subtitle").text.strip(),
            "meta": post_preview.find("p", class_="post-meta").text,
        }
        for post_preview in post_previews
    ]
    df = pd.DataFrame.from_records(posts)
    df["date"] = pd.to_datetime(
        df["meta"].str.split("|").str[0].str.strip(), format="%d %B, %Y"
    )
    df["comments"] = (
        df["meta"]
        .str.split("|")
        .str[1]
        .str.replace("Nessun", "0")
        .str.replace("commento", "commenti")
        .str.replace("commenti", "")
        .astype(int)
    )
    df["pedanteria"] = df["meta"].str.split("|").str[2].str.count("●")
    return df


def parse_post(row):
    # get the actual post contents
    row["title"] = row["soup"].find("h1").string
    article = row["soup"].find("article").div.div.div
    article.find("div", class_="share").decompose()
    row["post"] = article.prettify()
    row["post_markdown"] = markdownify(row["post"])
    return row


@click.command()
@click.argument("root_url", default="http://ilpedante.info/blog/page-0")
def main(root_url):
    urls = [root_url]
    next_url = root_url
    while True:
        try:
            next_url = find_next(next_url)
            urls.append(next_url)
        except AttributeError:  # there was no next so this is the last page
            break
    df = pd.DataFrame({"url": urls})
    # get all pages of the blog
    df["html"] = df["url"].apply(lambda x: requests.get(x).content)
    df["soup"] = df["html"].apply(BeautifulSoup, features="html.parser")
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
