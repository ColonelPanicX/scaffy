#!/usr/bin/env python3
"""
scaffy GUI — tkinter front-end for scaffy.py

Wraps scaffy's scaffold logic in a point-and-click interface.
Requires scaffy.py to be in the same directory (or bundled alongside by PyInstaller).
"""

from __future__ import annotations

import base64
import io
import os
import pathlib
import platform
import queue
import re
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk

import scaffy

# 16x16 house icon (ICO format, base64-encoded)
_HOUSE_ICON_B64 = (
    "AAABAAEAEBAAAAEAIABoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAQAQAAAAAAAAA"
    "AAAAAAAAAAAAAABktGT/ZLRk/2S0ZP9ktGT/ZLRk/2S0ZP9ktGT/ZLRk/2S0ZP9ktG"
    "T/ZLRk/2S0ZP9ktGT/ZLRk/2S0ZP9ktGT/ZLRk/2S0ZP9ktGT/ZLRk/2S0ZP9ktGT/"
    "ZLRk/2S0ZP9ktGT/ZLRk/2S0ZP9ktGT/ZLRk/2S0ZP9ktGT/ZLRk/wAAAAAAAAAAAAAA"
    "AADc3Ob/3Nzm/9zc5v9aeLT/Wni0/1p4tP9aeLT/3Nzm/9zc5v/c3Ob/AAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAc3Ob/3Nzm/9zc5v9aeLT/Wni0/1p4tP9aeLT/3Nzm/9zc"
    "5v/c3Ob/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA3Nzm/9zc5v/c3Ob/Wni0/1p4tP9a"
    "eLT/Wni0/9zc5v/c3Ob/3Nzm/wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANzc5v/c3Ob/"
    "3Nzm/1p4tP9aeLT/Wni0/1p4tP/c3Ob/3Nzm/9zc5v8AAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAANzc5v/c3Ob/3Nzm/9zc5v/c3Ob/3Nzm/9zc5v/c3Ob/3Nzm/9zc5v8AAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAA3Nzm/9zc5v/c3Ob/3Nzm/9zc5v/c3Ob/3Nzm/9zc5v/"
    "c3Ob/3Nzm/wAAAAAAAAAAAAAAAAAAAAA8UIz/PFCM/zxQjP88UIz/PFCM/zxQjP88UIz/"
    "PFCM/zxQjP88UIz/PFCM/zxQjP88UIz/PFCM/wAAAAAAAAAAAAAAADxQjP88UIz/PFCM"
    "/zxQjP88UIz/PFCM/zxQjP88UIz/PFCM/zxQjP88UIz/PFCM/wAAAAAAAAAAAAAAAAAA"
    "AAAAAAA8UIz/PFCM/zxQjP88UIz/PFCM/zxQjP88UIz/PFCM/zxQjP88UIz/AAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAADxQjP88UIz/PFCM/zxQjP88UIz/PFCM/zxQjP88UIz/"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPFCM/zxQjP88UIz/PFCM/zxQjP"
    "88UIz/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPFCM/zxQjP88"
    "UIz/PFCM/wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "PFCM/zxQjP8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAA=="
)

WINDOWS_RESERVED_NAMES = frozenset({
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
})
INVALID_FOLDER_CHARS = re.compile(r'[\\/:*?"<>|]')


def _valid_folder_name(name: str) -> str | None:
    """Return an error message if *name* is invalid as a folder name, else None."""
    if not name or not name.strip():
        return "Project name cannot be empty."
    if INVALID_FOLDER_CHARS.search(name):
        return 'Name cannot contain \\ / : * ? " < > |'
    if name.upper() in WINDOWS_RESERVED_NAMES:
        return f'"{name}" is a reserved Windows name.'
    if name.endswith(" ") or name.endswith("."):
        return "Name cannot end with a space or period."
    return None


def _default_path() -> str:
    """Return a sensible default target path for the current platform."""
    return str(pathlib.Path.home())


GOVERNANCE_OPTIONS = ["None", "Lightweight", "Standard", "Strict"]
PLATFORM_OPTIONS = ["None", "GitHub", "GitLab"]
LICENSE_OPTIONS = [
    "None", "MIT", "Apache-2.0", "GPL-3.0", "AGPL-3.0",
    "BSD-2-Clause", "BSD-3-Clause", "MPL-2.0", "Unlicense",
]

TOOLTIPS = {
    "mode": "New: creates a project folder inside the target path.\n"
            "Existing: installs .collab/ into an existing project folder.\n"
            "Upgrade: updates an existing .collab/ to the latest templates.",
    "name": "The name for your new project folder.\n"
            'Cannot contain \\ / : * ? " < > |',
    "path_new": "Parent directory where your new project folder will be created.",
    "path_existing": "Root directory of the existing project to scaffold into.",
    "path_upgrade": "Root directory of the project with an existing .collab/ to upgrade.",
    "description": "A short summary injected into the project context file.",
    "platform": "Git hosting platform. Generates issue/PR templates\n"
                "for the selected platform, or None to skip.",
    "governance": "Controls how much process structure is scaffolded.\n"
                  "None: no governance rules.\n"
                  "Lightweight: minimal guardrails.\n"
                  "Standard: kanban, contracts, session logging.\n"
                  "Strict: full audit trail and review gates.",
    "license": "Adds a LICENSE file to the project root.\n"
               "See the scaffy README for license details.",
    "init_git": "Runs 'git init' in the project root after scaffolding.\n"
                "Skip this if the project already has a git repo.",
    "force": "Overwrite existing scaffold files if they already exist.\n"
             "Without this, existing files are left untouched.",
    "open_folder": "Open the project folder in your file explorer\n"
                   "after a successful build.",
}


class Tooltip:
    """Hover tooltip for any tkinter widget."""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self._widget = widget
        self._text = text
        self._tip_window: tk.Toplevel | None = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _event: tk.Event) -> None:
        if self._tip_window:
            return
        x = self._widget.winfo_rootx() + 20
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._tip_window = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=self._text, justify="left",
            background="#ffffe0", foreground="#333",
            relief="solid", borderwidth=1,
            font=("TkDefaultFont", 9), padx=6, pady=4,
        )
        label.pack()

    def _hide(self, _event: tk.Event) -> None:
        if self._tip_window:
            self._tip_window.destroy()
            self._tip_window = None


def _help_label(parent: ttk.Frame, row: int, col: int, tip_text: str) -> tk.Label:
    """Place a small '?' label with a hover tooltip."""
    lbl = tk.Label(
        parent, text="?", font=("TkDefaultFont", 9, "bold"),
        foreground="#555", cursor="question_arrow",
    )
    lbl.grid(row=row, column=col, sticky="w", padx=(4, 0))
    Tooltip(lbl, tip_text)
    return lbl


class QueueWriter(io.TextIOBase):
    """Redirects write() calls into a queue for thread-safe GUI updates."""

    def __init__(self, q: queue.Queue) -> None:
        self._q = q

    def write(self, text: str) -> int:
        if text:
            self._q.put(text)
        return len(text)

    def flush(self) -> None:
        pass


def _open_folder(path: str) -> None:
    """Open a folder in the platform's native file explorer."""
    system = platform.system()
    if system == "Windows":
        os.startfile(path)
    elif system == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


class ScaffyApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("scaffy")
        self.resizable(True, True)
        self.minsize(620, 580)
        self._set_icon()

        self._output_queue: queue.Queue = queue.Queue()
        self._running = False
        self._target_root: str | None = None

        self._build_ui()
        self._poll_output()

    def _set_icon(self) -> None:
        """Set the window icon from the embedded ICO data."""
        try:
            ico_data = base64.b64decode(_HOUSE_ICON_B64)
            # Write to a temp file — tkinter needs a file path for iconbitmap
            tmp = tempfile.NamedTemporaryFile(suffix=".ico", delete=False)
            tmp.write(ico_data)
            tmp.close()
            self.iconbitmap(tmp.name)
            os.unlink(tmp.name)
        except Exception:
            pass  # Fall back to default icon silently

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root_frame = ttk.Frame(self, padding=12)
        root_frame.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        root_frame.columnconfigure(1, weight=1)

        row = 0

        # ── Section: Project Setup ────────────────────────────────────
        ttk.Label(root_frame, text="Project Setup", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=4, sticky="w", pady=(0, 4)
        )
        row += 1

        # Mode toggle
        ttk.Label(root_frame, text="Mode").grid(row=row, column=0, sticky="w", pady=2)
        mode_frame = ttk.Frame(root_frame)
        mode_frame.grid(row=row, column=1, columnspan=2, sticky="w", padx=(8, 0))
        self._mode_var = tk.StringVar(value="new")
        ttk.Radiobutton(
            mode_frame, text="New project", variable=self._mode_var,
            value="new", command=self._on_mode_change,
        ).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(
            mode_frame, text="Existing project", variable=self._mode_var,
            value="existing", command=self._on_mode_change,
        ).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(
            mode_frame, text="Upgrade scaffold", variable=self._mode_var,
            value="upgrade", command=self._on_mode_change,
        ).pack(side="left")
        _help_label(root_frame, row, 3, TOOLTIPS["mode"])
        row += 1

        # Project Name
        self._name_label = ttk.Label(root_frame, text="Project Name")
        self._name_label.grid(row=row, column=0, sticky="w", pady=2)
        self._name_var = tk.StringVar()
        self._name_entry = ttk.Entry(root_frame, textvariable=self._name_var)
        self._name_entry.grid(row=row, column=1, columnspan=2, sticky="ew", padx=(8, 0))
        _help_label(root_frame, row, 3, TOOLTIPS["name"])
        row += 1

        # Target Path
        self._path_label = ttk.Label(root_frame, text="Target Path")
        self._path_label.grid(row=row, column=0, sticky="w", pady=2)
        self._path_var = tk.StringVar(value=_default_path())
        ttk.Entry(root_frame, textvariable=self._path_var).grid(
            row=row, column=1, sticky="ew", padx=(8, 4)
        )
        ttk.Button(root_frame, text="Browse\u2026", command=self._browse_path).grid(
            row=row, column=2, sticky="ew"
        )
        self._path_help = _help_label(root_frame, row, 3, TOOLTIPS["path_new"])
        row += 1

        # Description
        ttk.Label(root_frame, text="Description").grid(row=row, column=0, sticky="w", pady=2)
        self._desc_var = tk.StringVar()
        ttk.Entry(root_frame, textvariable=self._desc_var).grid(
            row=row, column=1, columnspan=2, sticky="ew", padx=(8, 0)
        )
        _help_label(root_frame, row, 3, TOOLTIPS["description"])
        row += 1

        ttk.Separator(root_frame, orient="horizontal").grid(
            row=row, column=0, columnspan=4, sticky="ew", pady=8
        )
        row += 1

        # ── Section: Options ─────────────────────────────────────────
        ttk.Label(root_frame, text="Options", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=4, sticky="w", pady=(0, 4)
        )
        row += 1

        # Platform (first — drives auto-fill)
        ttk.Label(root_frame, text="Platform").grid(row=row, column=0, sticky="w", pady=2)
        self._platform_var = tk.StringVar(value="None")
        self._platform_combo = ttk.Combobox(
            root_frame, textvariable=self._platform_var,
            values=PLATFORM_OPTIONS, state="readonly", width=20,
        )
        self._platform_combo.grid(row=row, column=1, sticky="w", padx=(8, 0))
        self._platform_combo.bind("<<ComboboxSelected>>", self._on_platform_change)
        _help_label(root_frame, row, 3, TOOLTIPS["platform"])
        row += 1

        # Governance
        ttk.Label(root_frame, text="Governance").grid(row=row, column=0, sticky="w", pady=2)
        self._governance_var = tk.StringVar(value="Standard")
        self._governance_combo = ttk.Combobox(
            root_frame, textvariable=self._governance_var,
            values=GOVERNANCE_OPTIONS, state="readonly", width=20,
        )
        self._governance_combo.grid(row=row, column=1, sticky="w", padx=(8, 0))
        _help_label(root_frame, row, 3, TOOLTIPS["governance"])
        row += 1

        # License
        ttk.Label(root_frame, text="License").grid(row=row, column=0, sticky="w", pady=2)
        self._license_var = tk.StringVar(value="None")
        self._license_combo = ttk.Combobox(
            root_frame, textvariable=self._license_var,
            values=LICENSE_OPTIONS, state="readonly", width=20,
        )
        self._license_combo.grid(row=row, column=1, sticky="w", padx=(8, 0))
        _help_label(root_frame, row, 3, TOOLTIPS["license"])
        row += 1

        ttk.Separator(root_frame, orient="horizontal").grid(
            row=row, column=0, columnspan=4, sticky="ew", pady=8
        )
        row += 1

        # ── Section: Flags ───────────────────────────────────────────
        flag_frame = ttk.Frame(root_frame)
        flag_frame.grid(row=row, column=0, columnspan=4, sticky="w")

        self._init_git_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            flag_frame, text="Initialize git repo", variable=self._init_git_var
        ).pack(side="left")
        git_help = tk.Label(
            flag_frame, text="?", font=("TkDefaultFont", 9, "bold"),
            foreground="#555", cursor="question_arrow",
        )
        git_help.pack(side="left", padx=(4, 16))
        Tooltip(git_help, TOOLTIPS["init_git"])

        self._force_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            flag_frame, text="Force overwrite", variable=self._force_var
        ).pack(side="left")
        force_help = tk.Label(
            flag_frame, text="?", font=("TkDefaultFont", 9, "bold"),
            foreground="#555", cursor="question_arrow",
        )
        force_help.pack(side="left", padx=(4, 16))
        Tooltip(force_help, TOOLTIPS["force"])

        self._open_folder_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            flag_frame, text="Open folder after build", variable=self._open_folder_var
        ).pack(side="left")
        open_help = tk.Label(
            flag_frame, text="?", font=("TkDefaultFont", 9, "bold"),
            foreground="#555", cursor="question_arrow",
        )
        open_help.pack(side="left", padx=(4, 0))
        Tooltip(open_help, TOOLTIPS["open_folder"])
        row += 1

        ttk.Separator(root_frame, orient="horizontal").grid(
            row=row, column=0, columnspan=4, sticky="ew", pady=8
        )
        row += 1

        # ── Build button ─────────────────────────────────────────────
        self._run_btn = ttk.Button(root_frame, text="Build!", command=self._on_scaffold)
        self._run_btn.grid(row=row, column=0, columnspan=4, sticky="ew", ipady=4)
        row += 1

        ttk.Label(root_frame, text="Output", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=4, sticky="w", pady=(12, 4)
        )
        row += 1

        # ── Output panel ─────────────────────────────────────────────
        self._output = scrolledtext.ScrolledText(
            root_frame, height=12, state="disabled",
            wrap="word", font=("Courier New", 9),
        )
        self._output.grid(row=row, column=0, columnspan=4, sticky="nsew")
        root_frame.rowconfigure(row, weight=1)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_mode_change(self) -> None:
        mode = self._mode_var.get()
        is_new = mode == "new"
        is_upgrade = mode == "upgrade"

        self._name_entry.configure(state="normal" if is_new else "disabled")
        if not is_new:
            self._name_var.set("")

        # Disable options that upgrade reads from project.yaml
        option_state = "disabled" if is_upgrade else "readonly"
        self._platform_combo.configure(state=option_state)
        self._governance_combo.configure(state=option_state)
        self._license_combo.configure(state=option_state)

        # Update button label
        self._run_btn.configure(text="Upgrade!" if is_upgrade else "Build!")

        # Swap path tooltip
        tip_key = "path_new" if is_new else ("path_upgrade" if is_upgrade else "path_existing")
        self._path_help.unbind("<Enter>")
        self._path_help.unbind("<Leave>")
        Tooltip(self._path_help, TOOLTIPS[tip_key])

    def _on_platform_change(self, _event: tk.Event) -> None:
        if self._platform_var.get() == "None":
            self._governance_var.set("None")
            self._license_var.set("None")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _browse_path(self) -> None:
        chosen = filedialog.askdirectory(title="Select target directory")
        if chosen:
            self._path_var.set(chosen)

    def _on_scaffold(self) -> None:
        if self._running:
            return

        mode = self._mode_var.get()
        path = self._path_var.get().strip()

        if not path:
            self._append_output("Error: Target Path is required.\n")
            return

        # --- Upgrade mode ---
        if mode == "upgrade":
            target = os.path.normpath(path)
            self._target_root = target
            collab_dir = os.path.join(target, ".collab")
            if not os.path.isdir(collab_dir):
                self._append_output(
                    f"Error: No .collab/ directory found in {target}\n"
                    "Select a project that has already been scaffolded.\n"
                )
                return

            args = ["--upgrade", "--path", target]
            if self._force_var.get():
                args.append("--force")

            # Capture dry-run preview
            preview = self._capture_dry_run(args + ["--dry-run"])
            self._show_confirm_popup(preview, args)
            return

        # --- New / Existing mode ---
        if mode == "new":
            name = self._name_var.get().strip()
            if not name:
                self._append_output("Error: Project Name is required for new projects.\n")
                return
            err = _valid_folder_name(name)
            if err:
                self._append_output(f"Error: {err}\n")
                return
        else:
            name = os.path.basename(os.path.normpath(path))

        # Resolve the target root so we can open it after build
        if mode == "new":
            self._target_root = os.path.join(os.path.normpath(path), name)
        else:
            self._target_root = os.path.normpath(path)

        args = [
            "--name", name,
            "--path", path if mode == "new" else os.path.dirname(os.path.normpath(path)),
            "--governance", self._governance_var.get().lower(),
            "--platform", self._platform_var.get().lower(),
            "--license", self._license_var.get().lower(),
        ]
        if self._desc_var.get().strip():
            args += ["--description", self._desc_var.get().strip()]
        if self._init_git_var.get():
            args.append("--init-git")
        if self._force_var.get():
            args.append("--force")

        preview = self._capture_dry_run(args + ["--dry-run"])
        self._show_confirm_popup(preview, args)

    def _capture_dry_run(self, dry_args: list[str]) -> str:
        """Run scaffy with the given args and capture stdout."""
        old_stdout, old_stderr, old_argv = sys.stdout, sys.stderr, sys.argv
        capture = io.StringIO()
        sys.stdout = capture
        sys.stderr = capture
        sys.argv = ["scaffy"] + dry_args
        try:
            scaffy.main()
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            sys.argv = old_argv
        # Strip the trailing "Dry run complete" line — not needed in the GUI preview
        text = capture.getvalue()
        lines = text.rstrip().splitlines()
        if lines and "dry run complete" in lines[-1].lower():
            lines.pop()
        return "\n".join(lines) + "\n" if lines else text

    def _show_confirm_popup(self, preview: str, args: list[str]) -> None:
        """Show a preview of planned actions and ask for confirmation."""
        popup = tk.Toplevel(self)
        popup.title("Confirm Build")
        popup.minsize(520, 380)
        popup.transient(self)
        popup.grab_set()

        frame = ttk.Frame(popup, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame, text="The following files and directories will be created:",
            font=("", 10, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        text_widget = scrolledtext.ScrolledText(
            frame, wrap="word", font=("Courier New", 9), height=16,
        )
        text_widget.pack(fill="both", expand=True)
        text_widget.insert("1.0", preview)
        text_widget.configure(state="disabled")

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(12, 0))

        def on_confirm() -> None:
            popup.destroy()
            self._clear_output()
            self._set_running(True)
            thread = threading.Thread(
                target=self._run_scaffy, args=(args,), daemon=True,
            )
            thread.start()

        is_upgrade = "--upgrade" in args
        confirm_text = "Yes, Upgrade!" if is_upgrade else "Yes, Build!"
        ttk.Button(btn_frame, text="No", command=popup.destroy).pack(side="left")
        build_btn = ttk.Button(btn_frame, text=confirm_text, command=on_confirm)
        build_btn.pack(side="right")
        build_btn.focus_set()

    def _run_scaffy(self, args: list[str]) -> None:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_argv = sys.argv

        writer = QueueWriter(self._output_queue)
        sys.stdout = writer
        sys.stderr = writer
        sys.argv = ["scaffy"] + args

        try:
            scaffy.main()
            self._output_queue.put(("__done__", True))
        except SystemExit:
            self._output_queue.put(("__done__", False))
        except Exception as exc:
            self._output_queue.put(f"\nUnexpected error: {exc}\n")
            self._output_queue.put(("__done__", False))
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            sys.argv = old_argv

    # ------------------------------------------------------------------
    # Post-build actions
    # ------------------------------------------------------------------

    def _on_build_complete(self, success: bool) -> None:
        self._set_running(False)

        if not success or not self._target_root:
            return

        if self._open_folder_var.get() and os.path.isdir(self._target_root):
            _open_folder(self._target_root)

        # Show initial prompt popup
        prompt_path = os.path.join(self._target_root, ".collab", "initial-prompt.md")
        if os.path.isfile(prompt_path):
            with open(prompt_path, encoding="utf-8") as f:
                prompt_text = f.read()
            self._show_prompt_popup(prompt_text)

    def _show_prompt_popup(self, text: str) -> None:
        popup = tk.Toplevel(self)
        popup.title("Initial Prompt")
        popup.minsize(500, 350)
        popup.transient(self)

        frame = ttk.Frame(popup, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="Paste this into your AI agent to start your first session:",
            wraplength=460,
        ).pack(anchor="w", pady=(0, 8))

        text_widget = scrolledtext.ScrolledText(
            frame, wrap="word", font=("Courier New", 9),
        )
        text_widget.pack(fill="both", expand=True)
        text_widget.insert("1.0", text)
        text_widget.configure(state="disabled")

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(8, 0))

        def copy_to_clipboard() -> None:
            self.clipboard_clear()
            self.clipboard_append(text)
            copy_btn.configure(text="Copied!")
            self.after(1500, lambda: copy_btn.configure(text="Copy to Clipboard"))

        copy_btn = ttk.Button(btn_frame, text="Copy to Clipboard", command=copy_to_clipboard)
        copy_btn.pack(side="left")
        ttk.Button(btn_frame, text="Close", command=popup.destroy).pack(side="right")

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------

    def _poll_output(self) -> None:
        """Called every 50ms to drain the output queue into the text widget."""
        try:
            while True:
                item = self._output_queue.get_nowait()
                if isinstance(item, tuple) and item[0] == "__done__":
                    self._on_build_complete(item[1])
                else:
                    self._append_output(item)
        except queue.Empty:
            pass
        self.after(50, self._poll_output)

    def _append_output(self, text: str) -> None:
        self._output.configure(state="normal")
        self._output.insert("end", text)
        self._output.see("end")
        self._output.configure(state="disabled")

    def _clear_output(self) -> None:
        self._output.configure(state="normal")
        self._output.delete("1.0", "end")
        self._output.configure(state="disabled")

    def _set_running(self, running: bool) -> None:
        self._running = running
        is_upgrade = self._mode_var.get() == "upgrade"
        idle_text = "Upgrade!" if is_upgrade else "Build!"
        self._run_btn.configure(
            state="disabled" if running else "normal",
            text="Running\u2026" if running else idle_text,
        )


def main() -> None:
    app = ScaffyApp()
    app.mainloop()


if __name__ == "__main__":
    main()
