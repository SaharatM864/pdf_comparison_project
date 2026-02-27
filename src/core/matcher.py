import os
import re
from typing import List, Tuple


def get_sorted_single_files(dir_path: str) -> List[str]:
    """
    ฟังก์ชันสำหรับโหมด Single Document:
    อ่านไฟล์จากโฟลเดอร์เดียว ดึงเฉพาะไฟล์ที่เริ่มต้นด้วยตัวเลข 3 หลัก
    แล้วทำการจัดเรียงให้ถูกต้องตามลำดับ Prefix

    Returns:
        List ของเส้นทางไฟล์ (Absolute path) ที่ถูกจัดเรียงแล้ว
    """
    try:
        files = os.listdir(dir_path)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"ไม่พบโฟลเดอร์ที่ระบุ: {e}")

    # คัดกรองเอาเฉพาะไฟล์ .pdf
    files = [f for f in files if f.lower().endswith(".pdf")]

    # Regex สำหรับดึงตัวเลข 3 หลักแรก
    pattern = re.compile(r"^(\d{3})")

    dict_files = {}
    for f in files:
        match = pattern.search(f)
        if match:
            dict_files[match.group(1)] = f
        else:
            print(f"[คำเตือน] ไฟล์ข้ามการตรวจสอบ (ไม่มีตัวเลข 3 หลักนำหน้า): {f}")

    sorted_paths = []
    # จัดเรียงตาม keys (Prefix 3 หลัก) ให้ข้อมูลเรียงร้อยจาก 001 ไป 999
    for key in sorted(dict_files.keys()):
        sorted_paths.append(os.path.join(dir_path, dict_files[key]))

    return sorted_paths


def get_matching_files(dir_original: str, dir_revised: str) -> List[Tuple[str, str]]:
    """
    โมดูลการจับคู่และเตรียมข้อมูล:
    อ่านไฟล์จากโฟลเดอร์ต้นฉบับและโฟลเดอร์เปรียบเทียบ ดึงตัวเลข 3 หลักแรกจากชื่อไฟล์
    และทำการจับคู่ด้วย Prefix เพื่อรับประกันความถูกต้องแทนการจัดเรียงตายตัว

    Returns:
        List ของ Tuple ที่บรรจุ (เส้นทางไฟล์ต้นฉบับ, เส้นทางไฟล์เปรียบเทียบ)
    """

    try:
        files_orig = os.listdir(dir_original)
        files_rev = os.listdir(dir_revised)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"ไม่พบโฟลเดอร์ที่ระบุ: {e}")

    # คัดกรองเอาเฉพาะไฟล์ .pdf เผื่อมีไฟล์ขยะซ่อนอยู่ (เช่น .DS_Store หรือ thumbs.db)
    files_orig = [f for f in files_orig if f.lower().endswith(".pdf")]
    files_rev = [f for f in files_rev if f.lower().endswith(".pdf")]

    # Regex สำหรับดึงตัวเลข 3 หลักแรกที่ปรากฏในตอนต้นของชื่อไฟล์
    pattern = re.compile(r"^(\d{3})")

    dict_orig = {}
    for f in files_orig:
        match = pattern.search(f)
        if match:
            dict_orig[match.group(1)] = f
        else:
            print(f"[คำเตือน] ไฟล์ต้นฉบับข้ามการตรวจสอบ (ไม่มีตัวเลข 3 หลักนำหน้า): {f}")

    dict_rev = {}
    for f in files_rev:
        match = pattern.search(f)
        if match:
            dict_rev[match.group(1)] = f
        else:
            print(f"[คำเตือน] ไฟล์แก้ไขข้ามการตรวจสอบ (ไม่มีตัวเลข 3 หลักนำหน้า): {f}")

    matched_paths = []

    # ค้นหา keys ทั้งหมดเพื่อตรวจสอบคู่ที่ไม่สมบูรณ์
    all_keys = set(dict_orig.keys()).union(set(dict_rev.keys()))

    for key in sorted(all_keys):
        if key in dict_orig and key in dict_rev:
            path_orig = os.path.join(dir_original, dict_orig[key])
            path_rev = os.path.join(dir_revised, dict_rev[key])
            matched_paths.append((path_orig, path_rev))
        elif key in dict_orig:
            print(
                f"[คำเตือน] พบไฟล์ต้นฉบับรหัส {key} ({dict_orig[key]}) แต่ไม่พบไฟล์แก้ไขที่ตรงกัน"
            )
        else:
            print(f"[คำเตือน] พบไฟล์แก้ไขรหัส {key} ({dict_rev[key]}) แต่ไม่พบไฟล์ต้นฉบับที่ตรงกัน")

    return matched_paths
