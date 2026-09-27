import json
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

CONFIG_PATH = "config.json"
DEFAULT_CONFIG = {
    "ollama_url": "http://127.0.0.1:11434",
    "model": "qwen2.5-coder:7b",
    "timeout": 120
}

SYSTEM_PROMPT = """You are Bruce AI Script Builder.
Generate only benign Bruce Firmware automation/testing scripts.

Modes:
- BadUSB / BadBLE: output DuckyScript text only.
- BruceJS: output JavaScript for Bruce Firmware only.

Rules:
- No markdown fences.
- No explanations in the generated script.
- Keep syntax simple and compatible.
- Do not generate credential theft, destructive commands, ransomware, persistence,
  evasion, data wiping, system sabotage, blue-screen/crash payloads, or malware.
- Prefer harmless demonstrations such as opening a local application, typing a
  visible test message, waiting, or showing information.
"""

DANGEROUS_PATTERNS = [
    r"\bformat\b", r"\bdel\s+/[sqf]", r"\brmdir\s+/s",
    r"\bshutdown\b", r"\btaskkill\b", r"\bnet\s+user\b",
    r"\bcredential", r"\bkeylog", r"\bransom",
    r"\bdisable\s+(defender|security)", r"\bcrash\b",
    r"\bblue\s*screen\b"
]

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def validate_script(text):
    low = text.lower()
    return [p for p in DANGEROUS_PATTERNS if re.search(p, low)]

class BruceBuilder(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bruce AI Script Builder")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.config_data = load_config()
        self.mode = tk.StringVar(value="BadUSB / BadBLE")
        self.status = tk.StringVar(value="Ready")
        self.build_ui()

    def build_ui(self):
        top = ttk.Frame(self, padding=12)
        top.pack(fill="x")
        ttk.Label(top, text="Bruce AI Script Builder",
                  font=("Segoe UI", 18, "bold")).pack(side="left")
        ttk.Label(top, text="Mode:").pack(side="left", padx=(30, 6))
        ttk.Combobox(top, textvariable=self.mode,
                     values=["BadUSB / BadBLE", "BruceJS"],
                     state="readonly", width=18).pack(side="left")
        ttk.Button(top, text="Settings", command=self.settings).pack(side="right")

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        left, right = ttk.Frame(body, padding=8), ttk.Frame(body, padding=8)
        body.add(left, weight=1)
        body.add(right, weight=2)

        ttk.Label(left, text="Describe what you want",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.prompt_box = tk.Text(left, height=12, wrap="word", font=("Consolas", 11))
        self.prompt_box.pack(fill="both", expand=True, pady=8)

        ttk.Button(left, text="Generate AI Script", command=self.generate).pack(fill="x", pady=3)
        ttk.Button(left, text="Clear",
                   command=lambda: self.prompt_box.delete("1.0", "end")).pack(fill="x", pady=3)

        ttk.Label(left, text="Safe examples",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(14, 4))
        examples = [
            "Open Notepad and type a harmless test message.",
            "Wait 2 seconds, then type Hello from Bruce.",
            "Show a simple BruceJS message on the display."
        ]
        for example in examples:
            ttk.Button(left, text=example,
                       command=lambda x=example: self.set_example(x)).pack(fill="x", pady=2)

        ttk.Label(right, text="Generated script",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.editor = tk.Text(right, wrap="none", font=("Consolas", 11), undo=True)
        self.editor.pack(fill="both", expand=True, pady=8)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Label(bottom, textvariable=self.status).pack(side="left")
        ttk.Button(bottom, text="Validate", command=self.validate).pack(side="right", padx=4)
        ttk.Button(bottom, text="Export", command=self.export).pack(side="right", padx=4)

    def set_example(self, text):
        self.prompt_box.delete("1.0", "end")
        self.prompt_box.insert("1.0", text)

    def settings(self):
        win = tk.Toplevel(self)
        win.title("Ollama Settings")
        win.geometry("460x220")
        win.transient(self)
        vars_ = [
            ("Ollama URL", tk.StringVar(value=self.config_data["ollama_url"])),
            ("Model", tk.StringVar(value=self.config_data["model"])),
            ("Timeout", tk.StringVar(value=str(self.config_data["timeout"])))
        ]
        for label, var in vars_:
            row = ttk.Frame(win, padding=8)
            row.pack(fill="x")
            ttk.Label(row, text=label, width=14).pack(side="left")
            ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)
        def save():
            try:
                timeout = int(vars_[2][1].get())
            except ValueError:
                messagebox.showerror("Error", "Timeout must be a number.")
                return
            self.config_data = {
                "ollama_url": vars_[0][1].get().rstrip("/"),
                "model": vars_[1][1].get(),
                "timeout": timeout
            }
            save_config(self.config_data)
            win.destroy()
            self.status.set("Settings saved")
        ttk.Button(win, text="Save", command=save).pack(pady=12)

    def generate(self):
        prompt = self.prompt_box.get("1.0", "end").strip()
        if not prompt:
            messagebox.showwarning("Missing prompt", "Describe the script you want.")
            return
        self.status.set("Generating with Ollama...")
        self.update_idletasks()
        full_prompt = (SYSTEM_PROMPT + "\nSelected mode: " + self.mode.get() +
                       "\nUser request: " + prompt + "\nReturn only the script.")
        try:
            payload = json.dumps({
                "model": self.config_data["model"],
                "prompt": full_prompt,
                "stream": False,
                "options": {"temperature": 0.2}
            }).encode("utf-8")
            req = Request(self.config_data["ollama_url"] + "/api/generate",
                          data=payload,
                          headers={"Content-Type": "application/json"},
                          method="POST")
            with urlopen(req, timeout=self.config_data["timeout"]) as response:
                result = json.loads(tresponse.read().decode("utf-8")
            output = result.get("response", "").strip()
            output = re.sub(r"^```[a-zA-Z0-9_+-]*\s*", "", output)
            output = re.sub(r"\s*```$", "", output).strip()
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", output)
            if validate_script(output):
                self.status.set("Generated output blocked by safety validator")
                messagebox.showwarning("Safety check", "Blocked command pattern detected.")
            else:
                self.status.set("Generated successfully")
        except HTTPError as e:
            self.status.set("Ollama HTTP error")
            messagebox.showerror("Ollama error", str(e))
        except URLError:
            self.status.set("Cannot reach Ollama")
            messagebox.showerror("Ollama unavailable", "Start Ollama and check Settings.")
        except Exception as e:
            self.status.set("Generation failed")
            messagebox.showerror("Error", str(e))

    def validate(self):
        text = self.editor.get("1.0", "end").strip()
        hits = validate_script(text)
        if hits:
            self.status.set("Validation failed")
            messagebox.showwarning("Validation failed", "Blocked patterns found:\\n\\n" + "\\n".join(hits))
        else:
            self.status.set("Validation passed")
            messagebox.showinfo("Validation", "No blocked patterns detected.")

    def export(self):
        text = self.editor.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty", "Generate or enter a script first.")
            return
        if validate_script(text):
            messagebox.showerror("Blocked", "Fix the blocked content before exporting.")
            return
        ext = ".js" if self.mode.get() == "BruceJS" else ".txt"
        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetxypes=[("Bruce script", "*" + ext), ("All files", "*.*")]
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8", newline="\\n") as f:
            f.write(text + "\\n")
        self.status.set("Exported: " + os.path.basename(path))
        messagebox.showinfo("Exported", path)

if __name__ == "__main__":
    BruceBuilder().mainloop()
