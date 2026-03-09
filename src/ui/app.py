import os
import sys
import threading
import customtkinter as ctk
from tkinter import messagebox

from src.core.comparison import run_comparison
from src.core.renamer import rename_ddm_files
from src.ui.left_panel import LeftPanel
from src.ui.right_panel import RightPanel

# ตั้งค่า Theme ของ CustomTkinter
ctk.set_appearance_mode("Dark")  # โหมดมืดตาม Mockup
ctk.set_default_color_theme("blue")  # สีธีมน้ำเงิน


class PDFComparisonApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ระบบเปรียบเทียบเอกสาร PDF (PDF Comparison)")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.is_processing = False

        # โครงสร้างหลักแบบ Grid (1 แถว 2 คอลัมน์)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)  # แผงซ้าย 30%
        self.grid_columnconfigure(1, weight=7)  # แผงขวา 70%

        callbacks = {
            'update_table': self._on_update_table,
            'start_task': self._start_comparison
        }

        # ==================== แผงด้านซ้าย (Left Panel) ====================
        self.left_panel = LeftPanel(self, callbacks, corner_radius=15)
        self.left_panel.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")

        # ==================== แผงด้านขวา (Right Panel) ====================
        self.right_panel = RightPanel(self, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")

    def _on_update_table(self):
        """เรียกให้ RightPanel อัปเดตตารางเมื่อมีการเปลี่ยนโหมดหรือโฟลเดอร์จาก LeftPanel"""
        orig = self.left_panel.dir_original.get()
        rev = self.left_panel.dir_revised.get()
        mode = self.left_panel.op_mode.get()
        doc_type = self.left_panel.doc_type_var.get()
        self.right_panel.update_table(orig, rev, mode, doc_type)

    def _start_comparison(self):
        if self.is_processing: 
            return
        
        orig = self.left_panel.dir_original.get()
        rev = self.left_panel.dir_revised.get()
        mode = self.left_panel.op_mode.get()
        
        if mode == "compare" and (not orig or not rev):
            messagebox.showwarning("คำเตือน", "กรุณาเลือกโฟลเดอร์ให้ครบทั้งสองฝั่ง")
            return
        elif mode == "rename" and (not orig or not rev):
            messagebox.showwarning("คำเตือน", "กรุณาเลือกโฟลเดอร์ทั้ง Source และ DDM")
            return
        elif mode == "single" and not orig:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกโฟลเดอร์ต้นฉบับ")
            return
            
        gen_docx = self.left_panel.gen_docx.get()
        gen_pdf = self.left_panel.gen_pdf.get()
        
        if mode != "rename" and not gen_docx and not gen_pdf:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกรูปแบบ Output อย่างน้อย 1 รูปแบบ (DOCX หรือ PDF)")
            return
            
        # Disable UI
        self.is_processing = True
        self.left_panel.set_processing_state(True)
        self.right_panel.clear_log()
        self.right_panel.reset_progress("เริ่มการทำงาน...")
        
        if mode == "rename":
            doc_type = self.left_panel.doc_type_var.get()
            threading.Thread(
                target=self._run_rename_task,
                args=(orig, rev, doc_type),
                daemon=True,
            ).start()
        else:
            output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output"))
            os.makedirs(output_dir, exist_ok=True)
            
            params = {
                "dir_original": orig,
                "dir_revised": rev,
                "output_dir": output_dir,
                "mode": mode,
                "target_dpi": int(self.left_panel.dpi_value.get()),
                "page_num": 0,
                "generate_docx_flag": gen_docx,
                "generate_pdf_flag": gen_pdf,
                "progress_callback": self.right_panel.update_progress,
                "log_callback": self.right_panel.log,
            }
            threading.Thread(target=self._run_task, kwargs=params, daemon=True).start()

    def _run_rename_task(self, source_dir, dest_dir, doc_type):
        """รัน Rename ใน Thread แยก"""
        try:
            result = rename_ddm_files(source_dir, dest_dir, doc_type, log_callback=self.right_panel.log)
            self.after(0, self._on_rename_complete, result)
        except Exception as e:
            self.right_panel.log(f"[ข้อผิดพลาดร้ายแรง] {e}")
            self.after(0, self._on_rename_complete, None)

    def _run_task(self, **kwargs):
        """รัน Comparison ใน Thread แยก"""
        try:
            success = run_comparison(**kwargs)
            self.after(0, self._on_task_complete, success)
        except Exception as e:
            self.right_panel.log(f"[ข้อผิดพลาดร้ายแรง] {e}")
            self.after(0, self._on_task_complete, False)

    def _on_rename_complete(self, result):
        """Callback เมื่อ Rename เสร็จ"""
        self.is_processing = False
        self.left_panel.set_processing_state(False)
        
        if result:
            self.right_panel.set_progress_text(f"✅ สำเร็จ {result['success']} ไฟล์ | ❌ ล้มเหลว {result['error']} ไฟล์")
            self.right_panel.progress_bar.set(1.0)
            if result["error"] == 0:
                messagebox.showinfo("สำเร็จ", f"เปลี่ยนชื่อไฟล์สำเร็จทั้งหมด {result['success']} ไฟล์\n(ข้ามไฟล์ที่เคย Rename แล้ว {result['skipped']} ไฟล์)")
            else:
                messagebox.showwarning("เสร็จสิ้น (มีข้อผิดพลาด)", f"สำเร็จ {result['success']} ไฟล์ / ล้มเหลว {result['error']} ไฟล์\nกรุณาดูรายละเอียดใน Log Console")
            self._on_update_table()
        else:
            self.right_panel.set_progress_text("❌ เกิดข้อผิดพลาด")
            messagebox.showerror("ผิดพลาด", "การ Rename ล้มเหลว กรุณาดูรายละเอียดใน Log Console")

    def _on_task_complete(self, success):
        """Callback เมื่อ Comparison หรือ Single เสร็จ"""
        self.is_processing = False
        self.left_panel.set_processing_state(False)
        
        if success:
            self.right_panel.set_progress_text("✅ สำเร็จ! เปิดดูผลลัพธ์ในโฟลเดอร์ output")
            if messagebox.askyesno("สำเร็จ", "ประมวลผลเสร็จสิ้น\nต้องการเปิดโฟลเดอร์ output หรือไม่?"):
                output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output"))
                (os.startfile(output_dir) if sys.platform == "win32" else os.system(f"open {output_dir}"))
        else:
            self.right_panel.set_progress_text("❌ เกิดข้อผิดพลาด")
            messagebox.showerror("ผิดพลาด", "การประมวลผลล้มเหลว กรุณาดูรายละเอียดใน Log Console")


if __name__ == "__main__":
    app = PDFComparisonApp()
    app.mainloop()
