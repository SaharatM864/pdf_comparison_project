from PIL import Image


def concatenate_images_side_by_side(
    image_left: Image.Image, image_right: Image.Image
) -> Image.Image:
    """
    โมดูลการประมวลผลและผสานภาพ:
    คำนวณโครงสร้างและประกอบภาพสองภาพเคียงข้างกันทางแนวนอน (Side-by-side)

    Args:
        image_left (PIL.Image): ภาพ PDF ต้นฉบับที่จะวางฝั่งซ้าย
        image_right (PIL.Image): ภาพ PDF ฉบับแก้ไขที่จะวางฝั่งขวา

    Returns:
        PIL.Image: ภาพผืนใหม่ที่เกิดจากการรวมทั้งสองภาพเข้าด้วยกัน
    """

    # ดึงค่าพิกัดความกว้างและความสูงของภาพทั้งสอง
    width_left, height_left = image_left.size
    width_right, height_right = image_right.size

    # คำนวณมิติของผืนผ้าใบใหม่
    # ความกว้าง = เอาความกว้างภาพซ้าย + ภาพขวา
    canvas_width = width_left + width_right
    # ความสูง = ยึดตามภาพที่สูงที่สุด เพื่อป้องกันภาพโดนตัด
    canvas_height = max(height_left, height_right)

    # สร้างผ้าใบอิมเมจใหม่ด้วยโหมด 'RGB' (รองรับ 24-bit color) กำหนดพื้นหลังสีขาว
    combined_canvas = Image.new(
        "RGB", (canvas_width, canvas_height), color=(255, 255, 255)
    )

    # วางภาพต้นฉบับฝั่งซ้าย เริ่มต้นที่จุดพิกัดกำเนิด (0, 0)
    combined_canvas.paste(image_left, (0, 0))

    # วางภาพเปรียบเทียบฝั่งขวา เริ่มต้นที่จุดพิกัด (ความกว้างของภาพซ้าย, 0)
    combined_canvas.paste(image_right, (width_left, 0))

    return combined_canvas
