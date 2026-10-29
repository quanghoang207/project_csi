"""Giao diện Tkinter cho công cụ mã hóa file XOR."""

import queue
import threading
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from analysis.breaker import break_repeating_xor
from core.errors import (
    InvalidFileFormatError,
    OperationCancelled,
    WrongKeyOrCorruptedError,
)
from core.fileformat import decrypt_file, encrypt_file
from core.keygen import generate_random_key, save_keyfile
from core.xor_engine import xor_bytes


class XorToolApp:
    """Ứng dụng chọn file, mã hóa/giải mã và chạy demo trên dữ liệu mẫu."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("XORT | Công cụ mã hóa file")
        self.root.minsize(680, 470)
        self.root.geometry("760x540")
        self.messages = queue.Queue()
        self.cancel_event = None
        self.busy = False
        self._last_progress = None

        self.source_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.keyfile_var = tk.StringVar()
        self.use_keyfile_var = tk.BooleanVar(value=False)
        self.show_password_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Sẵn sàng")
        self.progress_var = tk.DoubleVar(value=0)
        self.demo_key_var = tk.StringVar(value="ORANGE")

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._request_close)
        self.root.after(100, self._poll)

    def _build_ui(self) -> None:
        style = ttk.Style(self.root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))

        outer = ttk.Frame(self.root, padding=(22, 18))
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="XORT", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Mã hóa file và kiểm tra toàn vẹn").pack(anchor="w", pady=(0, 14))

        tabs = ttk.Notebook(outer)
        tabs.pack(fill="both", expand=True)
        self.file_tab = ttk.Frame(tabs, padding=16)
        self.demo_tab = ttk.Frame(tabs, padding=16)
        tabs.add(self.file_tab, text="File")
        tabs.add(self.demo_tab, text="Demo XOR lặp")
        self._build_file_tab()
        self._build_demo_tab()

        footer = ttk.Frame(outer)
        footer.pack(fill="x", pady=(12, 0))
        self.progress = ttk.Progressbar(footer, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x")
        ttk.Label(footer, textvariable=self.status_var).pack(anchor="w", pady=(6, 0))

    def _build_file_tab(self) -> None:
        tab = self.file_tab
        tab.columnconfigure(1, weight=1)

        ttk.Label(tab, text="File nguồn").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Entry(tab, textvariable=self.source_var).grid(row=0, column=1, sticky="ew", pady=6)
        ttk.Button(tab, text="Chọn…", command=self._choose_source).grid(row=0, column=2, padx=(8, 0), pady=6)

        ttk.Label(tab, text="File đích").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Entry(tab, textvariable=self.output_var).grid(row=1, column=1, sticky="ew", pady=6)
        ttk.Button(tab, text="Lưu thành…", command=self._choose_output).grid(row=1, column=2, padx=(8, 0), pady=6)

        auth = ttk.LabelFrame(tab, text="Xác thực", style="Section.TLabelframe", padding=12)
        auth.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(14, 8))
        auth.columnconfigure(1, weight=1)
        ttk.Label(auth, text="Mật khẩu").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        self.password_entry = ttk.Entry(auth, textvariable=self.password_var, show="*")
        self.password_entry.grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Checkbutton(
            auth,
            text="Hiện mật khẩu",
            variable=self.show_password_var,
            command=self._toggle_password,
        ).grid(row=0, column=2, padx=(10, 0), pady=5)

        self.keyfile_check = ttk.Checkbutton(
            auth,
            text="Dùng keyfile",
            variable=self.use_keyfile_var,
            command=self._toggle_keyfile,
        )
        self.keyfile_check.grid(row=1, column=0, sticky="w", pady=5)
        self.keyfile_entry = ttk.Entry(auth, textvariable=self.keyfile_var, state="disabled")
        self.keyfile_entry.grid(row=1, column=1, sticky="ew", pady=5)
        self.keyfile_button = ttk.Button(auth, text="Chọn keyfile…", command=self._choose_keyfile, state="disabled")
        self.keyfile_button.grid(row=1, column=2, padx=(10, 0), pady=5)
        self.generate_key_button = ttk.Button(auth, text="Tạo keyfile ngẫu nhiên…", command=self._generate_keyfile)
        self.generate_key_button.grid(row=2, column=1, sticky="w", pady=(7, 0))

        actions = ttk.Frame(tab)
        actions.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        self.encrypt_button = ttk.Button(actions, text="Mã hóa", command=lambda: self._run_file_operation("encrypt"))
        self.encrypt_button.pack(side="left")
        self.decrypt_button = ttk.Button(actions, text="Giải mã", command=lambda: self._run_file_operation("decrypt"))
        self.decrypt_button.pack(side="left", padx=8)
        self.cancel_button = ttk.Button(actions, text="Hủy", command=self._cancel, state="disabled")
        self.cancel_button.pack(side="left")

    def _build_demo_tab(self) -> None:
        tab = self.demo_tab
        tab.columnconfigure(1, weight=1)
        ttk.Label(tab, text="Khóa thử nghiệm").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Entry(tab, textvariable=self.demo_key_var).grid(row=0, column=1, sticky="ew", pady=6)
        self.demo_button = ttk.Button(tab, text="Chạy demo trên sample_text.txt", command=self._run_breaker_demo)
        self.demo_button.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 12))
        ttk.Label(
            tab,
            text="Minh họa trên văn bản mẫu công khai trong dự án. Đây là XOR lặp khóa, không phải công cụ giải mã file người khác.",
            wraplength=560,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.demo_output = tk.Text(tab, height=13, wrap="word", state="disabled")
        self.demo_output.grid(row=3, column=0, columnspan=2, sticky="nsew")
        tab.rowconfigure(3, weight=1)

    def _choose_source(self) -> None:
        path = filedialog.askopenfilename(title="Chọn file nguồn")
        if not path:
            return
        self.source_var.set(path)
        source = Path(path)
        if source.name.endswith(".enc"):
            self.output_var.set(str(source.with_name(source.name[:-4])))
        else:
            self.output_var.set(str(source.with_name(source.name + ".enc")))

    def _choose_output(self) -> None:
        initial = self.output_var.get() or "output.enc"
        path = filedialog.asksaveasfilename(title="Chọn file đích", initialfile=Path(initial).name)
        if path:
            self.output_var.set(path)

    def _choose_keyfile(self) -> None:
        path = filedialog.askopenfilename(title="Chọn keyfile")
        if path:
            self.keyfile_var.set(path)

    def _generate_keyfile(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Lưu keyfile mới",
            defaultextension=".key",
            initialfile="xortool.key",
            filetypes=(("Key files", "*.key"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            if Path(path).exists() and not messagebox.askyesno("Ghi đè?", "File này đã tồn tại. Ghi đè?"):
                return
            save_keyfile(path, generate_random_key())
            self.keyfile_var.set(path)
            self.use_keyfile_var.set(True)
            self._toggle_keyfile()
            self.status_var.set("Đã tạo keyfile. Hãy giữ keyfile bí mật và tạo bản sao lưu.")
        except OSError as error:
            self._show_error(error)

    def _toggle_password(self) -> None:
        self.password_entry.configure(show="" if self.show_password_var.get() else "*")

    def _toggle_keyfile(self) -> None:
        enabled = self.use_keyfile_var.get()
        self.keyfile_entry.configure(state="normal" if enabled else "disabled")
        self.keyfile_button.configure(state="normal" if enabled else "disabled")
        self.password_entry.configure(state="disabled" if enabled else "normal")

    def _run_file_operation(self, operation: str) -> None:
        source_text, output_text = self.source_var.get().strip(), self.output_var.get().strip()
        if not source_text:
            messagebox.showwarning("Chưa chọn file", "Hãy chọn file nguồn.")
            return
        if not output_text:
            messagebox.showwarning("Chưa chọn file đích", "Hãy chọn nơi lưu file đích.")
            return
        source, output = Path(source_text), Path(output_text)
        if not source.is_file():
            self._show_error(FileNotFoundError("Không tìm thấy file nguồn."))
            return
        if source.resolve() == output.resolve():
            messagebox.showwarning("File đích không hợp lệ", "File nguồn và file đích không được trùng nhau.")
            return
        if output.exists() and not messagebox.askyesno("Ghi đè?", f"File đã tồn tại:\n{output}\n\nGhi đè file này?"):
            return

        if self.use_keyfile_var.get():
            keyfile = self.keyfile_var.get().strip()
            if not keyfile:
                messagebox.showwarning("Thiếu keyfile", "Hãy chọn keyfile.")
                return
            auth = {"keyfile": keyfile}
        else:
            password = self.password_var.get()
            if not password:
                messagebox.showwarning("Thiếu mật khẩu", "Hãy nhập mật khẩu hoặc chọn keyfile.")
                return
            auth = {"password": password}

        function = encrypt_file if operation == "encrypt" else decrypt_file
        self._start(lambda progress, cancel: function(
            source,
            output,
            progress_cb=progress,
            cancel_event=cancel,
            **auth,
        ))

    def _run_breaker_demo(self) -> None:
        key_text = self.demo_key_var.get().strip()
        if not key_text:
            messagebox.showwarning("Thiếu khóa", "Nhập một khóa thử nghiệm.")
            return
        sample_path = Path(__file__).resolve().parents[1] / "analysis" / "sample_text.txt"
        sample = sample_path.read_bytes()
        demo_key = key_text.encode("utf-8")

        def demo_task(progress, cancel):
            if cancel.is_set():
                raise OperationCancelled("Thao tác đã bị hủy.")
            ciphertext = xor_bytes(sample, demo_key)
            found_key, plaintext = break_repeating_xor(ciphertext)
            self.messages.put(("demo", found_key, plaintext))

        self._start(demo_task)

    def _start(self, function: Callable[[Callable[[int, int], None], threading.Event], None]) -> None:
        if self.busy:
            return
        self.cancel_event = threading.Event()
        self.busy = True
        self._last_progress = None
        self.progress_var.set(0)
        self.status_var.set("Đang xử lý…")
        self.encrypt_button.configure(state="disabled")
        self.decrypt_button.configure(state="disabled")
        self.demo_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        threading.Thread(target=self._worker, args=(function, self.cancel_event), daemon=True).start()

    def _worker(
        self,
        function: Callable[[Callable[[int, int], None], threading.Event], None],
        cancel_event: threading.Event,
    ) -> None:
        try:
            function(lambda done, total: self.messages.put(("progress", done, total)), cancel_event)
            self.messages.put(("done",))
        except OperationCancelled:
            self.messages.put(("cancelled",))
        except Exception as error:
            self.messages.put(("error", error))

    def _poll(self) -> None:
        try:
            while True:
                message = self.messages.get_nowait()
                self._handle_message(message)
        except queue.Empty:
            pass
        if not (getattr(self, "close_when_idle", False) and not self.busy):
            self.root.after(100, self._poll)

    def _handle_message(self, message: tuple) -> None:
        kind = message[0]
        if kind == "progress":
            _, done, total = message
            percent = 100 if total == 0 else min(100, int(done * 100 / total))
            if percent != self._last_progress:
                self.progress_var.set(percent)
                self._last_progress = percent
        elif kind == "demo":
            _, key, plaintext = message
            self.demo_output.configure(state="normal")
            self.demo_output.delete("1.0", "end")
            self.demo_output.insert("1.0", f"Khóa nhập: {self.demo_key_var.get()}\nKhóa tìm được: {key.decode('utf-8', errors='replace')}\n\n{plaintext.decode('utf-8', errors='replace')}")
            self.demo_output.configure(state="disabled")
        elif kind == "done":
            self.progress_var.set(100)
            self.status_var.set("Hoàn tất")
            self._set_idle()
        elif kind == "cancelled":
            self.status_var.set("Đã hủy thao tác")
            self._set_idle()
        elif kind == "error":
            self.status_var.set("Có lỗi")
            self._set_idle()
            self._show_error(message[1])

    def _set_idle(self) -> None:
        self.busy = False
        self.cancel_button.configure(state="disabled")
        self.encrypt_button.configure(state="normal")
        self.decrypt_button.configure(state="normal")
        self.demo_button.configure(state="normal")
        self.password_var.set("")
        if getattr(self, "close_when_idle", False):
            self.root.destroy()

    def _request_close(self) -> None:
        if self.busy:
            self.close_when_idle = True
            self._cancel()
        else:
            self.root.destroy()

    def _cancel(self) -> None:
        if self.cancel_event is not None:
            self.cancel_event.set()
            self.status_var.set("Đang hủy…")

    @staticmethod
    def _show_error(error: Exception) -> None:
        if isinstance(error, WrongKeyOrCorruptedError):
            text = "Sai mật khẩu hoặc file bị hỏng/bị chỉnh sửa."
        elif isinstance(error, InvalidFileFormatError):
            text = "Đây không phải file do công cụ này mã hóa."
        elif isinstance(error, FileNotFoundError):
            text = "Không tìm thấy file nguồn hoặc keyfile."
        elif isinstance(error, PermissionError):
            text = "Không có quyền đọc/ghi file hoặc thư mục."
        elif isinstance(error, ValueError):
            text = "Hãy nhập mật khẩu hoặc chọn keyfile (chỉ một trong hai)."
        else:
            text = f"Đã xảy ra lỗi không mong muốn: {str(error)[:240]}"
        messagebox.showerror("Không thể hoàn tất", text)


def run_app() -> None:
    """Khởi chạy cửa sổ chính."""
    root = tk.Tk()
    XorToolApp(root)
    root.mainloop()