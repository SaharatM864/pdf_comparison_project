import os
import time
import tkinter as tk
from tkinter import filedialog
import concurrent.futures
from typing import Tuple, Union
import fitz  # PyMuPDF

# นำเข้าโมดูลต่างๆ ที่เราสร้างไว้ใน core
from src.core.matcher import get_matching_files, get_sorted_single_files
from src.core.pdf_merger import merge_pdfs_side_by_side, prepare_single_pdf_page


def select_directory(prompt: str) -> str:
    root = tk.Tk()
    root.withdraw()  # ซ่อนหน้าต่างหลัก GUI
    root.attributes("-topmost", True)  # บังคับให้อยู่บนสุด
    folder_path = filedialog.askdirectory(title=prompt)
    root.destroy()
    return folder_path


def process_single_file(
    idx: int, path_orig: str
) -> Tuple[int, Union[bytes, Exception]]:
    """
    ประมวลผลเอกสาร 1 ไฟล์แบบเบ็ดเสร็จสำหรับการรันแบบ Parallel โหมด Single (PDF-to-PDF)
    สร้างหน้า PDF ใหม่ที่มี Header ชื่อไฟล์ด้านบน แล้วคืนค่าเป็น bytes
    """
    try:
        # สกัดชื่อไฟล์เพื่อใช้เป็นหัวกระดาษ (ตัดนามสกุลออก)
        file_name = os.path.basename(path_orig)
        name_without_ext = os.path.splitext(file_name)[0]

        # สร้างหน้า PDF ใหม่พร้อม Header (Vector placement — ไม่แปลงเป็นรูปภาพ)
        doc_out = prepare_single_pdf_page(path_orig, file_name=name_without_ext)

        # ถ่ายโอนเป็นไบต์อาร์เรย์ใน memory
        pdf_bytes = doc_out.tobytes(garbage=4, deflate=True)
        doc_out.close()

        return idx, pdf_bytes
    except Exception as e:
        return idx, e


def process_single_pair(
    idx: int, path_orig: str, path_rev: str
) -> Tuple[int, Union[str, Exception]]:
    """
    ประมวลผลเอกสาร 1 คู่แบบเบ็ดเสร็จสำหรับการรันแบบ Parallel โหมด Compare (PDF-to-PDF)
    จะบันทึกเอกสาร 1 คู่เป็นไฟล์ PDF ชั่วคราว (หรือเก็บบริบทผ่าน ByteArray)
    เพื่อนำทุกคู่มาต่อกันรวมเป็นไฟลหลักใบเดียวในภายหลัง
    """
    try:
        # สกัดชื่อไฟล์เพื่อใช้เป็นหัวกระดาษ (ตัดนามสกุลออก)
        file_name = os.path.basename(path_orig)
        pair_name = os.path.splitext(file_name)[0]

        # ผสาน PDF ซ้ายขวา พร้อมระบุชื่อคู่ (จะได้ fitz.Document)
        doc_merged = merge_pdfs_side_by_side(path_orig, path_rev, pair_name=pair_name)

        # ถ่ายโอนไบต์อาร์เรย์ของ PDF ชั่วคราว (in memory) เพื่อตัดปัญหาสิทธิ์และหลีกเลี่ยงการสร้างขยะในระบบ
        pdf_bytes = doc_merged.tobytes(garbage=4, deflate=True)
        doc_merged.close()

        return idx, pdf_bytes
    except Exception as e:
        return idx, e


def run_comparison(
    dir_original: str,
    dir_revised: str,
    output_dir: str,
    mode: str = "compare",
    target_dpi: int = 150,
    page_num: int = 0,
    generate_docx_flag: bool = True,
    generate_pdf_flag: bool = True,
    progress_callback=None,
    log_callback=None,
) -> bool:
    """
    ฟังก์ชันหลักที่ทำการเรียบเรียงเอกสาร
    ส่งคืน True ถ้าสำเร็จ, False ถ้าล้มเหลว
    """

    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    start_time = time.time()

    try:
        if mode == "single":
            log("\n[ขั้นตอน 1] กำลังค้นหาและเรียงลำดับไฟล์เอกสาร (โหมดเดี่ยว)...")
            files_to_process = get_sorted_single_files(dir_original)
            total_items = len(files_to_process)
            log(f"\nพบเอกสารทั้งหมด: {total_items} ไฟล์")

            if total_items == 0:
                log("ไม่พบไฟล์ที่อ่านได้ กรุณาตรวจสอบรหัสเอกสาร")
                return False

        else:
            # ระยะที่ 1: ดึงและจับคู่ไฟล์
            log("\n[ขั้นตอน 1] กำลังค้นหาและจับคู่ไฟล์เอกสาร (โหมดเปรียบเทียบ)...")
            files_to_process = get_matching_files(dir_original, dir_revised)
            total_items = len(files_to_process)
            log(f"\nพบเอกสารที่จับคู่ได้สมบูรณ์ทั้งหมด: {total_items} คู่ ({total_items * 2} ไฟล์)")

            if total_items == 0:
                log("ไม่พบไฟล์ที่จับคู่ได้ กรุณาตรวจสอบรหัสเอกสาร หรือตรวจว่าเลือกไฟล์ถูกโฟลเดอร์หรือไม่")
                return False

        # สร้างอาเรย์ว่างเตรียมรับผลลัพธ์และรักษาลำดับ (Order Preservation)
        accumulated_results = [None] * total_items

        # ระยะที่ 2 & 3: แปลง/ผสาน ด้วยระบบคู่ขนาน (Parallel Processing)
        if mode == "single":
            log(
                "\n[ขั้นตอน 2 & 3] กำลังผสานหน้า PDF คู่ขนาน (โหมด Single - Vector placement)..."
            )
        else:
            log(
                "\n[ขั้นตอน 2 & 3] กำลังผสานหน้า PDF คู่ขนาน (โหมด Compare - Vector placement)..."
            )

        # ใช้ ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            if mode == "single":
                future_to_idx = {
                    executor.submit(process_single_file, idx, path_orig): idx
                    for idx, path_orig in enumerate(files_to_process)
                }
            else:
                future_to_idx = {
                    executor.submit(process_single_pair, idx, pair[0], pair[1]): idx
                    for idx, pair in enumerate(files_to_process)
                }

            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_idx):
                original_idx = future_to_idx[future]
                try:
                    res_idx, processed_item = future.result()

                    if isinstance(processed_item, Exception):
                        raise processed_item

                    accumulated_results[res_idx] = processed_item
                    completed_count += 1

                    progress_percent = (completed_count / total_items) * 100
                    log(
                        f"  -> ประมวลผลรายการที่ {original_idx + 1} สำเร็จ... ({progress_percent:.1f}%)"
                    )

                    if progress_callback:
                        progress_callback(completed_count, total_items)

                except Exception as exc:
                    log(
                        f"  -> [ข้อผิดพลาด] รายการที่ {original_idx + 1} ทำงานล้มเหลว: {exc}"
                    )

        # กรองรายการที่ Error ออกไป
        accumulated_results = [res for res in accumulated_results if res is not None]

        if not accumulated_results:
            log("\nผลลัพธ์: ล้มเหลวไม่มีผลลัพธ์ที่ประมวลผลผ่านเลย ยกเลิกการสร้าง Report")
            return False

        # ระยะที่ 4: สร้างเอกสารผลลัพธ์
        log("\n[ขั้นตอน 4] กำลังรวมเล่มเพื่อสร้างไฟล์ตารางผลลัพธ์ (Final Output)...")

        # ทั้งโหมด single และ compare ตอนนี้ accumulated_results บรรจุ PDF bytes ทั้งคู่
        if generate_pdf_flag:
            suffix = "_Single" if mode == "single" else ""
            out_pdf = os.path.join(output_dir, f"Comparison_Report{suffix}.pdf")

            # ประกาศ PDF หลักสำหรับรับหน้าเอกสารต่างๆ นำมารวมเล่ม
            main_pdf = fitz.open()
            for pdf_bytes in accumulated_results:
                # แปลง bytes กลับเป็น Document ชั่วคราวและแทรกเข้าไปใน PDF หลัก
                temp_doc = fitz.open("pdf", pdf_bytes)
                main_pdf.insert_pdf(temp_doc)
                temp_doc.close()

            # บันทึกไฟล์ที่แทรกทุกหน้าสมบูรณ์แล้ว
            main_pdf.save(out_pdf, garbage=4, deflate=True)
            main_pdf.close()
            log(f"[สำเร็จ] รายงานผลลัพธ์ PDF รูปแบบ Vector ถูกบันทึกที่: {out_pdf}")

        elapsed_time = time.time() - start_time
        log("\n" + "=" * 50)
        log(f"ดำเนินการเสร็จสิ้น 100%! ใช้เวลาไปทั้งหมด: {elapsed_time:.2f} วินาที")
        log("=" * 50)

        return True

    except Exception as e:
        log(f"\n[เกิดข้อผิดพลาด] {e}")
        return False


def main():
    print("=" * 50)
    print("ระบบแปลงและเปรียบเทียบเอกสาร PDF อัตโนมัติ (Vector placement)")
    print("=" * 50)

    print("\nกรุณาเลือกโฟลเดอร์สำหรับ [เอกสารต้นฉบับ]")
    DIR_ORIGINAL = select_directory("เลือกโฟลเดอร์เอกสารต้นฉบับ (Original)")
    if not DIR_ORIGINAL:
        print("ยกเลิกการทำงาน: ไม่ได้เลือกโฟลเดอร์ต้นฉบับ")
        return

    print("กรุณาเลือกโฟลเดอร์สำหรับ [เอกสารแก้ไข]")
    DIR_REVISED = select_directory("เลือกโฟลเดอร์เอกสารแก้ไข (Revised)")
    if not DIR_REVISED:
        print("ยกเลิกการทำงาน: ไม่ได้เลือกโฟลเดอร์แก้ไข")
        return

    output_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "output")
    )
    os.makedirs(output_dir, exist_ok=True)

    run_comparison(
        dir_original=DIR_ORIGINAL,
        dir_revised=DIR_REVISED,
        output_dir=output_dir,
        target_dpi=150,
        page_num=0,
        mode="compare",
        generate_docx_flag=False,
        generate_pdf_flag=True,
    )


if __name__ == "__main__":
    main()
