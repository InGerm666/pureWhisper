# Whisper Transcription

**[English](README.md)**

本地音频转文字桌面工具，基于 OpenAI Whisper 模型，完全离线运行，无需 API Key。

> **说明**：这是作者给自己和朋友做的小工具，目前仍在实验阶段，功能和界面随时可能调整。项目完全开源，欢迎自由使用和修改。如果遇到任何问题或有改进建议，欢迎直接联系作者交流 🙌

---

## 环境要求

- **macOS**
- **Python 3.10+**
- **ffmpeg**（Whisper 依赖它解码音频）
- **Git**（用于下载项目代码）

---

## 安装步骤

### 1. 安装 Homebrew

Homebrew 是 macOS 上的**包管理器**，可以通过简单的命令安装和卸载软件，卸载时不会有残留文件。常用命令：

- `brew install <软件名>` — 安装软件
- `brew uninstall <软件名>` — 卸载软件

打开「终端」（Terminal），粘贴以下命令安装 Homebrew：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

安装完成后，终端会提示你运行两条命令来配置环境变量，类似：

```bash
echo >> ~/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

> **注意**：请以终端实际输出的命令为准，直接复制粘贴运行即可。这一步是让系统能识别 `brew` 命令。

验证安装成功：

```bash
brew --version
```

看到版本号输出（如 `Homebrew 4.x.x`）即为成功。

### 2. 安装 Python

从 Python 官网下载安装包（推荐 3.13）：

👉 **https://www.python.org/downloads/**

下载后双击 `.pkg` 文件，按提示完成安装即可。

> ⚠️ **不建议用 `brew install python`**，brew 版本不自带 tkinter，会导致程序无法启动。

验证：

```bash
python3 --version
pip3 --version
```

### 3. 安装 ffmpeg

```bash
brew install ffmpeg
```

验证：

```bash
ffmpeg -version
```

### 4. 安装 Git

> Git 不只是版本控制工具——**Homebrew 本身依赖 Git** 来管理包仓库（`brew update` 底层就是 `git pull`），很多包的安装源也是 Git 仓库。不装 Git，brew 都没法正常工作。

```bash
brew install git
```

验证：

```bash
git --version
```

### 5. 下载项目

```bash
cd ~/Desktop
git clone https://github.com/InGerm666/pureWhisper
cd pureWhisper
```

> 这会把项目下载到桌面。安装完成后你可以把 `pureWhisper` 文件夹移到任意位置。

或者直接在 GitHub 页面点 **Code → Download ZIP**，解压后在终端进入该文件夹。

### 6. 安装 Python 依赖

项目根目录下有 `requirements.txt`，使用虚拟环境安装依赖（避免 macOS 系统级冲突）：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> `venv` 会在项目文件夹内创建一个隔离的 Python 环境，这是 macOS 上安装第三方包的推荐方式。

> 首次安装 `openai-whisper` 会同时下载 PyTorch（约 2 GB），请耐心等待。

> 如果遇到报错请第一时间联系作者，作者会手把手帮你解决问题。

---

## 运行

**最简单的方式 — 双击项目文件夹中的 `start.command`**，它会自动配置环境并启动应用。

或者在终端手动运行：

```bash
cd 你的路径/pureWhisper
source venv/bin/activate
python3 whisper_app.py
```

> 💡 **小技巧**：输入 `cd `（注意后面有空格），然后把 `pureWhisper` 文件夹直接拖进终端窗口，路径会自动填入。

---

## 使用方法

1. **选择音频** — 点击拖放区域浏览文件，或直接将音频文件拖入窗口，或点击 `Scan Dir` 扫描程序所在目录的音频文件
2. **选择模型** — 从 tiny 到 turbo，模型越大越准但越慢（见下方模型对照表）
3. **English-only 开关** — tiny / base / small / medium 支持 `.en` 模式，纯英文音频下更快更准
4. **设置导出目录** — 默认为程序所在目录，可点击 `Choose` 自选或 `Desktop` 一键设为桌面
5. **开始转录** — 点击 `Start Transcription`，首次使用某模型会自动下载权重文件
6. **查看结果** — 完成后右侧面板显示转录文本，同时自动保存为 `<文件名>_transcript.txt`
7. **复制 / 打开 / 删除** — 右侧面板提供 `Copy All`（复制全文）、`Open Folder`（打开导出目录）、`Delete .txt`（删除所有转录文件）

---

## 模型选择参考

| 模型 | 大小 | 速度 | 适用场景 |
|------|------|------|----------|
| tiny | ~39 MB | 最快 | 快速预览、测试 |
| base | ~74 MB | 快 | 日常短音频 |
| small | ~244 MB | 中 | 多语言、较好准确率 |
| medium | ~769 MB | 慢 | 高准确率 |
| large | ~1.5 GB | 很慢 | 最高准确率 |
| turbo | ~809 MB | 较快 | large 的加速版，推荐 |

> Apple Silicon Mac 会自动使用 Metal 加速，无需额外配置。

## 支持的音频格式

mp3 · m4a · wav · flac · mp4 · ogg · aac
