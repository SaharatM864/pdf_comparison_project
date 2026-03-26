import customtkinter as ctk
from tkinter import filedialog

class LeftPanel(ctk.CTkScrollableFrame):
    def __init__(self, master, callbacks, **kwargs):
        super().__init__(master, **kwargs)
        self.callbacks = callbacks
        
        # ตัวแปรสถานะภายใน Panel
        self.dir_original = ctk.StringVar(value="")
        self.dir_revised = ctk.StringVar(value="")
        self.dpi_value = ctk.IntVar(value=150)
        self.gen_docx = ctk.BooleanVar(value=False)
        self.gen_pdf = ctk.BooleanVar(value=True)
        self.allow_unmatched = ctk.BooleanVar(value=False)
        self.op_mode = ctk.StringVar(value="compare")
        self.doc_type_var = ctk.StringVar(value="etax")
        
        self._create_widgets()
        
    def _create_widgets(self):
        # ส่วนที่ 0: เลือกโหมดการทำงาน
        lbl_mode = ctk.CTkLabel(
            self,
            text="⚙️ โหมดการทำงาน",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        lbl_mode.pack(pady=(20, 5), padx=20, anchor="w")

        self.seg_mode = ctk.CTkSegmentedButton(
            self,
            values=["เปรียบเทียบ (Compare)", "รวมเอกสาร (Single)", "Rename PDF"],
            command=self._on_mode_change,
        )
        self.seg_mode.pack(fill="x", padx=20, pady=(0, 15))
        self.seg_mode.set("เปรียบเทียบ (Compare)")

        # ส่วนที่ 1: เลือกโฟลเดอร์
        lbl_folders = ctk.CTkLabel(
            self,
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
            self, text="⚙️ การตั้งค่า", font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl_settings.pack(pady=(30, 10), padx=20, anchor="w")

        # DPI Slider
        frm_dpi = ctk.CTkFrame(self, fg_color="transparent")
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
        self.slider_dpi.configure(state="disabled")
        self.lbl_dpi_val.configure(text_color="gray")

        # Output Format
        lbl_format = ctk.CTkLabel(self, text="ไฟล์ผลลัพธ์:")
        lbl_format.pack(anchor="w", padx=20, pady=(15, 5))
        self.chk_docx = ctk.CTkCheckBox(
            self, text="สร้างไฟล์ DOCX", variable=self.gen_docx
        )
        self.chk_docx.pack(anchor="w", padx=30, pady=5)
        self.chk_docx.configure(state="disabled")

        self.chk_pdf = ctk.CTkCheckBox(
            self, text="สร้างไฟล์ PDF", variable=self.gen_pdf
        )
        self.chk_pdf.pack(anchor="w", padx=30, pady=5)
        self.chk_pdf.configure(state="disabled")

        self.chk_unmatched = ctk.CTkCheckBox(
            self, 
            text="รองรับเอกสารฝั่งเดียว (Allow Unmatched)", 
            variable=self.allow_unmatched,
            command=self._trigger_update_table
        )
        self.chk_unmatched.pack(anchor="w", padx=30, pady=5)

        # ส่วนที่ 2.5: เลือกประเภทเอกสาร (สำหรับโหมด Rename เท่านั้น)
        self.frm_doc_container = ctk.CTkFrame(self, fg_color="transparent")
        self.frm_doc_container.pack(fill="x", padx=0, pady=0)

        self.frm_doc_type = ctk.CTkFrame(self.frm_doc_container, fg_color="transparent")
        self.frm_doc_type.pack(fill="x", padx=20, pady=(15, 0))

        self.lbl_doc_type = ctk.CTkLabel(
            self.frm_doc_type,
            text="📝 ประเภทเอกสาร:",
            font=ctk.CTkFont(size=14),
        )
        self.lbl_doc_type.pack(anchor="w", pady=(0, 5))

        self.rb_etax = ctk.CTkRadioButton(
            self.frm_doc_type,
            text="e-Tax  (Prefix_ID1_ID2_ID3_..._S.pdf)",
            variable=self.doc_type_var,
            value="etax",
            command=self._trigger_update_table,
        )
        self.rb_etax.pack(anchor="w", padx=10, pady=2)

        self.rb_smart = ctk.CTkRadioButton(
            self.frm_doc_type,
            text="Smart Invoice  (Prefix_ID.pdf)",
            variable=self.doc_type_var,
            value="smart_invoice",
            command=self._trigger_update_table,
        )
        self.rb_smart.pack(anchor="w", padx=10, pady=2)

        self.lbl_matching_info = ctk.CTkLabel(
            self.frm_doc_type,
            text=(
                "ℹ️ เงื่อนไขการจับคู่ (Match Detect):\n"
                "• e-Tax: จับคู่ด้วย 3 กลุ่มแรกหลัง Prefix (ID1_ID2_ID3)\n"
                "  และอักขระท้ายสุด (Suffix)\n"
                "• Smart Invoice: จับคู่ด้วยชื่อไฟล์หลัง Prefix_ (ID.pdf)"
            ),
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="left",
        )
        self.lbl_matching_info.pack(anchor="w", padx=10, pady=(10, 0))

        # ซ่อนส่วนเลือกประเภทเอกสารเมื่อเริ่มต้น (ไม่ได้อยู่โหมด Rename)
        self.frm_doc_type.pack_forget()

        # ส่วนที่ 3: ปุ่มทำงาน
        self.btn_compare = ctk.CTkButton(
            self,
            text="🚀 เริ่มเปรียบเทียบ",
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.callbacks.get('start_task'),
        )
        self.btn_compare.pack(fill="x", padx=20, pady=20)

    def _create_folder_selector(self, label_text, string_var, command):
        lbl = ctk.CTkLabel(self, text=label_text)
        lbl.pack(anchor="w", padx=20, pady=(5, 0))

        frm = ctk.CTkFrame(self, fg_color="transparent")
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
        folder = filedialog.askdirectory(title="เลือกโฟลเดอร์ต้นฉบับ")
        if folder:
            self.dir_original.set(folder)
            self._trigger_update_table()

    def _select_rev_dir(self):
        folder = filedialog.askdirectory(title="เลือกโฟลเดอร์แก้ไข")
        if folder:
            self.dir_revised.set(folder)
            self._trigger_update_table()

    def _update_dpi_label(self, val):
        self.lbl_dpi_val.configure(text=f"ความละเอียด (DPI): {int(val)}")

    def _on_mode_change(self, value):
        if value == "รวมเอกสาร (Single)":
            self.op_mode.set("single")
            self.btn_rev.configure(state="disabled")
            self.lbl_rev.configure(text_color="gray")
            self.frm_doc_type.pack_forget()
            self.chk_unmatched.pack_forget()
            self.lbl_orig.configure(text="📂 โฟลเดอร์ต้นฉบับ (Original):")
            self.lbl_rev.configure(text="📂 โฟลเดอร์แก้ไข (Revised):")
            self.btn_compare.configure(text="🚀 เริ่มเปรียบเทียบ")

        elif value == "Rename PDF":
            self.op_mode.set("rename")
            self.btn_rev.configure(state="normal")
            self.lbl_rev.configure(text_color=["#000000", "#FFFFFF"])
            self.lbl_orig.configure(text="📂 โฟลเดอร์ต้นฉบับ (Source):")
            self.lbl_rev.configure(text="📂 โฟลเดอร์ปลายทาง (DDM):")
            self.frm_doc_type.pack(fill="x", padx=20, pady=(15, 0))
            self.btn_compare.configure(text="🚀 เริ่ม Rename")

        else:
            self.op_mode.set("compare")
            self.btn_rev.configure(state="normal")
            self.lbl_rev.configure(text_color=["#000000", "#FFFFFF"])
            self.frm_doc_type.pack_forget()
            
            # เรียง pack กลับเข้ามาที่เดิมคือใต้ Output format
            self.chk_unmatched.pack(anchor="w", padx=30, pady=5, after=self.chk_pdf)
            
            self.lbl_orig.configure(text="📂 โฟลเดอร์ต้นฉบับ (Original):")
            self.lbl_rev.configure(text="📂 โฟลเดอร์แก้ไข (Revised):")
            self.btn_compare.configure(text="🚀 เริ่มเปรียบเทียบ")

        self._trigger_update_table()

    def _trigger_update_table(self):
        if self.callbacks.get('update_table'):
            self.callbacks['update_table']()

    def set_processing_state(self, is_processing):
        """ควบคุมสถานะของปุ่มเมื่อทำงาน"""
        if is_processing:
            self.btn_compare.configure(state="disabled", text="⏳ กำลังประมวลผล...")
        else:
            mode = self.op_mode.get()
            btn_text = "🚀 เริ่ม Rename" if mode == "rename" else "🚀 เริ่มเปรียบเทียบ"
            self.btn_compare.configure(state="normal", text=btn_text)
