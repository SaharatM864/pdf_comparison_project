import os


def rename_ddm_files(source_dir, dest_dir, doc_type, log_callback=None):
    """
    เปลี่ยนชื่อไฟล์ PDF ในโฟลเดอร์ปลายทาง (DDM) โดยเพิ่ม Prefix จากโฟลเดอร์ต้นฉบับ (Source)
    รองรับ 2 รูปแบบเอกสาร: e-Tax และ Smart Invoice

    Args:
        source_dir: เส้นทางโฟลเดอร์ต้นฉบับ (มี Prefix อยู่ในชื่อไฟล์)
        dest_dir: เส้นทางโฟลเดอร์ปลายทาง (ไฟล์ที่ต้องเพิ่ม Prefix)
        doc_type: ประเภทเอกสาร ('etax' หรือ 'smart_invoice')
        log_callback: ฟังก์ชันสำหรับส่ง Log กลับไป GUI (ถ้าไม่ระบุจะใช้ print)

    Returns:
        dict ผลลัพธ์: {total, skipped, matched, success, error}
        หรือ None ถ้าเกิดข้อผิดพลาดร้ายแรง (เช่น โฟลเดอร์ไม่พบ)
    """

    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    result = {"total": 0, "skipped": 0, "matched": 0, "success": 0, "error": 0}
    mapping = {}

    # === Step 1: สร้าง Mapping จากไฟล์ต้นฉบับ ===
    log("Step 1: กำลังวิเคราะห์ไฟล์ต้นฉบับ (Source)...")

    if not os.path.exists(source_dir):
        log(f"Error: ไม่พบโฟลเดอร์ต้นฉบับ: {source_dir}")
        return None

    source_files = [f for f in os.listdir(source_dir) if f.lower().endswith(".pdf")]

    for f in source_files:
        if doc_type == "etax":
            parts = f.split("_")
            # รูปแบบต้นฉบับ e-tax: Prefix_ID1_ID2_ID3_YYYY_MM_DD_..._S.pdf
            if len(parts) >= 5:
                prefix = parts[0]
                id_key = tuple(parts[1:4])
                suffix = parts[-1]
                mapping[(id_key, suffix)] = prefix

        elif doc_type == "smart_invoice":
            # รูปแบบต้นฉบับ smart-invoice: Prefix_ID.pdf (เช่น 001_015909067636.pdf)
            parts = f.split("_", 1)
            if len(parts) == 2:
                prefix = parts[0]
                key = parts[1]  # e.g., '015909067636.pdf'
                mapping[key] = prefix

    log(f"พบไฟล์ต้นฉบับ {len(source_files)} ไฟล์ → สร้าง Mapping ได้ {len(mapping)} รายการ")

    # === Step 2: ตรวจสอบและเปลี่ยนชื่อไฟล์ในโฟลเดอร์ DDM ===
    log("\nStep 2: กำลังเปลี่ยนชื่อไฟล์ปลายทาง (DDM)...")

    if not os.path.exists(dest_dir):
        log(f"Error: ไม่พบโฟลเดอร์ปลายทาง: {dest_dir}")
        return None

    dest_files = [f for f in os.listdir(dest_dir) if f.lower().endswith(".pdf")]
    result["total"] = len(dest_files)

    for f in dest_files:
        # ข้ามไฟล์ที่ถูกเปลี่ยนชื่อไปแล้ว (มี Prefix 3 หลัก + '_')
        if len(f) > 4 and f[0:3].isdigit() and f[3] == "_":
            result["skipped"] += 1
            continue

        key = None

        if doc_type == "etax":
            parts = f.split("_")
            # รูปแบบใน DDM e-tax: ID1_ID2_ID3_YYYY_MM_DD_..._S.pdf
            if len(parts) >= 4:
                id_key = tuple(parts[0:3])
                suffix = parts[-1]
                key = (id_key, suffix)

        elif doc_type == "smart_invoice":
            # รูปแบบใน DDM smart-invoice: ID.pdf (เช่น 015909067636.pdf)
            key = f

        # ถ้าพบ Key ใน Mapping ให้ทำการเปลี่ยนชื่อ
        if key and key in mapping:
            result["matched"] += 1
            prefix = mapping[key]
            new_name = f"{prefix}_{f}"

            old_path = os.path.join(dest_dir, f)
            new_path = os.path.join(dest_dir, new_name)

            try:
                os.rename(old_path, new_path)
                log(f"  ✅ {f} → {new_name}")
                result["success"] += 1
            except Exception as e:
                log(f"  ❌ ไม่สามารถเปลี่ยนชื่อ '{f}' → {e}")
                result["error"] += 1

    # === สรุปผล ===
    doc_label = "e-Tax" if doc_type == "etax" else "Smart Invoice"
    log("\n" + "=" * 50)
    log(f"📊 สรุปผลการทำงาน ({doc_label})")
    log("=" * 50)
    log(f"📄 จำนวนไฟล์ปลายทาง (DDM) ทั้งหมด : {result['total']} ไฟล์")
    log(f"⏭️  ข้ามไฟล์ที่เปลี่ยนชื่อไปแล้ว       : {result['skipped']} ไฟล์")
    log(f"🔍 ค้นพบข้อมูลที่ตรงกับต้นฉบับ       : {result['matched']} ไฟล์")
    log(f"✅ เปลี่ยนชื่อสำเร็จ                : {result['success']} ไฟล์")
    log(f"❌ เปลี่ยนชื่อไม่สำเร็จ (Error)      : {result['error']} ไฟล์")
    if result["error"] > 0:
        log("\n⚠️ มีไฟล์เปลี่ยนชื่อไม่สำเร็จ โปรดตรวจสอบว่าไม่ได้เปิดไฟล์ PDF ค้างไว้ในโปรแกรมอื่น")
    log("=" * 50)

    return result


def get_rename_preview(source_dir, dest_dir, doc_type):
    """
    แสดง Preview รายการไฟล์ที่จะถูก Rename (ไม่ทำการเปลี่ยนชื่อจริง)

    Returns:
        list ของ tuple (ชื่อเดิม, ชื่อใหม่) หรือ list ว่างถ้าไม่มีไฟล์ที่ต้อง Rename
    """
    if not source_dir or not os.path.exists(source_dir):
        return []
    if not dest_dir or not os.path.exists(dest_dir):
        return []

    mapping = {}

    source_files = [f for f in os.listdir(source_dir) if f.lower().endswith(".pdf")]

    for f in source_files:
        if doc_type == "etax":
            parts = f.split("_")
            if len(parts) >= 5:
                prefix = parts[0]
                id_key = tuple(parts[1:4])
                suffix = parts[-1]
                mapping[(id_key, suffix)] = prefix
        elif doc_type == "smart_invoice":
            parts = f.split("_", 1)
            if len(parts) == 2:
                prefix = parts[0]
                key = parts[1]
                mapping[key] = prefix

    dest_files = [f for f in os.listdir(dest_dir) if f.lower().endswith(".pdf")]
    preview = []

    for f in dest_files:
        # ข้ามไฟล์ที่เปลี่ยนชื่อแล้ว
        if len(f) > 4 and f[0:3].isdigit() and f[3] == "_":
            continue

        key = None
        if doc_type == "etax":
            parts = f.split("_")
            if len(parts) >= 4:
                id_key = tuple(parts[0:3])
                suffix = parts[-1]
                key = (id_key, suffix)
        elif doc_type == "smart_invoice":
            key = f

        if key and key in mapping:
            prefix = mapping[key]
            new_name = f"{prefix}_{f}"
            preview.append((f, new_name))

    return preview
