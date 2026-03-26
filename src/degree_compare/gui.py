from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from .cli import _hash_pair
from .comparison import ComparisonResult
from .config import get_api_key
from .gemini_client import GeminiComparisonClient
from .history_db import HistoryRepository

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

        self._build_widgets()

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

        input_frame = ttk.LabelFrame(self.root, text="Degree URLs")
        input_frame.grid(row=2, column=0, columnspan=2, sticky="ew", **padding)
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="URL A").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))
        ttk.Entry(input_frame, textvariable=self.url_a_var).grid(row=0, column=1, sticky="ew", padx=10, pady=(10, 4))

        ttk.Label(input_frame, text="URL B").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 12))
        ttk.Entry(input_frame, textvariable=self.url_b_var).grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 12))

        action_frame = ttk.Frame(self.root)
        action_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(4, 4))
        action_frame.columnconfigure(0, weight=1)
        self.status_label = ttk.Label(action_frame, text="Ready", style="Status.TLabel", foreground="#444444")
        self.status_label.grid(row=0, column=0, sticky="w")
        self.compare_button = ttk.Button(action_frame, text="Compare", command=self._on_compare)
        self.compare_button.grid(row=0, column=1, sticky="e")

        ttk.Label(self.root, text="Comparison Results", style="Results.TLabel").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(8, 4)
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
        self.results_box.grid(row=5, column=0, columnspan=2, sticky="nsew")
        self.root.rowconfigure(5, weight=1)

    def _ensure_client(self) -> GeminiComparisonClient:
        if not self.client:
            api_key = get_api_key()
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
        threading.Thread(target=self._compare_async, args=(url_a, url_b), daemon=True).start()

    def _compare_async(self, url_a: str, url_b: str) -> None:
        try:
            url_hash = _hash_pair(url_a, url_b)
            cached = self.repo.fetch(url_hash)
            if cached:
                payload = cached.comparison_json
            else:
                client = self._ensure_client()
                payload = client.compare(url_a, url_b)
                result = ComparisonResult.from_raw_json(payload)
                self.repo.save(url_hash, payload, alert_count=result.alert_count)
            result = ComparisonResult.from_raw_json(payload)
            self.root.after(0, self._render_result, result)
        except RuntimeError as runtime_exc:
            self.root.after(0, lambda: messagebox.showerror("Configuration", str(runtime_exc)))
        except Exception as generic_exc:
            self.root.after(0, lambda: messagebox.showerror("Error", str(generic_exc)))
        finally:
            self.root.after(0, lambda: self.compare_button.config(state="normal"))

    def _render_result(self, result: ComparisonResult) -> None:
        color = ALERT_COLORS.get(result.alert_level, "#333333")
        self.status_label.config(text=result.alert_message, foreground=color)

        self.results_box.config(state="normal")
        self.results_box.delete("1.0", tk.END)
        for field in result.fields:
            self.results_box.insert(tk.END, f"{field.label}: {field.status}\n")
            self.results_box.insert(tk.END, f"A: {field.value_a or 'n/a'}\n")
            self.results_box.insert(tk.END, f"B: {field.value_b or 'n/a'}\n")
            if field.explanation:
                self.results_box.insert(tk.END, f"Reason: {field.explanation}\n")
            self.results_box.insert(tk.END, "\n")
        self.results_box.config(state="disabled")

    def run(self) -> None:
        self.root.mainloop()


def launch_gui() -> None:
    DegreeCompareGUI().run()


if __name__ == "__main__":
    launch_gui()
