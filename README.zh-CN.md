<div align="center">

<img src="https://raw.githubusercontent.com/yyert123/headvox/main/assets/social-preview.png" alt="HeadVox：文字稿一键生成口播配音和逐字对齐字幕" width="760">

# HeadVox

**文字稿 → 口播配音 + 逐字对齐的 SRT/VTT 字幕，一条命令完成。**
面向口播视频、知识讲解、网课和短视频的开源 Python 命令行工具与库。支持中文 · 英文 · 日语。

[![PyPI](https://img.shields.io/pypi/v/headvox.svg)](https://pypi.org/project/headvox/)
[![Python](https://img.shields.io/pypi/pyversions/headvox.svg)](https://pypi.org/project/headvox/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/yyert123/headvox/blob/main/LICENSE)
[![在线试听](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-%E5%9C%A8%E7%BA%BF%E8%AF%95%E5%90%AC-yellow)](https://huggingface.co/spaces/headvox/headvox)

[English](https://github.com/yyert123/headvox/blob/main/README.md) · **简体中文** · [日本語](https://github.com/yyert123/headvox/blob/main/README.ja.md)

<img src="https://raw.githubusercontent.com/yyert123/headvox/main/assets/demo.gif" alt="HeadVox 演示：真实输出，逐词高亮的字幕时间轴" width="720">

<sub>真实未修饰的输出（英文样例，Aria 音色），高亮的词由 <code>voiceover.json</code> 的逐词时间驱动。<a href="https://github.com/yyert123/headvox/blob/main/assets/demo-en.mp4">带声音的 MP4</a> · <a href="https://huggingface.co/spaces/headvox/headvox">更多样例（含中文）</a></sub>

</div>

---

**HeadVox** 是一个免费、MIT 协议的开源命令行工具和 Python 库：把纯文本或 Markdown 文字稿变成自然的神经语音口播配音，同时生成**按真实发音时间逐字对齐**的 SRT 和 WebVTT 字幕，以及**带逐词毫秒时间戳的 JSON 时间轴**。它还能用 ffmpeg 把配音和字幕直接合成到你的视频素材上——自动循环画面到配音长度，背景音乐在人声出现时自动压低。适合做口播、知识讲解、网课、产品演示，以及抖音 / B 站 / 视频号 / YouTube Shorts 短视频，再也不用手动卡字幕。

```bash
pip install "headvox[edge]"
headvox 稿子.md -o out/ --voice zh-female --video 口播素材.mp4
# out/voiceover.mp3  voiceover.srt  voiceover.vtt  voiceover.json  voiceover.mp4
```

▶ **试听未经修饰的真实输出**（中英文样例，字幕按生成的 VTT 实时滚动）：<https://huggingface.co/spaces/headvox/headvox>

## 📰 动态

- **2026-11-08** · v0.1.1：英文 / 简体中文 / 日本語 完整文档、可复现的性能测试脚本、在线样例页。
- **2026-11-08** · v0.1.0：首个公开版本发布到 [PyPI](https://pypi.org/project/headvox/)。

## 为什么做 HeadVox

做一条带配音的短视频，通常要分三步折腾：生成配音、手动卡字幕、再把两者压进视频。稿子改一句，三步全部重来。普通 TTS 工具只给你一个 MP3，最多每句一条字幕——对有声书够用，对竖屏短视频来说太长、也常常不准；中文、日文没有空格，按空格断行更是一团糟。

HeadVox 把**音频、字幕、时间轴当成同一个产物**，从同一份稿子生成，所以它们不可能互相漂移。

## 核心功能

| | |
|---|---|
| 🎯 **字幕逐字对齐** | 字幕时间来自语音引擎返回的真实词边界，不是按字数估算——第 40 条字幕和第 1 条一样准。 |
| 🀄 **中日文友好断行** | 中日文字符按 2 列宽计算，在宽度预算内（`--caption-chars`）优先在标点处断行，中英混排也不会冲出 9:16 屏幕。 |
| ⏸️ **节奏可控** | 句间（250 毫秒）、段间（700 毫秒）自动停顿；稿子里任意位置写 `[pause]`、`[pause 1.5s]`、`[pause 400ms]` 即可加停顿。 |
| 📝 **直接读 Markdown** | 标题、加粗、链接、代码块、列表符号会被还原成主播真正会念的话。 |
| 🧭 **逐词 JSON 时间轴** | 每段、每个词的起止毫秒——可直接驱动数字人口型、逐字高亮（卡拉 OK 字幕）或自定义字幕动画。 |
| 🎬 **一步合成视频** | 口播素材自动循环到配音长度；背景音乐用侧链压缩自动避让人声；软字幕或硬字幕任选。 |
| ⚡ **片段缓存** | 每句按「文本 + 音色参数」缓存，改一个词只重新合成那一句。 |
| 🧩 **可插拔语音后端** | `edge`（免费在线神经语音，无需 API Key）和 `sine`（离线，用于测试和预演），约 10 行代码即可接入你自己的引擎。 |
| 🪶 **轻量** | 纯 Python，无必需依赖，只需系统里有 ffmpeg；不打包、不下载任何模型。 |

## 和其他工具怎么选

| 你的需求 | 更合适的工具 |
|---|---|
| 把一小段文字转成 MP3 | 直接用 `edge-tts` 命令行 |
| 「输入主题 → AI 写稿 → 找素材 → 出片」全自动 | 端到端的短视频生成流水线 |
| 给**已经有人声**的视频生成字幕 | 基于 Whisper 的语音识别字幕工具 |
| 用**自己写的稿子**生成配音，字幕逐字对齐、中文友好、停顿可控，还要可复用的时间轴文件，并能合成到自己的素材上 | **HeadVox** |

HeadVox 刻意做成专注、可组合的一环：把一件事做好，然后把干净的 MP3/SRT/VTT/JSON/MP4 交给你已经在用的剪辑软件或流水线。

## 安装

```bash
pip install "headvox[edge]"   # 带免费在线神经语音（推荐）
pip install headvox           # 只要库和离线 sine 后端
```

需要 Python 3.9+，以及 PATH 中可用的 **ffmpeg** 和 `ffprobe`（macOS：`brew install ffmpeg`；Ubuntu：`sudo apt install ffmpeg`；Windows：`winget install ffmpeg`）。

## 快速上手

```bash
headvox 稿子.md -o out/                                   # 稿子进，文件出
headvox 稿子.md -o out/ --voice zh-male --rate +8         # 换男声，稍快一点
headvox 稿子.md --dry-run                                 # 只预览切分结果，不调用语音服务
echo "你好，这是 HeadVox。" | headvox - -o out/            # 从标准输入读取
```

常用参数（完整列表见 `headvox --help`）：

| 参数 | 默认值 | 作用 |
|---|---|---|
| `-v, --voice` | `zh-female` | 预设音色或任意 edge-tts 语音 ID |
| `--rate` / `--pitch` / `--volume` | `0` | 语速 %、音调 Hz、音量 %（如 `+8`、`-5`） |
| `--format` | `mp3` | `mp3`、`wav`、`m4a` |
| `--sentence-pause` / `--paragraph-pause` | `250` / `700` | 句间 / 段间停顿（毫秒） |
| `--caption-chars` | `42` | 字幕宽度预算（中文字符算 2） |
| `--video` | – | 要合成配音的视频素材 |
| `--fit` | `loop` | `loop` 循环画面到配音长度，或 `audio` 以配音长度为准 |
| `--music` / `--music-volume` | – / `0.12` | 背景音乐，自动循环并避让人声 |
| `--burn-subs` / `--no-subs` | 关 | 把字幕烧进画面 / 不加字幕 |
| `--proxy` | – | 在线后端使用的 HTTP 代理（或环境变量 `HEADVOX_PROXY`） |

## 怎样写出好听的稿子

- **一句话只讲一个点。** 句子短，字幕就短，读起来也更自然。
- **段落之间空一行**，会变成更长的停顿。
- **有意识地加停顿**：`就是这么简单。[pause 0.8s] 接下来是重点。`
- **写成要念出来的样子**：数字、缩写、版本号如果读错，就直接写成「二〇二六年」「零点一版」。
- **Markdown 没问题**：`# 标题` 会当普通句子念，`**加粗**` 的星号会被去掉，代码块会跳过。
- 竖屏（9:16）建议 `--caption-chars 24` 到 `28`；横屏 16:9 用默认 42 即可。

## 实用配方

**抖音 / 视频号 / Shorts 竖屏，硬字幕 + 背景音乐**
```bash
headvox 短视频.md -o out/ --voice zh-female --rate +6 --caption-chars 26 \
        --video 竖屏口播.mp4 --burn-subs --music 配乐.mp3
```

**网课 / B 站横屏，可开关的软字幕**
```bash
headvox 第三课.md -o 第三课/ --voice zh-male --video 课件录屏.mp4 --fit audio
```

**中英双语两个版本**
```bash
headvox intro.zh.md -o out/zh --voice zh-female
headvox intro.en.md -o out/en --voice en-female
```

**导入剪映 / Premiere / 达芬奇**：把 `voiceover.mp3` 和 `voiceover.srt` 一起导入，字幕会落在正确的帧上。

**批量处理一个文件夹**
```bash
for f in scripts/*.md; do headvox "$f" -o "out/$(basename "$f" .md)"; done
```
没改过的句子直接走缓存，重跑很快。

## Python 调用

```python
from headvox import synthesize, Script, VoiceSettings

res = synthesize(
    Script.from_file("稿子.md"),
    "out/",
    backend="edge",
    settings=VoiceSettings(voice="zh-CN-XiaoxiaoNeural", rate_pct=5),
)
print(res.duration_ms, "毫秒，", len(res.cues), "条字幕")
for cue in res.cues:
    print(cue.start_ms, cue.end_ms, cue.text)
```

接入自己的语音引擎、时间轴 JSON 格式等进阶内容见 [英文文档](https://github.com/yyert123/headvox/blob/main/README.md#custom-backend)。

## 预设音色

| 预设 | edge-tts 语音 |
|---|---|
| `zh-female` | `zh-CN-XiaoxiaoNeural`（晓晓） |
| `zh-male` | `zh-CN-YunxiNeural`（云希） |
| `en-female` | `en-US-AvaMultilingualNeural` |
| `en-male` | `en-US-AndrewMultilingualNeural` |
| `ja-female` | `ja-JP-NanamiNeural` |
| `ja-male` | `ja-JP-KeitaNeural` |

也可以传入任意 edge-tts 语音 ID（`edge-tts --list-voices` 查看），包括粤语、台湾普通话等。

## 常见问题排查

| 现象 | 解决办法 |
|---|---|
| 提示找不到 ffmpeg | 安装 ffmpeg，并确保 `ffmpeg`、`ffprobe` 都在 PATH 中 |
| edge 报 `NoAudioReceived` | 语音 ID 有误或暂时不可用，换个音色或稍后重试 |
| 网络受限 / 需要代理 | `--proxy http://host:port` 或设置 `HEADVOX_PROXY` |
| `--burn-subs` 失败 | 你的 ffmpeg 没有 libass，改用默认软字幕或安装完整版 ffmpeg |
| 竖屏字幕太长 | 调小 `--caption-chars`（如 24–28） |

## 常见问题

**HeadVox 免费吗？** 免费，MIT 开源。默认的 `edge` 后端通过 `edge-tts` 使用 Microsoft Edge「大声朗读」背后的免费在线服务，需要联网，但不需要 API Key 或账号。

**能离线用吗？** 解析、拼接、字幕、视频合成都在本地完成；用 `edge` 合成语音需要联网。通过后端接口接入本地 TTS 引擎即可完全离线。

**字幕为什么比按句切分更准？** HeadVox 使用引擎朗读时发出的词边界事件，去掉部分引擎在片段首尾加的静音，再放置断行——每条字幕都在第一个字真正被听到时出现。

**能直接生成数字人吗？** 不能，HeadVox 不渲染人脸。它产出数字人 / 口型工具需要的配音、字幕和逐词时间轴，也能把结果合成到你已有的数字人视频上。

**生成的配音能商用吗？** HeadVox 代码是 MIT 协议；合成语音的使用权取决于你所用的语音服务条款，请按你的用途自行确认。

**和微软或 edge-tts 有关系吗？** 没有。HeadVox 是独立的原创项目，只是把 `edge-tts` 作为可选后端之一。

## 📊 实测性能

使用 [`scripts/bench.py`](https://github.com/yyert123/headvox/blob/main/scripts/bench.py) 对 [`examples/`](https://github.com/yyert123/headvox/blob/main/examples) 中的两份示例稿实测：2 核 aarch64 云端沙箱、Python 3.12，edge 语音经 HTTP 代理访问（2026-11-08）。「首次」包含访问语音服务的网络往返，「缓存」为缓存命中后的重跑。

| 稿子 | 后端 / 音色 | 音频时长 | 字幕条数 | 最宽一条 | 重叠 | 首次 | 缓存 | 首次 RTF |
|---|---|---|---|---|---|---|---|---|
| `demo-en.md` | edge · en-US-AriaNeural | 20.1 秒 | 9 | 41 / 42 | 0 | 5.75 秒 | 0.63 秒 | 0.29 |
| `demo-zh.md` | edge · zh-CN-XiaoxiaoNeural | 23.2 秒 | 8 | 38 / 42 | 0 | 5.25 秒 | 0.65 秒 | 0.23 |
| `demo-en.md` | sine（离线） | 18.4 秒 | 9 | 39 / 42 | 0 | 0.93 秒 | 0.60 秒 | 0.05 |

RTF = 处理耗时 ÷ 音频时长，越低越快。实际速度主要取决于你到语音服务的网络延迟。复现：`python scripts/bench.py examples/demo-zh.md --voice zh-CN-XiaoxiaoNeural`

## 工作原理

<img src="https://raw.githubusercontent.com/yyert123/headvox/main/assets/pipeline.png" alt="HeadVox 流程：解析、合成、拼接、字幕、合成视频" width="100%">

1. **解析**：把稿子拆成适合朗读的片段，去掉 Markdown，识别 `[pause]` 指令。
2. **合成**：逐段调用语音后端，按文本和音色参数缓存。
3. **拼接**：合成一条 24 kHz 音轨，修掉引擎自带的首尾空白，保证停顿精确。
4. **字幕**：根据词边界生成字幕，在中日文友好的宽度预算内按标点断行。
5. **合成视频**（可选）：ffmpeg 合成到视频上，循环画面、压低音乐，添加软字幕或硬字幕。

## 🗺️ 路线图

- [ ] 本地模型后端（如 VoxCPM / CosyVoice），支持完全离线和声音克隆
- [ ] ASS 字幕输出，支持样式和卡拉 OK 效果
- [ ] 多角色稿子（`[voice zh-male]` 切换音色）
- [ ] 更多语言的断行规则
- [ ] 可选的 Web 界面

## ⚠️ 风险与局限

- **在线后端**：默认 `edge` 后端会把稿子文本发送到微软的在线朗读服务，需要联网。保密内容请接入本地后端。
- **声音权利**：HeadVox 代码为 MIT 协议，合成语音的使用权取决于所用语音服务的条款，商用前请确认。
- **如实标注**：合成配音可能被误认为真人。请勿用于冒充他人；平台或观众有要求时请标注 AI 配音。
- **能力范围**：HeadVox 不生成人脸、不克隆声音、不识别已有音频。

## 参与开发

```bash
git clone https://github.com/yyert123/headvox.git
cd headvox
pip install -e ".[dev]"
pytest            # 通过离线 sine 后端完整运行
```

欢迎提 Issue 和 PR，特别是新的语音后端、更多语言的断行规则和字幕样式。

## 📖 引用

如果 HeadVox 对你的课程、研究或产品有帮助，欢迎通过 [`CITATION.cff`](https://github.com/yyert123/headvox/blob/main/CITATION.cff)（GitHub 右侧「Cite this repository」）引用，也欢迎点个 ⭐。

## 许可证

[MIT](https://github.com/yyert123/headvox/blob/main/LICENSE)。HeadVox 为原创作品，与 Microsoft 及 `edge-tts` 项目无关联。

## 🙏 致谢

- [edge-tts](https://github.com/rany2/edge-tts)：访问 Microsoft Edge 在线语音的 Python 客户端
- [FFmpeg](https://ffmpeg.org/)：音视频处理
