import os
import sys
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

from src.core.comparison import run_comparison
from src.core.matcher import get_matching_files, get_sorted_single_files

# ตั้งค่า Theme ของ CustomTkinter
ctk.set_appearance_mode("Dark")  # โหมดมืดตาม Mockup
ctk.set_default_color_theme("blue")  # สีธีมน้ำเงิน


class PDFComparisonApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ระบบเปรียบเทียบเอกสาร PDF (PDF Comparison)")
        self.geometry("1100x700")
        self.minsize(900, 600)

        # ตัวแปรสถานะ
        self.dir_original = ctk.StringVar(value="")
        self.dir_revised = ctk.StringVar(value="")
        self.dpi_value = ctk.IntVar(value=150)
        self.gen_docx = ctk.BooleanVar(
            value=False
        )  # ค่าเริ่มต้นเป็น False เพราะโหมดแรกคือ compare
        self.gen_pdf = ctk.BooleanVar(value=True)
        self.is_processing = False
        self.op_mode = ctk.StringVar(value="compare")

        self._create_layout()

    def _create_layout(self):
        # โครงสร้างหลักแบบ Grid (1 แถว 2 คอลัมน์)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)  # แผงซ้าย 30%
        self.grid_columnconfigure(1, weight=7)  # แผงขวา 70%

        # ==================== แผงด้านซ้าย (Left Panel) ====================
        self.left_panel = ctk.CTkFrame(self, corner_radius=15)
        self.left_panel.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")

        # ส่วนที่ 0: เลือกโหมดการทำงาน
        lbl_mode = ctk.CTkLabel(
            self.left_panel,
            text="⚙️ โหมดการทำงาน",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        lbl_mode.pack(pady=(20, 5), padx=20, anchor="w")

        self.seg_mode = ctk.CTkSegmentedButton(
            self.left_panel,
            values=["โหมดเปรียบเทียบ (Compare)", "โหมดรวมเอกสารเดี่ยว (Single)"],
            command=self._on_mode_change,
        )
        self.seg_mode.pack(fill="x", padx=20, pady=(0, 15))
        self.seg_mode.set("โหมดเปรียบเทียบ (Compare)")

        # ส่วนที่ 1: เลือกโฟลเดอร์
        lbl_folders = ctk.CTkLabel(
            self.left_panel,
            text="📁 เลือกโฟลเดอร์",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        lbl_folders.pack(pady=(5, 10), padx=20, anchor="w")

        # โฟลเดอร์ต้นฉบับ
        self.lbl_orig, self.entry_orig, self.btn_orig = self._create_folder_selector(
            "📂 โฟลเดอร์ต้นฉบับ (Original):", self.dir_original, self._select_orig_dir
        )
        # โฟลเดอร์แก้ไข
        self.lbl_rev, self.entry_rev, self.btn_rev = self._create_folder_selector(
            "📂 โฟลเดอร์แก้ไข (Revised):", self.dir_revised, self._select_rev_dir
        )

        # ส่วนที่ 2: ตั้งค่า
        lbl_settings = ctk.CTkLabel(
            self.left_panel, text="⚙️ การตั้งค่า", font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl_settings.pack(pady=(30, 10), padx=20, anchor="w")

        # DPI Slider
        frm_dpi = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        frm_dpi.pack(fill="x", padx=20, pady=5)
        self.lbl_dpi_val = ctk.CTkLabel(frm_dpi, text="ความละเอียด (DPI): 150")
        self.lbl_dpi_val.pack(anchor="w")
        self.slider_dpi = ctk.CTkSlider(
            frm_dpi,
            from_=72,
            to=300,
            variable=self.dpi_value,
            command=self._update_dpi_label,
        )
        self.slider_dpi.pack(fill="x", pady=5)
        # เริ่มต้นที่โหมด Compare ปิดใช้งาน DPI (เพราะไม่ได้ใช้เรนเดอร์ภาพแล้ว)
        self.slider_dpi.configure(state="disabled")
        self.lbl_dpi_val.configure(text_color="gray")

        # Output Format
        lbl_format = ctk.CTkLabel(self.left_panel, text="ไฟล์ผลลัพธ์:")
        lbl_format.pack(anchor="w", padx=20, pady=(15, 5))
        self.chk_docx = ctk.CTkCheckBox(
            self.left_panel, text="สร้างไฟล์ DOCX", variable=self.gen_docx
        )
        self.chk_docx.pack(anchor="w", padx=30, pady=5)
        # เริ่มต้นโหมด Compare: บังคับปิด DOCX
        self.chk_docx.configure(state="disabled")

        self.chk_pdf = ctk.CTkCheckBox(
            self.left_panel, text="สร้างไฟล์ PDF", variable=self.gen_pdf
        )
        self.chk_pdf.pack(anchor="w", padx=30, pady=5)
        # บังคับเลือก PDF ไว้เสมอ
        self.chk_pdf.configure(state="disabled")

        # Spacer
        ctk.CTkLabel(self.left_panel, text="").pack(expand=True)

        # ส่วนที่ 3: ปุ่มทำงาน
        self.btn_compare = ctk.CTkButton(
            self.left_panel,
            text="🚀 เริ่มเปรียบเทียบ",
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._start_comparison,
        )
        self.btn_compare.pack(fill="x", padx=20, pady=20)

        # ==================== แผงด้านขวา (Right Panel) ====================
        self.right_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")
        self.right_panel.grid_rowconfigure(0, weight=6)  # ตาราง
        self.right_panel.grid_rowconfigure(1, weight=1)  # Progress
        self.right_panel.grid_rowconfigure(2, weight=3)  # Log Console
        self.right_panel.grid_columnconfigure(0, weight=1)

        # ส่วนที่ 1: ตารางคู่ไฟล์
        self.frm_table = ctk.CTkFrame(self.right_panel, corner_radius=15)
        self.frm_table.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        table_lbl = ctk.CTkLabel(
            self.frm_table,
            text="📋 รายการจับคู่เอกสารก่อนประมวลผล",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        table_lbl.pack(pady=10, padx=15, anchor="w")

        self.table_textbox = ctk.CTkTextbox(
            self.frm_table,
            activate_scrollbars=True,
            state="disabled",
            font=ctk.CTkFont(family="Consolas", size=13),
        )
        self.table_textbox.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # ส่วนที่ 2: Progress
        self.frm_progress = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.frm_progress.grid(row=1, column=0, sticky="nsew", pady=10)

        self.lbl_progress = ctk.CTkLabel(
            self.frm_progress, text="รอเริ่มงาน...", font=ctk.CTkFont(size=14)
        )
        self.lbl_progress.pack(anchor="w")

        self.progress_bar = ctk.CTkProgressBar(self.frm_progress)
        self.progress_bar.pack(fill="x", pady=(5, 0))
        self.progress_bar.set(0)

        # ส่วนที่ 3: Log Console
        self.frm_log = ctk.CTkFrame(self.right_panel, corner_radius=15)
        self.frm_log.grid(row=2, column=0, sticky="nsew", pady=(10, 0))

        log_lbl = ctk.CTkLabel(
            self.frm_log, text="🖥️ Console Log", font=ctk.CTkFont(size=14, weight="bold")
        )
        log_lbl.pack(pady=(10, 0), padx=15, anchor="w")

        self.log_textbox = ctk.CTkTextbox(
            self.frm_log,
            activate_scrollbars=True,
            state="disabled",
            font=ctk.CTkFont(family="Consolas", size=12),
        )
        self.log_textbox.pack(fill="both", expand=True, padx=15, pady=10)

    def _create_folder_selector(self, label_text, string_var, command):
        lbl = ctk.CTkLabel(self.left_panel, text=label_text)
        lbl.pack(anchor="w", padx=20, pady=(5, 0))

        frm = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        frm.pack(fill="x", padx=20, pady=5)

        entry = ctk.CTkEntry(
            frm,
            textvariable=string_var,
            state="disabled",
            fg_color=("#E0E0E0", "#2B2B2B"),
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn = ctk.CTkButton(frm, text="Browse", width=60, command=command)
        btn.pack(side="right")
        return lbl, entry, btn

    def _select_orig_dir(self):
        folder = filedialog.askdirectory(title="เลือกโฟลเดอร์เอกสารต้นฉบับ")
        if folder:
            self.dir_original.set(folder)
            self._update_matching_table()

    def _select_rev_dir(self):
        folder = filedialog.askdirectory(title="เลือกโฟลเดอร์เอกสารแก้ไข")
        if folder:
            self.dir_revised.set(folder)
            self._update_matching_table()

    def _update_dpi_label(self, val):
        self.lbl_dpi_val.configure(text=f"ความละเอียด (DPI): {int(val)}")

    def _on_mode_change(self, value):
        if value == "โหมดรวมเอกสารเดี่ยว (Single)":
            self.op_mode.set("single")

            # ปิดปุ่มเลือกโฟลเดอร์เปรียบเทียบ
            self.btn_rev.configure(state="disabled")
            self.lbl_rev.configure(text_color="gray")
        else:
            self.op_mode.set("compare")

            # เปิดให้ใช้ปุ่มเอกสารแก้ไขอีกครั้ง
            self.btn_rev.configure(state="normal")
            self.lbl_rev.configure(text_color=["#000000", "#FFFFFF"])

        self._update_matching_table()

    def _update_matching_table(self):
        orig = self.dir_original.get()
        rev = self.dir_revised.get()
        mode = self.op_mode.get()

        self.table_textbox.configure(state="normal")
        self.table_textbox.delete("1.0", "end")

        if mode == "single":
            if orig:
                try:
                    single_files = get_sorted_single_files(orig)
                    total = len(single_files)

                    header = f"{'NO.':<5} | {'FILE NAME':<80}\n"
                    separator = "-" * 90 + "\n"

                    self.table_textbox.insert("end", f"พบเอกสารทั้งหมด {total} ไฟล์\n\n")
                    self.table_textbox.insert("end", header)
                    self.table_textbox.insert("end", separator)

                    for idx, path in enumerate(single_files):
                        name = os.path.basename(path)
                        if len(name) > 75:
                            name = name[:72] + "..."

                        row = f"{idx+1:<5} | {name:<80}\n"
                        self.table_textbox.insert("end", row)

                except Exception as e:
                    self.table_textbox.insert(
                        "end", f"เกิดข้อผิดพลาดในการอ่านโฟลเดอร์:\n{str(e)}"
                    )
            else:
                self.table_textbox.insert("end", "กรุณาเลือกโฟลเดอร์ต้นฉบับ เพื่อดูรายการไฟล์")

        else:
            if orig and rev:
                try:
                    matched_files = get_matching_files(orig, rev)
                    total = len(matched_files)

                    header = (
                        f"{'NO.':<5} | {'ORIGINAL FILE':<40} | {'REVISED FILE':<40}\n"
                    )
                    separator = "-" * 90 + "\n"

                    self.table_textbox.insert("end", f"พบการจับคู่ {total} คู่\n\n")
                    self.table_textbox.insert("end", header)
                    self.table_textbox.insert("end", separator)

                    for idx, (path_orig, path_rev) in enumerate(matched_files):
                        name_o = os.path.basename(path_orig)
                        if len(name_o) > 38:
                            name_o = name_o[:35] + "..."

                        name_r = os.path.basename(path_rev)
                        if len(name_r) > 38:
                            name_r = name_r[:35] + "..."

                        row = f"{idx+1:<5} | {name_o:<40} | {name_r:<40}\n"
                        self.table_textbox.insert("end", row)

                except Exception as e:
                    self.table_textbox.insert(
                        "end", f"เกิดข้อผิดพลาดในการอ่านโฟลเดอร์:\n{str(e)}"
                    )
            else:
                self.table_textbox.insert(
                    "end", "กรุณาเลือกโฟลเดอร์ทั้ง ต้นฉบับ และ แก้ไข เพื่อดูรายการจับคู่"
                )

        self.table_textbox.configure(state="disabled")

    def log(self, text):
        """เพิ่มข้อความลงใน Log Console (Thread-safe)"""

        def update_log():
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", text + "\n")
            self.log_textbox.see("end")  # Scroll to bottom
            self.log_textbox.configure(state="disabled")

        self.after(0, update_log)

    def update_progress(self, current, total):
        """อัพเดทหลอด Progress (Thread-safe)"""

        def update_ui():
            percent = current / total if total > 0 else 0
            self.progress_bar.set(percent)
            self.lbl_progress.configure(
                text=f"กำลังประมวลผล... {current}/{total} คู่ ({percent*100:.1f}%)"
            )

        self.after(0, update_ui)

    def _start_comparison(self):
        # Validate
        orig = self.dir_original.get()
        rev = self.dir_revised.get()
        mode = self.op_mode.get()

        if mode == "compare":
            if not orig or not rev:
                messagebox.showwarning("คำเตือน", "กรุณาเลือกโฟลเดอร์ให้ครบทั้งสองฝั่ง")
                return
        else:
            if not orig:
                messagebox.showwarning("คำเตือน", "กรุณาเลือกโฟลเดอร์ต้นฉบับ")
                return

        if not self.gen_docx.get() and not self.gen_pdf.get():
            messagebox.showwarning(
                "คำเตือน", "กรุณาเลือกรูปแบบ Output อย่างน้อย 1 รูปแบบ (DOCX หรือ PDF)"
            )
            return

        # Disable UI
        self.is_processing = True
        self.btn_compare.configure(state="disabled", text="⏳ กำลังประมวลผล...")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        self.progress_bar.set(0)
        self.lbl_progress.configure(text="เริ่มการทำงาน...")

        # Prepare params
        output_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "output")
        )
        os.makedirs(output_dir, exist_ok=True)

        params = {
            "dir_original": orig,
            "dir_revised": rev,
            "output_dir": output_dir,
            "mode": mode,
            "target_dpi": int(self.dpi_value.get()),
            "page_num": 0,
            "generate_docx_flag": self.gen_docx.get(),
            "generate_pdf_flag": self.gen_pdf.get(),
            "progress_callback": self.update_progress,
            "log_callback": self.log,
        }

        # รันใน Thread แยกเพื่อไม่ให้ GUI ค้าง
        threading.Thread(target=self._run_task, kwargs=params, daemon=True).start()

    def _run_task(self, **kwargs):
        try:
            success = run_comparison(**kwargs)
            self.after(0, self._on_task_complete, success)
        except Exception as e:
            self.log(f"[ข้อผิดพลาดร้ายแรง] {e}")
            self.after(0, self._on_task_complete, False)

    def _on_task_complete(self, success):
        self.is_processing = False
        self.btn_compare.configure(state="normal", text="🚀 เริ่มเปรียบเทียบ")

        if success:
            self.lbl_progress.configure(text="✅ สำเร็จ! เปิดดูผลลัพธ์ในโฟลเดอร์ output")
            if messagebox.askyesno(
                "สำเร็จ", "ประมวลผลเสร็จสิ้น\nต้องการเปิดโฟลเดอร์ output หรือไม่?"
            ):
                output_dir = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "..", "output")
                )
                (
                    os.startfile(output_dir)
                    if sys.platform == "win32"
                    else os.system(f"open {output_dir}")
                )
        else:
            self.lbl_progress.configure(text="❌ เกิดข้อผิดพลาด")
            messagebox.showerror(
                "ผิดพลาด", "การประมวลผลล้มเหลว กรุณาดูรายละเอียดใน Log Console"
            )


if __name__ == "__main__":
    app = PDFComparisonApp()
    app.mainloop()
