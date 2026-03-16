# Whisper Transcription

A local audio-to-text desktop app powered by OpenAI Whisper. Runs completely offline — no API key required.

> **Note**: This is a small tool the author built for personal use and friends. It's still experimental — features and UI may change at any time. The project is fully open-source. Feel free to use and modify it. If you run into any issues or have suggestions, don't hesitate to reach out 🙌

---

## Requirements

- **macOS**
- **Python 3.10+**
- **ffmpeg** (required by Whisper for audio decoding)
- **Git** (for cloning the project)

---

## Installation

### 1. Install Homebrew

Homebrew is a **package manager** for macOS. It lets you install and uninstall software with simple commands. Common usage:

- `brew install <package>` — install
- `brew uninstall <package>` — uninstall

Open Terminal and paste:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After installation, the terminal will prompt you to run two commands to set up your PATH, something like:

```bash
echo >> ~/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

> **Note**: Copy and paste the exact commands shown in your terminal. This step makes the `brew` command available system-wide.

Verify:

```bash
brew --version
```

You should see version output like `Homebrew 4.x.x`.

### 2. Install Python

```bash
brew install python
```

Verify:

```bash
python3 --version
pip3 --version
```

### 3. Install ffmpeg

```bash
brew install ffmpeg
```

Verify:

```bash
ffmpeg -version
```

### 4. Install Git

> Git is not just for version control — **Homebrew itself depends on Git** to manage its package repository (`brew update` is essentially `git pull` under the hood). Without Git, brew won't work properly.

```bash
brew install git
```

Verify:

```bash
git --version
```

### 5. Clone the project

```bash
git clone https://github.com/InGerm666/pureWhisper
cd pureWhisper
```

Or click **Code → Download ZIP** on the GitHub page and extract it.

### 6. Install Python dependencies

The project root contains `requirements.txt`. Install everything with one command:

```bash
pip3 install -r requirements.txt
```

> First-time installation of `openai-whisper` will also download PyTorch (~2 GB). Please be patient.

> If you encounter an `"externally-managed-environment"` error, use a virtual environment:
> If you run into any errors, feel free to contact the author — happy to help you troubleshoot step by step.
>
> ```bash
> python3 -m venv venv
> source venv/bin/activate
> pip install -r requirements.txt
> ```

---

## Run

```bash
python3 whisper_app.py
```

---

## Usage

1. **Select audio** — Click the drop zone to browse, drag and drop an audio file into the window, or click `Scan Dir` to scan the app's directory for audio files
2. **Choose a model** — From tiny to turbo. Larger models are more accurate but slower (see model table below)
3. **English-only toggle** — tiny / base / small / medium support `.en` mode for faster and more accurate English-only transcription
4. **Set export directory** — Defaults to the app's directory. Click `Choose` to pick a folder or `Desktop` for a quick shortcut
5. **Start transcription** — Click `Start Transcription`. The model weights will be downloaded automatically on first use
6. **View results** — The transcript appears in the right panel and is automatically saved as `<filename>_transcript.txt`
7. **Copy / Open / Delete** — The right panel provides `Copy All`, `Open Folder`, and `Delete .txt` (deletes all transcript files)

---

## Model Reference

| Model | Size | Speed | Best for |
|-------|------|-------|----------|
| tiny | ~39 MB | Fastest | Quick preview, testing |
| base | ~74 MB | Fast | Short everyday audio |
| small | ~244 MB | Medium | Multilingual, good accuracy |
| medium | ~769 MB | Slow | High accuracy |
| large | ~1.5 GB | Very slow | Highest accuracy |
| turbo | ~809 MB | Fast | Accelerated large model, recommended |

> Apple Silicon Macs automatically use Metal acceleration — no extra setup needed.

## Supported Audio Formats

mp3 · m4a · wav · flac · mp4 · ogg · aac

---

# 中文说明

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

```bash
brew install python
```

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
git clone https://github.com/InGerm666/pureWhisper
cd pureWhisper
```

或者直接在 GitHub 页面点 **Code → Download ZIP**，解压后在终端进入该文件夹。

### 6. 安装 Python 依赖

项目根目录下有 `requirements.txt`，一条命令安装所有依赖：

```bash
pip3 install -r requirements.txt
```

> 首次安装 `openai-whisper` 会同时下载 PyTorch（约 2 GB），请耐心等待。

> 如果遇到 `"externally-managed-environment"` 报错，使用虚拟环境：
> 如果遇到报错请第一时间联系作者，作者会手把手帮你解决问题
>
> ```bash
> python3 -m venv venv
> source venv/bin/activate
> pip install -r requirements.txt
> ```

---

## 运行

```bash
python3 whisper_app.py
```

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
