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
        self.root.geometry("720x520")
        self.repo = HistoryRepository()
        self.client: GeminiComparisonClient | None = None

        self.url_a_var = tk.StringVar()
        self.url_b_var = tk.StringVar()

        self._build_widgets()

    def _build_widgets(self) -> None:
        padding = {"padx": 12, "pady": 6}

        ttk.Label(self.root, text="URL A").grid(row=0, column=0, sticky="w", **padding)
        ttk.Entry(self.root, textvariable=self.url_a_var, width=80).grid(row=0, column=1, **padding)

        ttk.Label(self.root, text="URL B").grid(row=1, column=0, sticky="w", **padding)
        ttk.Entry(self.root, textvariable=self.url_b_var, width=80).grid(row=1, column=1, **padding)

        self.compare_button = ttk.Button(self.root, text="Compare", command=self._on_compare)
        self.compare_button.grid(row=2, column=1, sticky="e", **padding)

        self.status_label = ttk.Label(self.root, text="Ready", foreground="#444444")
        self.status_label.grid(row=3, column=0, columnspan=2, sticky="w", **padding)

        self.results_box = tk.Text(self.root, height=20, width=90, state="disabled")
        self.results_box.grid(row=4, column=0, columnspan=2, padx=12, pady=(6, 12))

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
