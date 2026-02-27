import os
import time
import tkinter as tk
from tkinter import filedialog
import concurrent.futures
from typing import Tuple
from PIL import Image

# นำเข้าโมดูลต่างๆ ที่เราสร้างไว้ใน core
from src.core.matcher import get_matching_files
from src.core.rasterizer import rasterize_pdf_to_image
from src.core.concatenator import concatenate_images_side_by_side
from src.core.generator import generate_docx, generate_pdf


def select_directory(prompt: str) -> str:
    root = tk.Tk()
    root.withdraw()  # ซ่อนหน้าต่างหลัก GUI
    root.attributes("-topmost", True)  # บังคับให้อยู่บนสุด
    folder_path = filedialog.askdirectory(title=prompt)
    root.destroy()
    return folder_path


def process_single_pair(
    idx: int, path_orig: str, path_rev: str
) -> Tuple[int, Image.Image]:
    """
    ประมวลผลเอกสาร 1 คู่แบบเบ็ดเสร็จสำหรับการรันแบบ Parallel (Type-safe)
    """
    # สกัดชื่อไฟล์เพื่อใช้เป็นหัวกระดาษ (ตัดนามสกุลออก)
    file_name = os.path.basename(path_orig)
    pair_name = os.path.splitext(file_name)[0]

    # สกัดภาพจาก PDF (สมมติว่าเปรียบเทียบหน้าแรกสุดคือ page_num=0)
    img_orig = rasterize_pdf_to_image(path_orig, page_num=0, target_dpi=150)
    img_rev = rasterize_pdf_to_image(path_rev, page_num=0, target_dpi=150)

    # ผสานภาพซ้ายขวา พร้อมระบุชื่อคู่
    integrated_image = concatenate_images_side_by_side(
        img_orig, img_rev, pair_name=pair_name
    )

    # ส่งคืน Index กลับไปเพื่อใช้เรียงลำดับ (Order Preservation) ให้ถูกต้องเหมือนเดิม
    return idx, integrated_image


def run_comparison(
    dir_original: str,
    dir_revised: str,
    output_dir: str,
    target_dpi: int = 150,
    page_num: int = 0,
    generate_docx_flag: bool = True,
    generate_pdf_flag: bool = True,
    progress_callback=None,
    log_callback=None,
) -> bool:
    """
    ฟังก์ชันหลักที่ทำการเปรียบเทียบเอกสาร PDF
    ส่งคืน True ถ้าสำเร็จ, False ถ้าล้มเหลว
    """

    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    start_time = time.time()

    try:
        # ระยะที่ 1: ดึงและจับคู่ไฟล์
        log("\n[ขั้นตอน 1] กำลังค้นหาและจับคู่ไฟล์เอกสาร...")
        matched_files = get_matching_files(dir_original, dir_revised)
        total_pairs = len(matched_files)
        log(f"\nพบเอกสารที่จับคู่ได้สมบูรณ์ทั้งหมด: {total_pairs} คู่ ({total_pairs * 2} ไฟล์)")

        if total_pairs == 0:
            log("ไม่พบไฟล์ที่จับคู่ได้ กรุณาตรวจสอบว่าชื่อไฟล์เริ่มต้นด้วยตัวเลข 3 หลักตรงกัน")
            return False

        # สร้างอาเรย์ว่างเตรียมรับภาพตามจำนวนทั้งหมดเพื่อรักษาลำดับเดิมไว้
        accumulated_images = [None] * total_pairs

        # ระยะที่ 2 & 3: แปลง PDF เป็นภาพ และ นำมาต่อกัน
        log("\n[ขั้นตอน 2 & 3] กำลังแปลงและผสานภาพด้วยระบบคู่ขนาน (Parallel Processing)...")

        # ใช้ ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_idx = {
                executor.submit(process_single_pair, idx, path_orig, path_rev): idx
                for idx, (path_orig, path_rev) in enumerate(matched_files)
            }

            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_idx):
                original_idx = future_to_idx[future]
                try:
                    res_idx, integrated_img = future.result()
                    accumulated_images[res_idx] = integrated_img
                    completed_count += 1

                    progress_percent = (completed_count / total_pairs) * 100
                    log(
                        f"  -> ผสานคู่ที่ {original_idx + 1} สำเร็จ... ({progress_percent:.1f}%)"
                    )

                    if progress_callback:
                        progress_callback(completed_count, total_pairs)

                except Exception as exc:
                    log(f"  -> [ข้อผิดพลาด] คู่ที่ {original_idx + 1} ทำงานล้มเหลว: {exc}")

        # กรองรายการที่ Error ออก
        accumulated_images = [img for img in accumulated_images if img is not None]

        if not accumulated_images:
            log("\nผลลัพธ์: ล้มเหลวไม่สามารถประมวลภาพได้เลยสักภาพเดียว ยกเลิกการสร้าง Report")
            return False

        # ระยะที่ 4: สร้างเอกสารผลลัพธ์
        log("\n[ขั้นตอน 4] กำลังสร้างไฟล์ผลลัพธ์...")

        if generate_docx_flag:
            out_docx = os.path.join(output_dir, "Comparison_Report.docx")
            generate_docx(accumulated_images, out_docx)
            log(f"[สำเร็จ] รายงานผลลัพธ์ DOCX ถูกบันทึกที่: {out_docx}")

        if generate_pdf_flag:
            out_pdf = os.path.join(output_dir, "Comparison_Report.pdf")
            generate_pdf(accumulated_images, out_pdf)
            log(f"[สำเร็จ] รายงานผลลัพธ์ PDF ถูกบันทึกที่: {out_pdf}")

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
    print("ระบบแปลงและเปรียบเทียบเอกสาร PDF อัตโนมัติ (Side-by-side)")
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
        generate_docx_flag=True,
        generate_pdf_flag=True,
    )


if __name__ == "__main__":
    main()
