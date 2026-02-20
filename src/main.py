import os
import time
import tkinter as tk
from tkinter import filedialog
import concurrent.futures
from typing import Tuple
from PIL import Image

# นำเข้าโมดูลต่างๆ ที่เราสร้างไว้
from matcher import get_matching_files
from rasterizer import rasterize_pdf_to_image
from concatenator import concatenate_images_side_by_side
from generator import generate_docx, generate_pdf


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
    file_name = os.path.basename(path_orig)

    # สกัดภาพจาก PDF (สมมติว่าเปรียบเทียบหน้าแรกสุดคือ page_num=0)
    img_orig = rasterize_pdf_to_image(path_orig, page_num=0, target_dpi=150)
    img_rev = rasterize_pdf_to_image(path_rev, page_num=0, target_dpi=150)

    # ผสานภาพซ้ายขวา
    integrated_image = concatenate_images_side_by_side(img_orig, img_rev)

    # ส่งคืน Index กลับไปเพื่อใช้เรียงลำดับ (Order Preservation) ให้ถูกต้องเหมือนเดิม
    return idx, integrated_image


def main():
    print("=" * 50)
    print("ระบบแปลงและเปรียบเทียบเอกสาร PDF อัตโนมัติ (Side-by-side)")
    print("=" * 50)

    # ให้ผู้ใช้เลือกโฟลเดอร์
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

    # สร้างโฟลเดอร์ output ถ้ายังไม่มี โดยยึดพิกัดเทียบกับโฟลเดอร์ src
    output_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "output")
    )
    os.makedirs(output_dir, exist_ok=True)

    OUT_DOCX = os.path.join(output_dir, "Comparison_Report.docx")
    OUT_PDF = os.path.join(output_dir, "Comparison_Report.pdf")

    start_time = time.time()

    try:
        # ระยะที่ 1: ดึงและจับคู่ไฟล์
        print("\n[ขั้นตอน 1] กำลังค้นหาและจับคู่ไฟล์เอกสาร...")
        matched_files = get_matching_files(DIR_ORIGINAL, DIR_REVISED)
        total_pairs = len(matched_files)
        print(f"\nพบเอกสารที่จับคู่ได้สมบูรณ์ทั้งหมด: {total_pairs} คู่ ({total_pairs * 2} ไฟล์)")

        if total_pairs == 0:
            print("ไม่พบไฟล์ที่จับคู่ได้ กรุณาตรวจสอบว่าชื่อไฟล์เริ่มต้นด้วยตัวเลข 3 หลักตรงกัน")
            return

        # สร้างอาเรย์ว่างเตรียมรับภาพตามจำนวนทั้งหมดเพื่อรักษาลำดับเดิมไว้
        accumulated_images = [None] * total_pairs

        # ระยะที่ 2 & 3: แปลง PDF เป็นภาพ และ นำมาต่อกัน (ทำงานแบบคู่ขนาน - Parallel Execution)
        print("\n[ขั้นตอน 2 & 3] กำลังแปลงและผสานภาพด้วยระบบคู่ขนาน (Parallel Processing)...")

        # ใช้ ThreadPoolExecutor เพื่อกระจายงาน (PyMuPDF คืน GIL ให้กับระบบระหว่างการเรนเดอร์ภาพ)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # จ่ายงานเข้าไปใน Thread Pool
            future_to_idx = {
                executor.submit(process_single_pair, idx, path_orig, path_rev): idx
                for idx, (path_orig, path_rev) in enumerate(matched_files)
            }

            # เก็บเกี่ยวผลลัพธ์ทันทีที่แต่ละ Thread ทำงานเสร็จสิ้น
            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_idx):
                original_idx = future_to_idx[future]
                try:
                    res_idx, integrated_img = future.result()
                    accumulated_images[res_idx] = (
                        integrated_img  # ยัดใส่กลับในตำแหน่ง Index เดิม
                    )
                    completed_count += 1

                    # หาสัดส่วนเปอร์เซ็นความคืบหน้า
                    progress_percent = (completed_count / total_pairs) * 100
                    print(
                        f"  -> ผสานคู่ที่ {original_idx + 1} สำเร็จ... ({progress_percent:.1f}%)"
                    )

                except Exception as exc:
                    print(f"  -> [ข้อผิดพลาด] คู่ที่ {original_idx + 1} ทำงานล้มเหลว: {exc}")

        # กรองรายการที่ Error ออก (กรอง None ทิ้ง) ป้องกันไม่ให้ report แครช
        accumulated_images = [img for img in accumulated_images if img is not None]

        if not accumulated_images:
            print("\nผลลัพธ์: ล้มเหลวไม่สามารถประมวลภาพได้เลยสักภาพเดียว ยกเลิกการสร้าง Report")
            return

        # ระยะที่ 4: สร้างเอกสารผลลัพธ์
        print("\n[ขั้นตอน 4] กำลังสร้างไฟล์ผลลัพธ์...")
        generate_docx(accumulated_images, OUT_DOCX)
        generate_pdf(accumulated_images, OUT_PDF)

        elapsed_time = time.time() - start_time
        print("\n" + "=" * 50)
        print(f"ดำเนินการเสร็จสิ้น 100%! ใช้เวลาไปทั้งหมด: {elapsed_time:.2f} วินาที")
        print("=" * 50)

    except Exception as e:
        print(f"\n[เกิดข้อผิดพลาด] {e}")


if __name__ == "__main__":
    main()
