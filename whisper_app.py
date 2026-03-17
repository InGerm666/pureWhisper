import whisper
import os
import sys
import glob
import subprocess
import threading
import time
import queue
import re
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

AUDIO_EXTS = ("*.mp3", "*.m4a", "*.wav", "*.flac", "*.mp4", "*.ogg", "*.aac")
AUDIO_SUFFIXES = {".mp3", ".m4a", ".wav", ".flac", ".mp4", ".ogg", ".aac"}
MODELS = ["tiny", "base", "small", "medium", "large", "turbo"]
EN_MODELS = {"tiny", "base", "small", "medium"}
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Window sizes ────────────────────────────────────────────────────────────
SIZE_INIT = (600, 480)        # Title + drop zone + file path + model buttons
SIZE_MODEL = (600, 780)       # + export / start sections
SIZE_TRANSCRIPT = (1100, 780) # + right transcript panel

# ─── Theme: Minimal Black ────────────────────────────────────────────────────
BG = "#0A0A0A"
CARD = "#141414"
CARD2 = "#1A1A1A"
BORDER = "#2A2A2A"
TEXT = "#F0F0F0"
TEXT2 = "#999999"
TEXT3 = "#555555"
WHITE = "#FFFFFF"
GREEN = "#4ADE80"
AMBER = "#FBBF24"
RED = "#EF4444"

ctk.set_appearance_mode("dark")


_SEG_RE = re.compile(r"\[\d[\d:.]+\s*-->\s*(\d[\d:.]+)\]")


def _parse_end_time(line):
    """Extract end timestamp (seconds) from whisper segment line like [00:00.000 --> 00:30.000]."""
    m = _SEG_RE.search(line)
    if not m:
        return None
    t = m.group(1)
    parts = t.replace(".", ":").split(":")
    if len(parts) == 3:  # MM:SS:mmm
        return int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 1000
    elif len(parts) == 4:  # HH:MM:SS:mmm
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2]) + int(parts[3]) / 1000
    return None


class _StdoutCapture:
    """Capture stdout, parse segment timestamps, push progress to queue."""
    def __init__(self, msg_queue, duration):
        self._q = msg_queue
        self._duration = duration
        self._buf = ""

    def write(self, s):
        self._buf += s
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            end = _parse_end_time(line)
            if end is not None and self._duration > 0:
                prog = min(end / self._duration, 0.95)
                self._q.put(("progress", prog))
            self._q.put(("log", line))

    def flush(self):
        pass


class _StderrCapture:
    """Capture stderr and forward to queue (for model download progress etc.)."""
    def __init__(self, msg_queue):
        self._q = msg_queue
        self._buf = ""

    def write(self, s):
        self._buf += s
        if "\r" in self._buf or "\n" in self._buf:
            line = self._buf.strip()
            if line:
                self._q.put(("log", line))
            self._buf = ""

    def flush(self):
        pass


if HAS_DND:
    class BaseTk(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)
else:
    BaseTk = ctk.CTk


class WhisperApp(BaseTk):
    def __init__(self):
        super().__init__()
        self.title("Whisper")
        self.configure(fg_color=BG)
        self._resize_window(*SIZE_INIT, center=True)
        self._selected_model = tk.StringVar(value="")
        self._en_opt = tk.BooleanVar(value=False)
        self._export_dir = tk.StringVar(value=SCRIPT_DIR)
        self._file_path = tk.StringVar(value="")
        self._output_path = ""
        self._model_btns = {}
        self._cached_model = None
        self._cached_model_name = ""
        self._cancel_event = threading.Event()
        self._run_id = 0
        self._msg_queue = queue.Queue()
        self._build_ui()
        # Force initial render on macOS Sequoia (Tcl/Tk drawing bug)
        self.withdraw()
        self.update()
        self.deiconify()

    def _resize_window(self, w, h, center=False):
        self.update_idletasks()
        if center:
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            x = (sw - w) // 2
            y = (sh - h) // 2
            self.geometry(f"{w}x{h}+{x}+{y}")
        else:
            self.geometry(f"{w}x{h}")

    # ─── UI ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Horizontal split
        self._main = ctk.CTkFrame(self, fg_color=BG)
        self._main.pack(fill="both", expand=True)

        # Left controls
        self._left = ctk.CTkFrame(self._main, fg_color=BG, width=560)
        self._left.pack(side="left", fill="both", padx=(40, 20), pady=40)
        self._left.pack_propagate(False)

        # Right transcript
        self._right = ctk.CTkFrame(self._main, fg_color=CARD, corner_radius=16)

        # ── Title ────────────────────────────────────────────────────────────
        ctk.CTkLabel(self._left, text="Whisper",
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color=WHITE).pack(anchor="w")
        ctk.CTkLabel(self._left, text="Audio transcription, locally.",
                     font=ctk.CTkFont(size=13), text_color=TEXT3).pack(anchor="w", pady=(0, 24))

        # ── Drop Zone ────────────────────────────────────────────────────────
        self._drop = ctk.CTkFrame(self._left, height=110, corner_radius=12,
                                   fg_color=CARD, border_width=2,
                                   border_color=BORDER)
        self._drop.pack(fill="x", pady=(0, 16))
        self._drop.pack_propagate(False)

        drop_inner = ctk.CTkFrame(self._drop, fg_color="transparent")
        drop_inner.place(relx=0.5, rely=0.5, anchor="center")

        self._drop_icon = ctk.CTkLabel(drop_inner, text="↑", font=ctk.CTkFont(size=28),
                                        text_color=TEXT3)
        self._drop_icon.pack()
        self._drop_lbl = ctk.CTkLabel(drop_inner, text="Drop audio file here, or click to browse",
                                       font=ctk.CTkFont(size=13), text_color=TEXT2)
        self._drop_lbl.pack(pady=(2, 0))
        self._drop_fmt = ctk.CTkLabel(drop_inner, text="mp3 · m4a · wav · flac · mp4",
                                       font=ctk.CTkFont(size=10), text_color=TEXT3)
        self._drop_fmt.pack(pady=(2, 0))

        # Click to browse
        for w in (self._drop, drop_inner, self._drop_icon, self._drop_lbl, self._drop_fmt):
            w.bind("<Button-1>", lambda _: self._browse_file())

        # DnD
        if HAS_DND:
            self._drop.drop_target_register(DND_FILES)
            self._drop.dnd_bind('<<Drop>>', self._on_drop)

        # File path (compact)
        self._path_row = ctk.CTkFrame(self._left, fg_color="transparent")
        self._path_row.pack(fill="x", pady=(0, 20))
        ctk.CTkEntry(self._path_row, textvariable=self._file_path,
                     fg_color=CARD, border_color=BORDER, text_color=TEXT,
                     placeholder_text="Or enter file path...",
                     height=32, corner_radius=8).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(self._path_row, text="×", width=32, height=32,
                       fg_color=CARD, hover_color="#3C1111", border_width=1,
                       border_color=BORDER, text_color=TEXT3,
                       font=ctk.CTkFont(size=14),
                       corner_radius=8, command=self._clear_file).pack(side="left", padx=(0, 4))
        ctk.CTkButton(self._path_row, text="Scan Dir", width=75, height=32,
                       fg_color=CARD, hover_color=CARD2, border_width=1,
                       border_color=BORDER, text_color=TEXT2,
                       corner_radius=8, command=self._scan_dir).pack(side="left")

        # Scan dropdown (hidden until scan)
        self._scan_frame = ctk.CTkFrame(self._left, fg_color="transparent")
        self._scan_menu = ctk.CTkOptionMenu(self._scan_frame, width=500, height=32,
                                             fg_color=CARD, button_color=CARD2,
                                             button_hover_color=BORDER,
                                             text_color=TEXT2,
                                             command=self._on_scan_select)

        # ── Section: Model ───────────────────────────────────────────────────
        ctk.CTkLabel(self._left, text="MODEL",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT3).pack(anchor="w", pady=(0, 8))

        btn_row = ctk.CTkFrame(self._left, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 16))
        for m in MODELS:
            btn = ctk.CTkButton(btn_row, text=m, width=80, height=36,
                                corner_radius=8, fg_color=CARD,
                                border_width=1, border_color=BORDER,
                                text_color=TEXT3, hover_color=CARD2,
                                font=ctk.CTkFont(size=12),
                                command=lambda n=m: self._select_model(n))
            btn.pack(side="left", padx=(0, 6))
            self._model_btns[m] = btn

        # ── English opt (hidden) ─────────────────────────────────────────────
        self._en_sec = ctk.CTkFrame(self._left, fg_color="transparent")
        self._en_switch = ctk.CTkSwitch(self._en_sec,
                                         text="English-only model (.en)",
                                         variable=self._en_opt,
                                         progress_color=WHITE, button_color=WHITE,
                                         button_hover_color=TEXT2,
                                         font=ctk.CTkFont(size=12), text_color=TEXT2)
        self._en_switch.pack(anchor="w")

        # ── Export (hidden) ──────────────────────────────────────────────────
        self._export_sec = ctk.CTkFrame(self._left, fg_color="transparent")

        ctk.CTkLabel(self._export_sec, text="EXPORT",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT3).pack(anchor="w", pady=(0, 8))

        exp_row = ctk.CTkFrame(self._export_sec, fg_color="transparent")
        exp_row.pack(fill="x")
        ctk.CTkEntry(exp_row, textvariable=self._export_dir,
                     fg_color=CARD, border_color=BORDER, text_color=TEXT,
                     height=32, corner_radius=8).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(exp_row, text="Choose", width=60, height=32,
                       fg_color=CARD, hover_color=CARD2, border_width=1,
                       border_color=BORDER, text_color=TEXT2,
                       corner_radius=8, command=self._browse_export).pack(side="left", padx=(0, 4))
        ctk.CTkButton(exp_row, text="Desktop", width=65, height=32,
                       fg_color=CARD, hover_color=CARD2, border_width=1,
                       border_color=BORDER, text_color=TEXT2,
                       corner_radius=8, command=self._set_desktop).pack(side="left")

        self._preview_lbl = ctk.CTkLabel(self._export_sec, text="", text_color=TEXT3,
                                          font=ctk.CTkFont(size=10), anchor="w")
        self._preview_lbl.pack(anchor="w", pady=(6, 0))

        # ── Start ────────────────────────────────────────────────────────────
        self._start_sec = ctk.CTkFrame(self._left, fg_color="transparent")

        self._start_btn = ctk.CTkButton(self._start_sec, text="Start Transcription",
                                         height=44, corner_radius=10,
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         fg_color=WHITE, hover_color="#E0E0E0",
                                         text_color=BG, command=self._start)
        self._start_btn.pack(fill="x", pady=(0, 10))

        self._progress = ctk.CTkProgressBar(self._start_sec, height=3,
                                             corner_radius=2,
                                             progress_color=WHITE, fg_color=BORDER)
        self._progress.pack(fill="x")
        self._progress.set(0)

        self._status_lbl = ctk.CTkLabel(self._start_sec, text="",
                                         text_color=TEXT3, font=ctk.CTkFont(size=11))
        self._status_lbl.pack(anchor="w", pady=(6, 0))

        # Log
        self._log_text = ctk.CTkTextbox(self._start_sec, height=60,
                                         font=ctk.CTkFont(family="Menlo", size=10),
                                         fg_color=CARD, text_color=TEXT3,
                                         corner_radius=8, wrap="word",
                                         activate_scrollbars=False)
        self._log_text.pack(fill="x", pady=(6, 0))
        self._log_text.configure(state="disabled")

        # ── Right: Transcript ────────────────────────────────────────────────
        right_top = ctk.CTkFrame(self._right, fg_color="transparent")
        right_top.pack(fill="x", padx=24, pady=(24, 8))

        ctk.CTkLabel(right_top, text="TRANSCRIPT",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT3).pack(side="left")

        self._result_lbl = ctk.CTkLabel(right_top, text="", font=ctk.CTkFont(size=11),
                                         text_color=GREEN)
        self._result_lbl.pack(side="right")

        self._result_path_lbl = ctk.CTkLabel(self._right, text="", text_color=TEXT3,
                                              font=ctk.CTkFont(size=10), anchor="w")
        self._result_path_lbl.pack(padx=24, anchor="w")

        toolbar = ctk.CTkFrame(self._right, fg_color="transparent")
        toolbar.pack(fill="x", padx=24, pady=(8, 0))

        self._copy_btn = ctk.CTkButton(toolbar, text="Copy All", width=75, height=30,
                                        fg_color=CARD2, hover_color=BORDER,
                                        text_color=TEXT2, corner_radius=8,
                                        command=self._copy_all)
        self._copy_btn.pack(side="left", padx=(0, 4))
        ctk.CTkButton(toolbar, text="Open Folder", width=90, height=30,
                       fg_color=CARD2, hover_color=BORDER,
                       text_color=TEXT2, corner_radius=8,
                       command=self._open_folder).pack(side="left", padx=(0, 4))
        ctk.CTkButton(toolbar, text="Delete .txt", width=80, height=30,
                       fg_color=CARD2, hover_color="#3C1111",
                       text_color=RED, corner_radius=8,
                       command=self._delete_txt).pack(side="left")

        self._result_text = ctk.CTkTextbox(self._right,
                                            font=ctk.CTkFont(size=13),
                                            fg_color=CARD2, text_color=TEXT,
                                            corner_radius=10, wrap="word")
        self._result_text.pack(fill="both", expand=True, padx=24, pady=(10, 24))

        self._export_dir.trace_add("write", lambda *_: self._update_preview())

    # ─── Model ───────────────────────────────────────────────────────────────

    def _select_model(self, name):
        self._selected_model.set(name)
        for m, btn in self._model_btns.items():
            if m == name:
                btn.configure(fg_color=WHITE, text_color=BG, border_color=WHITE,
                              font=ctk.CTkFont(size=12, weight="bold"))
            else:
                btn.configure(fg_color=CARD, text_color=TEXT3, border_color=BORDER,
                              font=ctk.CTkFont(size=12))
        self._show_steps()

    def _show_steps(self):
        model = self._selected_model.get()

        self._en_sec.pack_forget()
        self._export_sec.pack_forget()
        self._start_sec.pack_forget()

        if model in EN_MODELS:
            self._en_sec.pack(fill="x", pady=(0, 16))
        else:
            self._en_opt.set(False)

        self._export_sec.pack(fill="x", pady=(0, 16))
        self._start_sec.pack(fill="x", pady=(0, 0))
        self._update_preview()
        self._resize_window(*SIZE_MODEL)

    # ─── Events ──────────────────────────────────────────────────────────────

    def _clear_file(self):
        self._file_path.set("")
        self._drop_lbl.configure(text="Drop audio file here, or click to browse",
                                  text_color=TEXT2)
        self._drop_icon.configure(text="↑", text_color=TEXT3)
        self._drop.configure(border_color=BORDER)
        if self._scan_frame.winfo_manager():
            self._scan_frame.pack_forget()
        self._update_preview()

    def _on_drop(self, event):
        path = event.data.strip()
        # Handle paths wrapped in braces (macOS/tkdnd)
        if path.startswith("{") and path.endswith("}"):
            path = path[1:-1]
        ext = os.path.splitext(path)[1].lower()
        if ext not in AUDIO_SUFFIXES:
            messagebox.showwarning("Unsupported", f"Not a supported audio format: {ext}")
            return
        self._file_path.set(path)
        self._drop_lbl.configure(text=os.path.basename(path), text_color=WHITE)
        self._drop_icon.configure(text="✓", text_color=GREEN)
        self._drop.configure(border_color=GREEN)
        self._update_preview()

    def _browse_file(self):
        filetypes = [("Audio files", " ".join(AUDIO_EXTS)), ("All files", "*.*")]
        path = filedialog.askopenfilename(initialdir=os.path.expanduser("~/Desktop"), filetypes=filetypes)
        if path:
            self._file_path.set(path)
            self._drop_lbl.configure(text=os.path.basename(path), text_color=WHITE)
            self._drop_icon.configure(text="✓", text_color=GREEN)
            self._drop.configure(border_color=GREEN)
            self._update_preview()

    def _scan_dir(self):
        found = []
        for ext in AUDIO_EXTS:
            found.extend(glob.glob(os.path.join(SCRIPT_DIR, ext)))
        if not found:
            messagebox.showinfo("Scan", "No audio files found")
            return
        names = [os.path.basename(f) for f in found]
        self._scan_paths = dict(zip(names, found))
        self._scan_menu.configure(values=names)
        self._scan_menu.set(names[0])
        self._file_path.set(found[0])
        self._drop_lbl.configure(text=names[0], text_color=WHITE)
        self._drop_icon.configure(text="✓", text_color=GREEN)
        self._drop.configure(border_color=GREEN)
        if not self._scan_frame.winfo_manager():
            self._scan_frame.pack(fill="x", pady=(0, 16), after=self._path_row)
            self._scan_menu.pack(fill="x")
        self._update_preview()

    def _on_scan_select(self, choice):
        path = getattr(self, "_scan_paths", {}).get(choice, "")
        if path:
            self._file_path.set(path)
            self._drop_lbl.configure(text=choice, text_color=WHITE)
            self._update_preview()

    def _set_desktop(self):
        self._export_dir.set(os.path.expanduser("~/Desktop"))

    def _browse_export(self):
        d = filedialog.askdirectory(initialdir=os.path.expanduser("~/Desktop"))
        if d:
            self._export_dir.set(d)

    def _update_preview(self):
        out_dir = self._export_dir.get().strip() or SCRIPT_DIR
        audio = self._file_path.get().strip()
        if audio:
            base = os.path.splitext(os.path.basename(audio))[0]
            preview = os.path.join(out_dir, f"{base}_transcript.txt")
        else:
            preview = os.path.join(out_dir, "<filename>_transcript.txt")
        self._preview_lbl.configure(text=preview)

    def _open_folder(self):
        subprocess.Popen(["open", self._export_dir.get().strip() or SCRIPT_DIR])

    def _log(self, msg):
        self._log_text.configure(state="normal")
        self._log_text.insert("end", msg + "\n")
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    # ─── Transcription ───────────────────────────────────────────────────────

    def _start(self):
        if self._start_btn.cget("text") == "Cancel":
            self._cancel_event.set()
            self._progress.set(0)
            self._status_lbl.configure(text="Cancelled", text_color=RED)
            self._start_btn.configure(text="Start Transcription",
                                       fg_color=WHITE, hover_color="#E0E0E0", text_color=BG)
            return

        path = self._file_path.get().strip()
        if not path:
            messagebox.showwarning("No File", "Select an audio file first")
            return
        if not os.path.exists(path):
            messagebox.showerror("Not Found", f"Cannot find: {path}")
            return
        if not self._selected_model.get():
            messagebox.showwarning("No Model", "Select a model first")
            return

        self._cancel_event.clear()
        self._run_id += 1
        # Drain any stale messages
        while not self._msg_queue.empty():
            try:
                self._msg_queue.get_nowait()
            except queue.Empty:
                break
        self._right.pack_forget()
        self._start_btn.configure(text="Cancel", fg_color=RED, hover_color="#B91C1C", text_color=WHITE)
        self._progress.set(0)
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.configure(state="disabled")
        self._status_lbl.configure(text="Loading model...", text_color=AMBER)
        threading.Thread(target=self._run, daemon=True).start()
        self._poll_queue()

    def _poll_queue(self):
        """Process up to 20 queued messages per tick, then reschedule."""
        for _ in range(20):
            try:
                kind, data = self._msg_queue.get_nowait()
            except queue.Empty:
                break
            if kind == "log":
                self._log(data)
            elif kind == "progress":
                self._progress.set(data)
            elif kind == "status":
                text, color = data
                self._status_lbl.configure(text=text, text_color=color)
            elif kind == "done":
                self._on_done(data)
                return
            elif kind == "error":
                self._on_error(data)
                return
        if self._start_btn.cget("text") == "Cancel":
            self.after(200, self._poll_queue)

    def _run(self):
        run_id = self._run_id
        q = self._msg_queue
        old_stdout, old_stderr = sys.stdout, sys.stderr
        try:
            model_name = self._selected_model.get()
            en_opt = self._en_opt.get()
            file_path = self._file_path.get().strip()

            if en_opt and model_name in EN_MODELS:
                model_name = f"{model_name}.en"
            language = "en" if en_opt else None

            # Load model
            if self._cached_model_name == model_name and self._cached_model is not None:
                q.put(("log", f"Using cached {model_name}"))
                model = self._cached_model
            else:
                q.put(("log", f"Loading {model_name}..."))
                t0 = time.time()
                sys.stderr = _StderrCapture(q)
                model = whisper.load_model(model_name)
                sys.stderr = old_stderr
                dt = time.time() - t0
                q.put(("log", f"Model ready ({dt:.1f}s)"))
                self._cached_model = model
                self._cached_model_name = model_name

            if self._cancel_event.is_set() or run_id != self._run_id:
                return

            # Pre-load audio and compute duration
            q.put(("status", ("Loading audio...", AMBER)))
            audio = whisper.load_audio(file_path)
            duration = len(audio) / whisper.audio.SAMPLE_RATE
            q.put(("log", f"Audio duration: {duration:.1f}s"))

            if self._cancel_event.is_set() or run_id != self._run_id:
                return

            # Transcribe with real progress
            q.put(("status", ("Transcribing...", AMBER)))
            q.put(("log", "Transcribing..."))
            t0 = time.time()

            sys.stdout = _StdoutCapture(q, duration)
            sys.stderr = _StderrCapture(q)
            result = model.transcribe(audio, task="transcribe",
                                       language=language, verbose=True)
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            dt = time.time() - t0

            if self._cancel_event.is_set() or run_id != self._run_id:
                return

            segs = len(result.get("segments", []))
            lang = result.get("language", "?")
            q.put(("log", f"Done — {segs} segments, {dt:.1f}s, lang={lang}"))
            q.put(("done", result["text"]))
        except Exception as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            q.put(("error", str(e)))

    def _on_done(self, text):
        self._start_btn.configure(text="Start Transcription",
                                   fg_color=WHITE, hover_color="#E0E0E0", text_color=BG)
        self._progress.set(1.0)
        self._status_lbl.configure(text="Complete", text_color=GREEN)

        out_dir = self._export_dir.get().strip() or SCRIPT_DIR
        base = os.path.splitext(os.path.basename(self._file_path.get()))[0]
        out_path = os.path.join(out_dir, f"{base}_transcript.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)

        self._output_path = out_path
        self._result_lbl.configure(text="Saved")
        self._result_path_lbl.configure(text=out_path)
        self._result_text.delete("1.0", "end")
        self._result_text.insert("1.0", text)

        if not self._right.winfo_manager():
            self._right.pack(side="left", fill="both", expand=True, padx=(0, 40), pady=40)
            self._resize_window(*SIZE_TRANSCRIPT)

    def _on_error(self, msg):
        self._start_btn.configure(text="Start Transcription",
                                   fg_color=WHITE, hover_color="#E0E0E0", text_color=BG)
        self._progress.set(0)
        self._status_lbl.configure(text="Error", text_color=RED)
        self._log(f"Error: {msg}")

    def _copy_all(self):
        content = self._result_text.get("1.0", "end").strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)
            self._copy_btn.configure(text="Copied!")
            self.after(1500, lambda: self._copy_btn.configure(text="Copy All"))

    def _delete_txt(self):
        out_dir = self._export_dir.get().strip() or SCRIPT_DIR
        txt_files = glob.glob(os.path.join(out_dir, "*_transcript.txt"))
        if not txt_files:
            messagebox.showinfo("No Files", f"No transcript files in:\n{out_dir}")
            return
        if not messagebox.askyesno("Confirm", f"Delete {len(txt_files)} transcript file(s)?"):
            return
        for f in txt_files:
            os.remove(f)
        self._status_lbl.configure(text=f"Deleted {len(txt_files)} transcript(s)", text_color=RED)


if __name__ == "__main__":
    app = WhisperApp()
    app.mainloop()
