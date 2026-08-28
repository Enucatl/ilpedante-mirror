from pathlib import Path

from ilpedante_mirror.archive import (
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
        ("che-cosa-penso-delle-sardine", 'Che cosa penso delle "sardine"')
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


def test_generate_includes_empty_post_from_snapshot(tmp_path: Path) -> None:
    generated = generate(SOURCE, tmp_path / "posts", tmp_path)

    assert generated
    assert any(
        path.name == "2019-12-11-che-cosa-penso-delle-sardine.md" for path in generated
    )
