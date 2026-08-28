from pathlib import Path

import pandas as pd

from ilpedante_mirror.bulk_download import merge_with_snapshot


def test_incremental_download_retains_missing_archived_posts(tmp_path: Path) -> None:
    snapshot = tmp_path / "posts.csv.gz"
    previous = pd.DataFrame(
        [
            {
                "url": "https://example.test/post/old",
                "title": "Old",
                "author": "Author",
                "date": "2024-01-01",
                "html": "old html",
                "soup": "old soup",
                "post": "old post",
                "post_markdown": "old markdown",
            }
        ]
    )
    previous.to_csv(snapshot, index=False, compression="gzip")

    links = previous[["url", "title", "author", "date"]].head(0)

    result = merge_with_snapshot(links, snapshot, incremental=True)

    assert list(result["url"]) == ["https://example.test/post/old"]
