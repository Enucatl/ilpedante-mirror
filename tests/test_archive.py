from pathlib import Path

from ilpedante_mirror.archive import (
    EMPTY_POST_SLUG,
    Post,
    front_matter,
    generate,
    read_posts,
    rewrite_internal_links,
    rewrite_media,
)

SOURCE = Path("_posts/posts.csv.gz")


def test_snapshot_has_one_empty_post() -> None:
    posts = read_posts(SOURCE)

    assert posts
    assert [(post.slug, post.title) for post in posts if not post.markdown.strip()] == [
        (EMPTY_POST_SLUG, 'Che cosa penso delle "sardine"')
    ]


def test_front_matter_quotes_yaml_sensitive_title() -> None:
    post = next(post for post in read_posts(SOURCE) if '"sardine"' in post.title)

    assert 'title: "Che cosa penso delle \\"sardine\\""' in front_matter(post)


def test_slug_is_preserved_from_original_url() -> None:
    post = next(
        post for post in read_posts(SOURCE) if post.title == "Arie pedanti (il libro)"
    )

    assert post.slug == "arie-pedanti-il-libro"


def test_internal_links_use_repository_base_path() -> None:
    source = (
        "[uno](https://ilpedante.info/post/un-titolo#parte) "
        "[due](/post/altro/) [doppio](https://ilpedante.info//post/doppio) "
        "[esterno](https://example.com/post/notizia)"
    )

    assert rewrite_internal_links(source) == (
        "[uno]({{ site.baseurl }}/post/un-titolo/#parte) "
        "[due]({{ site.baseurl }}/post/altro/) "
        "[doppio]({{ site.baseurl }}/post/doppio/) "
        "[esterno](https://example.com/post/notizia)"
    )


def test_media_rewriting_and_missing_embed_note() -> None:
    source = (
        "![presente](/files/p.png)\n"
        "![assente](http://ilpedante.info/files/a.png)\n"
        "[documento](http://ilpedante.info/files/a.pdf)"
    )

    result = rewrite_media(source, {"/files/p.png"})

    assert "![presente]({{ site.baseurl }}/files/p.png)" in result
    assert "Nota d'archivio" in result
    assert "http://ilpedante.info/files/a.png" in result
    assert "media non recuperato; URL originale" in result


def test_generate_omits_empty_post(tmp_path: Path) -> None:
    generated = generate(SOURCE, tmp_path / "posts", tmp_path)

    assert generated
    assert not any(EMPTY_POST_SLUG in path.name for path in generated)


def test_recovered_posts_are_added_from_local_manifest(tmp_path: Path) -> None:
    recovered = tmp_path / "recovered.json"
    recovered.write_text(
        '[{"slug":"nuovo","title":"Nuovo","author":"Il Pedante",'
        '"date":"2025-06-10 09:15:22","markdown":"Test"}]',
        encoding="utf-8",
    )

    generated = generate(SOURCE, tmp_path / "posts", tmp_path, recovered)

    assert (tmp_path / "posts/2025-06-10-nuovo.md").exists()


def test_checked_in_recovery_manifest_generates_recovered_posts(tmp_path: Path) -> None:
    generated = generate(
        SOURCE,
        tmp_path / "posts",
        tmp_path,
        Path("recovered_source/recovered_posts.json"),
    )

    assert any(
        path.name == "2019-12-11-che-cosa-penso-delle-sardine.md" for path in generated
    )
