from __future__ import annotations

import os
import threading
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from .cli import _hash_pair
from .comparison import ComparisonResult
from .config import API_KEY_ENV_VAR, get_api_key
from .gemini_client import GeminiComparisonClient
from .history_db import HistoryRepository
from .secret_store import save_api_key

ALERT_COLORS = {
    "green": "#1b5e20",
    "yellow": "#f9a825",
    "red": "#c62828",
}


class DegreeCompareGUI:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Degree Comparator")
        self.root.geometry("820x600")
        self.root.minsize(760, 520)
        self.root.configure(padx=18, pady=18)
        self.repo = HistoryRepository()
        self.client: GeminiComparisonClient | None = None
        self.history_cache: dict[str, ComparisonResult] = {}

        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass  # fall back to platform default if clam is unavailable
        self.style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        self.style.configure("Subtitle.TLabel", font=("Segoe UI", 11))
        self.style.configure("Status.TLabel", font=("Segoe UI", 11, "bold"))
        self.style.configure("Results.TLabel", font=("Segoe UI", 12, "bold"))

        self.url_a_var = tk.StringVar()
        self.url_b_var = tk.StringVar()
        self.view_mode_var = tk.StringVar(value="Degree comparison")

        self._build_widgets()
        self._refresh_history()

    def _build_widgets(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        padding = {"padx": 10, "pady": 8}

        header = ttk.Label(self.root, text="Degree Comparison Studio", style="Title.TLabel")
        header.grid(row=0, column=0, columnspan=2, sticky="w")
        subtitle = ttk.Label(
            self.root,
            text="Compare Finnish higher-education degree descriptions side-by-side",
            style="Subtitle.TLabel",
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 14))

        mode_frame = ttk.Frame(self.root)
        mode_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        mode_frame.columnconfigure(1, weight=0)
        ttk.Label(mode_frame, text="View mode").grid(row=0, column=0, sticky="w", padx=(10, 8))
        self.view_mode_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.view_mode_var,
            values=("Degree comparison", "Curriculum comparison"),
            state="readonly",
            width=24,
        )
        self.view_mode_combo.grid(row=0, column=1, sticky="w")
        self.view_mode_combo.bind("<<ComboboxSelected>>", self._on_view_mode_changed)

        input_frame = ttk.LabelFrame(self.root, text="Degree URLs")
        input_frame.grid(row=3, column=0, columnspan=2, sticky="ew", **padding)
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="URL A").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))
        ttk.Entry(input_frame, textvariable=self.url_a_var).grid(row=0, column=1, sticky="ew", padx=10, pady=(10, 4))

        ttk.Label(input_frame, text="URL B").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 12))
        ttk.Entry(input_frame, textvariable=self.url_b_var).grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 12))

        action_frame = ttk.Frame(self.root)
        action_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(4, 4))
        action_frame.columnconfigure(0, weight=0)
        action_frame.columnconfigure(1, weight=1)
        self.status_label = ttk.Label(action_frame, text="Ready", style="Status.TLabel", foreground="#444444")
        self.status_label.grid(row=0, column=0, sticky="w")
        self.compare_button = ttk.Button(action_frame, text="Compare", command=self._on_compare)
        self.compare_button.grid(row=0, column=2, sticky="e")
        self.change_key_button = ttk.Button(action_frame, text="Change API key", command=self._on_change_api_key)
        self.change_key_button.grid(row=0, column=3, sticky="e", padx=(8, 0))

        ttk.Label(self.root, text="Comparison Results", style="Results.TLabel").grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(8, 4)
        )
        self.results_box = tk.Text(
            self.root,
            height=18,
            width=100,
            state="disabled",
            relief="flat",
            highlightthickness=1,
            highlightcolor="#cccccc",
            highlightbackground="#cccccc",
            font=("Consolas", 10),
        )
        self.results_box.tag_configure("diff_status", foreground="#c62828", font=("Consolas", 10, "bold"))
        self.results_box.grid(row=6, column=0, columnspan=2, sticky="nsew")
        self.root.rowconfigure(6, weight=2)

        history_frame = ttk.LabelFrame(self.root, text="Previous Comparisons")
        history_frame.grid(row=7, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)

        columns = ("urls", "alert", "timestamp")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=6)
        self.history_tree.heading("urls", text="URL Pair")
        self.history_tree.heading("alert", text="Alert")
        self.history_tree.heading("timestamp", text="Last Compared")
        self.history_tree.column("urls", width=420, anchor="w")
        self.history_tree.column("alert", width=80, anchor="center")
        self.history_tree.column("timestamp", width=140, anchor="center")
        self.history_tree.bind("<<TreeviewSelect>>", self._on_history_select)
        self.history_tree.grid(row=0, column=0, sticky="nsew", padx=(6, 0), pady=6)

        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=6, padx=(0, 6))
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        self.root.rowconfigure(7, weight=1)

    def _ensure_client(self) -> GeminiComparisonClient:
        if not self.client:
            api_key = self._get_or_prompt_api_key()
            if not api_key:
                raise RuntimeError("A Gemini API key is required to run comparisons.")
            self.client = GeminiComparisonClient(api_key=api_key)
        return self.client

    def _on_compare(self) -> None:
        url_a = self.url_a_var.get().strip()
        url_b = self.url_b_var.get().strip()
        if not url_a or not url_b:
            messagebox.showwarning("Missing data", "Both URLs are required.")
            return
        self.compare_button.config(state="disabled")
        self.status_label.config(text="Comparing...", foreground="#333333")
        try:
            self._ensure_client()
        except RuntimeError as exc:
            messagebox.showerror("Configuration", str(exc))
            self.compare_button.config(state="normal")
            self.status_label.config(text="Ready", foreground="#444444")
            return
        threading.Thread(target=self._compare_async, args=(url_a, url_b), daemon=True).start()

    def _compare_async(self, url_a: str, url_b: str) -> None:
        try:
            focus = self._current_focus()
            url_hash = f"{_hash_pair(url_a, url_b)}::{focus}"
            cached = self.repo.fetch(url_hash)
            if cached:
                payload = cached.comparison_json
            else:
                client = self._ensure_client()
                payload = client.compare(url_a, url_b, focus=focus)
                result = ComparisonResult.from_raw_json(payload)
                self.repo.save(url_hash, payload, alert_count=result.alert_count)
            result = ComparisonResult.from_raw_json(payload)
            self.root.after(0, self._render_result, result)
            self.root.after(0, self._refresh_history)
        except RuntimeError as runtime_exc:
            self.root.after(0, lambda: messagebox.showerror("Configuration", str(runtime_exc)))
        except Exception as generic_exc:
            self.root.after(0, lambda: messagebox.showerror("Error", str(generic_exc)))
        finally:
            self.root.after(0, lambda: self.compare_button.config(state="normal"))

    def _render_result(self, result: ComparisonResult) -> None:
        if self.view_mode_var.get() == "Curriculum comparison":
            self._render_curriculum_result(result)
            return

        color = ALERT_COLORS.get(result.alert_level, "#333333")
        self.status_label.config(text=result.alert_message, foreground=color)

        self.results_box.config(state="normal")
        self.results_box.delete("1.0", tk.END)
        for field in result.fields:
            self.results_box.insert(tk.END, f"{field.label}: ")
            if field.status == "DIFF":
                self.results_box.insert(tk.END, field.status, "diff_status")
            else:
                self.results_box.insert(tk.END, field.status)
            self.results_box.insert(tk.END, "\n")
            self.results_box.insert(tk.END, f"A: {field.value_a or 'n/a'}\n")
            self.results_box.insert(tk.END, f"B: {field.value_b or 'n/a'}\n")
            if field.explanation:
                self.results_box.insert(tk.END, f"Reason: {field.explanation}\n")
            self.results_box.insert(tk.END, "\n")
        self.results_box.config(state="disabled")

    def _render_curriculum_result(self, result: ComparisonResult) -> None:
        curriculum_field = next((field for field in result.fields if field.key == "opetussuunnitelma"), None)
        if curriculum_field and curriculum_field.status == "DIFF":
            self.status_label.config(text="Curriculum differences detected.", foreground=ALERT_COLORS["red"])
        elif curriculum_field and curriculum_field.status == "MATCH":
            self.status_label.config(text="Curriculums match semantically.", foreground=ALERT_COLORS["green"])
        else:
            self.status_label.config(text="No curriculum data found in this comparison.", foreground="#444444")

        self.results_box.config(state="normal")
        self.results_box.delete("1.0", tk.END)
        self.results_box.insert(tk.END, "Curriculum Comparison View\n")
        self.results_box.insert(tk.END, "=" * 30 + "\n\n")
        self.results_box.insert(tk.END, f"URL A: {result.url_a}\n")
        self.results_box.insert(tk.END, f"URL B: {result.url_b}\n\n")

        if not curriculum_field:
            self.results_box.insert(
                tk.END,
                "The current cached result does not include the opetussuunnitelma field.\n"
                "Run a fresh comparison to regenerate data.",
            )
            self.results_box.config(state="disabled")
            return

        self.results_box.insert(tk.END, "Status: ")
        if curriculum_field.status == "DIFF":
            self.results_box.insert(tk.END, curriculum_field.status, "diff_status")
        else:
            self.results_box.insert(tk.END, curriculum_field.status)
        self.results_box.insert(tk.END, "\n\n")

        self.results_box.insert(tk.END, "Curriculum A\n")
        self.results_box.insert(tk.END, "-" * 12 + "\n")
        self.results_box.insert(tk.END, f"{curriculum_field.value_a or 'n/a'}\n\n")

        self.results_box.insert(tk.END, "Curriculum B\n")
        self.results_box.insert(tk.END, "-" * 12 + "\n")
        self.results_box.insert(tk.END, f"{curriculum_field.value_b or 'n/a'}\n\n")

        if curriculum_field.explanation:
            self.results_box.insert(tk.END, "Difference summary\n")
            self.results_box.insert(tk.END, "-" * 18 + "\n")
            self.results_box.insert(tk.END, f"{curriculum_field.explanation}\n")

        self.results_box.config(state="disabled")

    def _refresh_history(self) -> None:
        if not hasattr(self, "history_tree"):
            return
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        self.history_cache.clear()

        for record in self.repo.list_recent():
            result = ComparisonResult.from_raw_json(record.comparison_json)
            mode_prefix = "[CURR] " if self._is_curriculum_only_result(result) else ""
            pair_label = f"{mode_prefix}{self._shorten_url(result.url_a)} ↔ {self._shorten_url(result.url_b)}"
            alert = result.alert_level.upper()
            timestamp = self._format_timestamp(record.timestamp)
            item_id = self.history_tree.insert("", "end", values=(pair_label, alert, timestamp))
            self.history_cache[item_id] = result

    def _on_history_select(self, _event: object | None = None) -> None:
        selection = self.history_tree.selection()
        if not selection:
            return
        item_id = selection[0]
        result = self.history_cache.get(item_id)
        if result:
            self._render_result(result)

    def _on_view_mode_changed(self, _event: object | None = None) -> None:
        selection = self.history_tree.selection()
        if selection:
            selected_result = self.history_cache.get(selection[0])
            if selected_result:
                self._render_result(selected_result)

    def _current_focus(self) -> str:
        if self.view_mode_var.get() == "Curriculum comparison":
            return "curriculum"
        return "full"

    @staticmethod
    def _is_curriculum_only_result(result: ComparisonResult) -> bool:
        return len(result.fields) == 1 and result.fields[0].key == "opetussuunnitelma"

    def _on_change_api_key(self) -> None:
        new_key = self._prompt_for_api_key()
        if new_key:
            self.client = None
            messagebox.showinfo("API key updated", "Future comparisons will use the new Gemini API key.")

    def _get_or_prompt_api_key(self) -> str | None:
        try:
            return get_api_key()
        except RuntimeError:
            return self._prompt_for_api_key()

    def _prompt_for_api_key(self) -> str | None:
        prompt_text = (
            "Enter the Gemini API key provided by your administrator. The key is stored only on this device."
        )
        while True:
            api_key = simpledialog.askstring(
                "Set Gemini API key",
                prompt_text,
                parent=self.root,
                show="*",
            )
            if api_key is None:
                return None
            api_key = api_key.strip()
            if not api_key:
                messagebox.showwarning("Missing key", "The API key cannot be empty.")
                continue
            try:
                save_api_key(api_key)
            except ValueError:
                messagebox.showwarning("Invalid key", "Provide a non-empty API key.")
                continue
            os.environ[API_KEY_ENV_VAR] = api_key
            return api_key

    @staticmethod
    def _shorten_url(url: str, max_length: int = 60) -> str:
        if len(url) <= max_length:
            return url
        return url[: max_length - 3] + "..."

    @staticmethod
    def _format_timestamp(timestamp: str) -> str:
        try:
            dt = datetime.fromisoformat(timestamp)
        except ValueError:
            return timestamp
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")

    def run(self) -> None:
        self.root.mainloop()


def launch_gui() -> None:
    DegreeCompareGUI().run()


if __name__ == "__main__":
    launch_gui()
