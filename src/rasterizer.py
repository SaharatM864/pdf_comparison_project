import fitz  # อินเทอร์เฟซของไลบรารี PyMuPDF
from PIL import Image
import io


def rasterize_pdf_to_image(
    pdf_path: str, page_num: int = 0, target_dpi: int = 150
) -> Image.Image:
    """
    โมดูลการสกัดและแปลงเป็นภาพ:
    ฟังก์ชันสกัดหน้าเอกสาร PDF ให้กลายเป็นออบเจ็กต์ภาพของไลบรารี Pillow
    โดยรับประกันความละเอียดตามเป้าหมาย (target_dpi) และจัดการข้อมูลผ่าน In-memory buffer

    Args:
        pdf_path (str): เส้นทางไปยังไฟล์ PDF
        page_num (int): หมายเลขหน้าเอกสารที่ต้องการสกัด (เริ่มต้นที่ index 0)
        target_dpi (int): ความละเอียดของภาพเป้าหมาย (ค่าเริ่มต้น 150 DPI เพื่อความสมดุลของหน่วยความจำ)

    Returns:
        PIL.Image: ออบเจ็กต์ภาพที่พร้อมนำไปประมวลผลต่อ
    """
    # 1. จัดสรรพอยน์เตอร์เพื่ออ่านไฟล์ PDF สู่หน่วยความจำ
    document_stream = fitz.open(pdf_path)

    try:
        # 2. โหลดโครงสร้างของหน้าที่ต้องการ
        page_data = document_stream.load_page(page_num)

        # 3. คำนวณ Transformation Matrix เพื่อปรับสมดุล DPI
        # อัตราส่วนการขยาย = DPI ที่ต้องการ / DPI ฐาน (72)
        magnification_ratio = target_dpi / 72.0
        transformation_matrix = fitz.Matrix(magnification_ratio, magnification_ratio)

        # 4. ส่งคำสั่งให้ MuPDF engine สร้างตารางบิตแมป (Rasterization)
        # การตั้งค่า alpha=False ขจัดการประมวลผลเลเยอร์ความโปร่งใสที่ไม่จำเป็นและบังคับพื้นหลังขาว
        pixmap = page_data.get_pixmap(matrix=transformation_matrix, alpha=False)

        # 5. ถ่ายโอนไบต์อาร์เรย์ (Byte Array) จาก Pixmap เข้าสู่หน่วยความจำชั่วคราว (I/O Buffer)
        image_bytes = io.BytesIO(pixmap.tobytes("png"))

        # แปลงโครงสร้างให้อยู่ในรูปแบบ PIL Image
        pil_image = Image.open(image_bytes)

        # คัดลอกภาพเพื่อตัดการเชื่อมต่อกับไฟล์ต้นฉบับก่อนคืนหน่วยความจำ
        pil_image.load()

        return pil_image

    finally:
        # ทำลายออบเจ็กต์ PDF ทิ้งเพื่อคืนหน่วยความจำกลับสู่ระบบปฏิบัติการอย่างปลอดภัย
        document_stream.close()
