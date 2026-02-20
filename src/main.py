import os
import time

# นำเข้าโมดูลต่างๆ ที่เราสร้างไว้
from matcher import get_matching_files
from rasterizer import rasterize_pdf_to_image
from concatenator import concatenate_images_side_by_side
from generator import generate_docx, generate_pdf


def main():
    # กำหนดเส้นทางไดเรกทอรี (อ้างอิงจากโฟลเดอร์หลัก pdf_comparison_project)
    DIR_ORIGINAL = "../data/original_docs"
    DIR_REVISED = "../data/revised_docs"
    OUT_DOCX = "../output/Comparison_Report.docx"
    OUT_PDF = "../output/Comparison_Report.pdf"

    print("=" * 50)
    print("ระบบแปลงและเปรียบเทียบเอกสาร PDF อัตโนมัติ (Side-by-side)")
    print("=" * 50)

    start_time = time.time()

    try:
        # ระยะที่ 1: ดึงและจับคู่ไฟล์
        print("[ขั้นตอน 1] กำลังค้นหาและจับคู่ไฟล์เอกสาร...")
        matched_files = get_matching_files(DIR_ORIGINAL, DIR_REVISED)
        total_pairs = len(matched_files)
        print(f"พบเอกสารที่จับคู่ได้ทั้งหมด: {total_pairs} คู่ ({total_pairs * 2} ไฟล์)")

        if total_pairs == 0:
            print(
                "ไม่พบไฟล์ในโฟลเดอร์ กรุณานำไฟล์ PDF ไปใส่ในโฟลเดอร์ data/original_docs และ data/revised_docs"
            )
            return

        accumulated_images = []

        # ระยะที่ 2 & 3: แปลง PDF เป็นภาพ และ นำมาต่อกัน
        print("\n[ขั้นตอน 2 & 3] กำลังแปลงและผสานภาพ...")
        for idx, (path_orig, path_rev) in enumerate(matched_files):
            file_name = os.path.basename(path_orig)
            print(f"  -> กำลังประมวลผลคู่ที่ {idx + 1}/{total_pairs}: {file_name}")

            # สกัดภาพจาก PDF (สมมติว่าเปรียบเทียบหน้าแรกสุดคือ page_num=0)
            img_orig = rasterize_pdf_to_image(path_orig, page_num=0, target_dpi=150)
            img_rev = rasterize_pdf_to_image(path_rev, page_num=0, target_dpi=150)

            # ผสานภาพซ้ายขวา
            integrated_image = concatenate_images_side_by_side(img_orig, img_rev)
            accumulated_images.append(integrated_image)

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
