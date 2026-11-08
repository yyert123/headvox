<div align="center">

# HeadVox

**台本 → ナレーション音声 + 単語単位で同期した SRT/VTT 字幕を、コマンド一発で。**
顔出し動画・解説動画・オンライン講座・ショート動画向けのオープンソース Python CLI／ライブラリ。日本語・中国語・英語に対応。

[![PyPI](https://img.shields.io/pypi/v/headvox.svg)](https://pypi.org/project/headvox/)
[![Python](https://img.shields.io/pypi/pyversions/headvox.svg)](https://pypi.org/project/headvox/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/yyert123/headvox/blob/main/LICENSE)
[![サンプル試聴](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-%E3%82%B5%E3%83%B3%E3%83%97%E3%83%AB-yellow)](https://huggingface.co/spaces/headvox/headvox)

[English](https://github.com/yyert123/headvox/blob/main/README.md) · [简体中文](https://github.com/yyert123/headvox/blob/main/README.zh-CN.md) · **日本語**

</div>

---

**HeadVox** は無料・MIT ライセンスのコマンドラインツール兼 Python ライブラリです。プレーンテキストや Markdown の台本から自然なニューラル音声合成（TTS）でナレーションを作り、**実際の発話タイミングに合わせた SRT / WebVTT 字幕**と、**単語ごとのミリ秒タイムスタンプを含む JSON** を出力します。さらに ffmpeg で動画素材に合成し、映像をナレーションの長さまでループさせ、BGM を声に合わせて自動で下げることもできます。YouTube ショート・TikTok・解説動画・講座動画を作る人が、手作業の字幕タイミング調整から解放されるためのツールです。

```bash
pip install "headvox[edge]"
headvox script.md -o out/ --voice ja-female --video avatar.mp4
# out/voiceover.mp3  voiceover.srt  voiceover.vtt  voiceover.json  voiceover.mp4
```

▶ **無編集の実際の出力を試聴**（中国語・英語サンプル、生成された VTT で字幕が流れます）：<https://huggingface.co/spaces/headvox/headvox>

## 特長

| | |
|---|---|
| 🎯 **単語単位の字幕同期** | TTS エンジンが返す実際の単語境界から字幕を作るため、文字数からの推定と違い、後半でずれません。 |
| 🀄 **日本語・中国語に強い改行** | 全角文字を 2 桁として幅を計算し、句読点で優先的に改行。縦型 9:16 画面でもはみ出しません。 |
| ⏸️ **間（ま）を自在に** | 文間 250ms・段落間 700ms の自動ポーズに加え、`[pause]`、`[pause 1.5s]`、`[pause 400ms]` を台本の好きな場所に。 |
| 📝 **Markdown 対応** | 見出し・強調・リンク・コードブロック・箇条書き記号を、読み上げに適した文に変換。 |
| 🧭 **単語ごとの JSON タイムライン** | 口パク（リップシンク）・アバター・カラオケ風字幕・独自の字幕アニメーションにそのまま使えます。 |
| 🎬 **動画合成まで一発** | 素材のループ、サイドチェーンによる BGM の自動ダッキング、ソフト字幕／焼き込み字幕を選択可能。 |
| ⚡ **キャッシュ** | 文ごとにキャッシュするので、一語直しても再合成はその一文だけ。 |
| 🧩 **バックエンド差し替え** | `edge`（無料のオンライン音声、API キー不要）と `sine`（オフライン・テスト用）。独自エンジンも約 10 行で追加。 |

## インストール

```bash
pip install "headvox[edge]"
```

Python 3.9 以上と、PATH 上の **ffmpeg**／`ffprobe` が必要です。

## 使い方

```bash
headvox talk.md -o out/ --voice ja-female                  # 基本
headvox talk.md -o out/ --voice ja-male --rate +8          # 男性の声で少し速く
headvox talk.md --dry-run                                  # 分割結果だけ確認（TTS は呼ばない）
headvox short.md -o out/ --voice ja-female --caption-chars 26 \
        --video portrait.mp4 --burn-subs --music bgm.mp3   # 縦型ショート動画
```

プリセット音声：`ja-female`（`ja-JP-NanamiNeural`）、`ja-male`（`ja-JP-KeitaNeural`）、`zh-female`、`zh-male`、`en-female`、`en-male`。任意の edge-tts 音声 ID も指定できます（`edge-tts --list-voices`）。

全オプション、Python API、JSON の形式、独自バックエンドの書き方は [英語版 README](https://github.com/yyert123/headvox/blob/main/README.md) を参照してください。

## よくある質問

**無料ですか？** はい、MIT ライセンスです。既定の `edge` バックエンドは `edge-tts` 経由で Microsoft Edge の音声読み上げの無料オンラインサービスを使います。インターネット接続は必要ですが、API キーやアカウントは不要です。

**オフラインで使えますか？** 解析・結合・字幕・動画合成はすべてローカルです。`edge` での音声合成のみネット接続が必要で、ローカル TTS をバックエンドとして追加すれば完全オフラインにできます。

**アバター動画も作れますか？** 顔の生成は行いません。アバターやリップシンクツールが必要とする音声・字幕・単語タイミングを出力し、既存のアバター動画に合成できます。

**Microsoft や edge-tts とは関係がありますか？** ありません。HeadVox は独立したオリジナルのプロジェクトで、`edge-tts` を任意のバックエンドの一つとして利用しているだけです。

## ライセンス

[MIT](https://github.com/yyert123/headvox/blob/main/LICENSE)
