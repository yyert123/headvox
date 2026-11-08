from headvox.script import split_script, strip_markdown, iter_words


def test_markdown_is_reduced_to_speech():
    md = "# Title\n\nHello **world**, see [docs](https://x.y).\n\n```py\nprint(1)\n```\n\n- item one"
    plain = strip_markdown(md)
    assert "**" not in plain and "https" not in plain and "print" not in plain
    assert "Hello world, see docs." in plain
    assert "item one" in plain


def test_chinese_sentences_and_paragraph_pauses():
    segs = split_script("你好。今天天气不错！\n\n第二段来了？", sentence_pause_ms=200, paragraph_pause_ms=800)
    assert [s.text for s in segs] == ["你好。", "今天天气不错！", "第二段来了？"]
    assert segs[0].pause_after_ms == 200
    assert segs[1].pause_after_ms == 800
    assert segs[-1].pause_after_ms == 0


def test_pause_directive():
    segs = split_script("One. [pause 1.5s] Two. [pause 300ms] Three. [pause] Four.")
    by_text = {s.text: s.pause_after_ms for s in segs}
    assert by_text["One."] >= 1500
    assert by_text["Two."] >= 300
    assert by_text["Three."] >= 600


def test_long_sentence_splits_at_clause():
    long = "，".join(["这是一个比较长的分句"] * 12) + "。"
    segs = split_script(long, max_len=60)
    assert len(segs) > 1
    assert "".join(s.text for s in segs).replace("，", "") == long.replace("，", "")


def test_decimal_and_abbrev_not_split():
    segs = split_script("Version 2.5 ships today. Done.")
    assert segs[0].text == "Version 2.5 ships today."


def test_iter_words_mixed():
    assert list(iter_words("用 Python 写")) == ["用", "Python", "写"]
