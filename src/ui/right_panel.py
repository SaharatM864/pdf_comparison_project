import os
import customtkinter as ctk

from src.core.matcher import get_matching_files, get_sorted_single_files
from src.core.renamer import get_rename_preview

class RightPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_rowconfigure(0, weight=6)  # ตาราง
        self.grid_rowconfigure(1, weight=1)  # Progress
        self.grid_rowconfigure(2, weight=3)  # Log Console
        self.grid_columnconfigure(0, weight=1)
        
        self._create_widgets()
        
    def _create_widgets(self):
        # ส่วนที่ 1: ตารางคู่ไฟล์
        self.frm_table = ctk.CTkFrame(self, corner_radius=15)
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
        self.frm_progress = ctk.CTkFrame(self, fg_color="transparent")
        self.frm_progress.grid(row=1, column=0, sticky="nsew", pady=10)

        self.lbl_progress = ctk.CTkLabel(
            self.frm_progress, text="รอเริ่มงาน...", font=ctk.CTkFont(size=14)
        )
        self.lbl_progress.pack(anchor="w")

        self.progress_bar = ctk.CTkProgressBar(self.frm_progress)
        self.progress_bar.pack(fill="x", pady=(5, 0))
        self.progress_bar.set(0)

        # ส่วนที่ 3: Log Console
        self.frm_log = ctk.CTkFrame(self, corner_radius=15)
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

    def update_table(self, orig, rev, mode, doc_type, allow_unmatched=False):
        """จัดการดึงข้อมูลมาแสดงในตาราง"""
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
                    self.table_textbox.insert("end", f"เกิดข้อผิดพลาดในการอ่านโฟลเดอร์:\n{str(e)}")
            else:
                self.table_textbox.insert("end", "กรุณาเลือกโฟลเดอร์ต้นฉบับ เพื่อดูรายการไฟล์")

        elif mode == "rename":
            if orig and rev:
                try:
                    preview = get_rename_preview(orig, rev, doc_type)
                    total = len(preview)

                    doc_label = "e-Tax" if doc_type == "etax" else "Smart Invoice"
                    header = f"{'NO.':<5} | {'ชื่อเดิม':<40} | {'ชื่อใหม่':<40}\n"
                    separator = "-" * 90 + "\n"

                    self.table_textbox.insert("end", f"[{doc_label}] พบไฟล์ที่จะ Rename {total} ไฟล์\n\n")
                    self.table_textbox.insert("end", header)
                    self.table_textbox.insert("end", separator)

                    for idx, (old_name, new_name) in enumerate(preview):
                        old_disp = old_name if len(old_name) <= 38 else old_name[:35] + "..."
                        new_disp = new_name if len(new_name) <= 38 else new_name[:35] + "..."
                        row = f"{idx+1:<5} | {old_disp:<40} | {new_disp:<40}\n"
                        self.table_textbox.insert("end", row)

                    if total == 0:
                        self.table_textbox.insert("end", "ไม่พบไฟล์ที่ต้องเปลี่ยนชื่อ (อาจ Rename ไปแล้ว หรือไม่ตรงกับ Mapping)")

                except Exception as e:
                    self.table_textbox.insert("end", f"เกิดข้อผิดพลาดในการอ่านโฟลเดอร์:\n{str(e)}")
            else:
                self.table_textbox.insert("end", "กรุณาเลือกโฟลเดอร์ทั้ง Source และ DDM เพื่อดูรายการไฟล์")

        else:  # compare
            if orig or rev:  # ผ่อนปรนหากมีเพียง 1 ก็ทำงานได้
                try:
                    matched_files = get_matching_files(orig, rev, allow_unmatched=allow_unmatched)
                    total = len(matched_files)
                    
                    matched = sum(1 for p1, p2 in matched_files if p1 and p2)
                    unmatched = total - matched

                    header = f"{'NO.':<5} | {'ORIGINAL FILE':<40} | {'REVISED FILE':<40}\n"
                    separator = "-" * 90 + "\n"

                    self.table_textbox.insert("end", f"พบรายการทั้งหมด {total} รายการ ({matched} จับคู่สมบูรณ์ / {unmatched} ฝั่งเดียว)\n\n")
                    self.table_textbox.insert("end", header)
                    self.table_textbox.insert("end", separator)

                    for idx, (path_orig, path_rev) in enumerate(matched_files):
                        if path_orig:
                            name_o = os.path.basename(path_orig)
                            if len(name_o) > 38:
                                name_o = name_o[:35] + "..."
                        else:
                            name_o = "— (ไม่มีเอกสาร) —"

                        if path_rev:
                            name_r = os.path.basename(path_rev)
                            if len(name_r) > 38:
                                name_r = name_r[:35] + "..."
                        else:
                            name_r = "— (ไม่มีเอกสาร) —"

                        row = f"{idx+1:<5} | {name_o:<40} | {name_r:<40}\n"
                        self.table_textbox.insert("end", row)

                except Exception as e:
                    self.table_textbox.insert("end", f"เกิดข้อผิดพลาดในการอ่านโฟลเดอร์:\n{str(e)}")
            else:
                self.table_textbox.insert("end", "กรุณาเลือกโฟลเดอร์อย่างน้อยหนึ่งฝั่งเพื่อดูรายการ")

        self.table_textbox.configure(state="disabled")

        self.table_textbox.configure(state="disabled")

    def log(self, text):
        """เพิ่มข้อความลงใน Log Console (Thread-safe)"""
        def update_log():
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", text + "\n")
            self.log_textbox.see("end")  # Scroll to bottom
            self.log_textbox.configure(state="disabled")

        self.after(0, update_log)

    def clear_log(self):
        """ล้าง Log Console"""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

    def update_progress(self, current, total):
        """อัพเดทหลอด Progress (Thread-safe)"""
        def update_ui():
            percent = current / total if total > 0 else 0
            self.progress_bar.set(percent)
            self.lbl_progress.configure(
                text=f"กำลังประมวลผล... {current}/{total} คู่ ({percent*100:.1f}%)"
            )

        self.after(0, update_ui)

    def reset_progress(self, text="รอเริ่มงาน..."):
        self.progress_bar.set(0)
        self.lbl_progress.configure(text=text)

    def set_progress_text(self, text):
        self.lbl_progress.configure(text=text)
