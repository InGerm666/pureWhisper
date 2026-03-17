# Whisper Transcription

**[中文文档](README_CN.md)**

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

Download the installer from the official Python website (3.13 recommended):

👉 **https://www.python.org/downloads/**

Double-click the `.pkg` file and follow the prompts to install.

> ⚠️ **Do not use `brew install python`** — the Homebrew version doesn't include tkinter, which will prevent the app from launching.

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
cd ~/Desktop
git clone https://github.com/InGerm666/pureWhisper
cd pureWhisper
```

> This downloads the project to your Desktop. You can move the `pureWhisper` folder anywhere after setup.

Or click **Code → Download ZIP** on the GitHub page and extract it.

### 6. Install Python dependencies

The project root contains `requirements.txt`. Use a virtual environment to install dependencies (this avoids system-level conflicts on macOS):

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> `venv` creates an isolated Python environment inside the project folder. This is the recommended way to install packages on modern macOS.

> First-time installation of `openai-whisper` will also download PyTorch (~2 GB). Please be patient.

> If you run into any errors, feel free to contact the author — happy to help you troubleshoot step by step.

---

## Run

**Easiest way — double-click `start.command`** in the project folder. It automatically sets up the environment and launches the app.

Or run manually in Terminal:

```bash
cd /path/to/pureWhisper
source venv/bin/activate
python3 whisper_app.py
```

> 💡 **Tip**: Type `cd ` (with a trailing space), then drag the `pureWhisper` folder into the Terminal window — the path will be filled in automatically.

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
