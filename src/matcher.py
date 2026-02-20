import os
from typing import List, Tuple

def get_matching_files(dir_original: str, dir_revised: str) -> List[Tuple[str, str]]:
    """
    โมดูลการจับคู่และเตรียมข้อมูล:
    อ่านไฟล์จากโฟลเดอร์ต้นฉบับและโฟลเดอร์เปรียบเทียบ จัดเรียงตามลำดับพจนานุกรม 
    เพื่อรับประกันการจับคู่ที่ถูกต้องแม่นยำ
    
    Returns:
        List ของ Tuple ที่บรรจุ (เส้นทางไฟล์ต้นฉบับ, เส้นทางไฟล์เปรียบเทียบ)
    """
    
    # ดึงรายชื่อไฟล์และบังคับการจัดเรียงตามลำดับพจนานุกรม
    try:
        files_orig = sorted(os.listdir(dir_original))
        files_rev = sorted(os.listdir(dir_revised))
    except FileNotFoundError as e:
        raise FileNotFoundError(f"ไม่พบโฟลเดอร์ที่ระบุ: {e}")

    # คัดกรองเอาเฉพาะไฟล์ .pdf เผื่อมีไฟล์ขยะซ่อนอยู่ (เช่น .DS_Store หรือ thumbs.db)
    files_orig = [f for f in files_orig if f.lower().endswith('.pdf')]
    files_rev = [f for f in files_rev if f.lower().endswith('.pdf')]

    # ตรวจสอบความสมบูรณ์ของชุดข้อมูล (Data Integrity Check)
    if len(files_orig) != len(files_rev):
        raise ValueError(
            f"ข้อผิดพลาดทางสถาปัตยกรรม: จำนวนไฟล์ระหว่างสองแหล่งข้อมูลไม่สมดุลกัน "
            f"(ต้นฉบับ: {len(files_orig)} ไฟล์, แก้ไข: {len(files_rev)} ไฟล์)"
        )

    matched_paths = []
    
    # จับคู่ชื่อไฟล์และสร้างเส้นทางไฟล์สัมบูรณ์ (Absolute/Relative Paths)
    for f_orig, f_rev in zip(files_orig, files_rev):
        path_orig = os.path.join(dir_original, f_orig)
        path_rev = os.path.join(dir_revised, f_rev)
        matched_paths.append((path_orig, path_rev))

    return matched_paths