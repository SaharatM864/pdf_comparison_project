import fitz  # PyMuPDF
import platform


def prepare_single_pdf_page(pdf_path: str, file_name: str = "") -> fitz.Document:
    """
    ฟังก์ชันสำหรับโหมด Single (PDF-to-PDF):
    สร้างหน้า PDF ใหม่ที่มีพื้นที่ Header ด้านบน พร้อมวาดชื่อไฟล์ตรงกลาง
    แล้ววางเนื้อหาหน้าแรกของ PDF ต้นฉบับไว้ด้านล่าง
    โดยไม่ต้องแปลงเป็นรูปภาพ (คงไว้เป็น Vector Text ทั้งหมด)

    Args:
        pdf_path (str): เส้นทางไปยังไฟล์ PDF
        file_name (str): ชื่อไฟล์ที่จะแสดงเป็น Header (ไม่รวมนามสกุล)

    Returns:
        fitz.Document: ออบเจ็กต์เอกสาร PDF ใหม่ (ยังค้างในหน่วยความจำ ยังไม่ได้ save)
    """
    doc_src = fitz.open(pdf_path)

    try:
        page_src = doc_src[0]
        rect_src = page_src.rect
        width_src, height_src = rect_src.width, rect_src.height

        # พื้นที่ความสูงของ Header
        header_height = 50 if file_name else 0

        # คำนวณมิติของหน้ากระดาษใหม่
        canvas_width = width_src
        canvas_height = height_src + header_height

        # สร้างเอกสาร PDF ใหม่
        doc_out = fitz.open()
        new_page = doc_out.new_page(width=canvas_width, height=canvas_height)

        # วาดเนื้อหาจากหน้าต้นฉบับ (เลื่อนลงมาเท่ากับ header_height)
        dest_rect = fitz.Rect(0, header_height, width_src, header_height + height_src)
        new_page.show_pdf_page(dest_rect, doc_src, 0)

        # พิมพ์ข้อความชื่อไฟล์ด้านบนตรงกลาง
        if file_name:
            fontname = "helv"
            fontsize = 16

            text_length = fitz.get_text_length(
                file_name, fontname=fontname, fontsize=fontsize
            )

            x_pos = (canvas_width - text_length) / 2
            y_pos = (header_height / 2) + (fontsize / 3)

            new_page.insert_text(
                fitz.Point(x_pos, y_pos),
                file_name,
                fontname=fontname,
                fontsize=fontsize,
                color=(0, 0, 0),
            )

        return doc_out

    finally:
        doc_src.close()


def merge_pdfs_side_by_side(
    path_orig: str, path_rev: str, pair_name: str = ""
) -> fitz.Document:
    """
    ฟังก์ชันสำหรับโหมด Compare (PDF-to-PDF):
    ผสานหน้าแรกของ PDF สองไฟล์เข้าด้วยกันแบบเคียงข้าง (Side-by-side)
    โดยรักษาความเป็น Vector Text ของเอกสารเดิมไว้ทั้งหมด
    และเผื่อพื้นที่ด้านบนสำหรับเขียนชื่อไฟล์ (pair_name)

    Args:
        path_orig (str): เส้นทางไปยังไฟล์ PDF ต้นฉบับ
        path_rev (str): เส้นทางไปยังไฟล์ PDF ฉบับแก้ไข
        pair_name (str): ชื่อไฟล์คู่ที่จะแสดงเป็น Header

    Returns:
        fitz.Document: ออบเจ็กต์เอกสาร PDF ใหม่ที่เกิดจากการผสาน (ยังค้างในหน่วยความจำ ยังไม่ได้ save)
    """

    # เปิดไฟล์ทั้งสอง
    doc_left = fitz.open(path_orig)
    doc_right = fitz.open(path_rev)

    try:
        # สมมติว่าต้องการเปรียบเทียบแค่หน้าแรก (page 0)
        page_left = doc_left[0]
        page_right = doc_right[0]

        # ดึงขนาดกระดาษ
        rect_left = page_left.rect
        rect_right = page_right.rect

        width_left, height_left = rect_left.width, rect_left.height
        width_right, height_right = rect_right.width, rect_right.height

        # พื้นที่ความสูงของ Header
        header_height = 50 if pair_name else 0

        # คำนวณมิติของหน้ากระดาษใหม่ (Canvas)
        canvas_width = width_left + width_right
        canvas_height = max(height_left, height_right) + header_height

        # สร้างออบเจ็กต์ PDF ใหม่สำหรับรองรับหน้ากระดาษที่รวมแล้ว
        doc_merged = fitz.open()

        # สร้างหน้ากระดาษเปล่าใบใหม่ตามขนาดที่คำนวณไว้
        new_page = doc_merged.new_page(width=canvas_width, height=canvas_height)

        # วาดเนื้อหาจากหน้าต้นฉบับฝั่งซ้าย (เลื่อนหน้าลงมาเท่ากับระยะ header_height)
        dest_rect_left = fitz.Rect(
            0, header_height, width_left, header_height + height_left
        )
        new_page.show_pdf_page(dest_rect_left, doc_left, 0)

        # วาดเนื้อหาจากหน้าเปรียบเทียบฝั่งขวา (เลื่อน x ไปทางขวา = width_left)
        dest_rect_right = fitz.Rect(
            width_left,
            header_height,
            width_left + width_right,
            header_height + height_right,
        )
        new_page.show_pdf_page(dest_rect_right, doc_right, 0)

        # พิมพ์ข้อความชื่อไฟล์ด้านบน
        if pair_name:
            fontname = "helv"  # ฟอนต์มาตรฐานของ PDF
            fontsize = 16

            # คำนวณความกว้างของข้อความคร่าวๆ (fitz.get_text_length)
            text_length = fitz.get_text_length(
                pair_name, fontname=fontname, fontsize=fontsize
            )

            # จุดพิกัด (x, y) สำหรับใส่ข้อความ
            x_pos = (canvas_width - text_length) / 2
            y_pos = (header_height / 2) + (fontsize / 3)

            # เขียนข้อความ (สีดำ rgb=(0,0,0))
            new_page.insert_text(
                fitz.Point(x_pos, y_pos),
                pair_name,
                fontname=fontname,
                fontsize=fontsize,
                color=(0, 0, 0),
            )

        return doc_merged

    finally:
        # ปิดไฟล์เพื่อคืนหน่วยความจำ (ไฟล์ปลายทาง doc_merged ยังเปิดอยู่เพื่อนำไปใช้ต่อ)
        doc_left.close()
        doc_right.close()
