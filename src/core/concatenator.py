from PIL import Image, ImageDraw, ImageFont
import platform


def add_header_to_single_image(image: Image.Image, file_name: str = "") -> Image.Image:
    """
    ฟังก์ชันสำหรับโหมด Single Document:
    ขยายพื้นที่ภาพด้านบนให้เป็นส่วนหัว (Header) สไลด์ภาพเติมลงไป
    และวาดชื่อไฟล์ไว้ตรงกลาง เพื่อให้เอกสารดูมีระเบียบเหมือนในโหมด Compare

    Args:
        image (PIL.Image): ภาพ PDF หน้าเอกสาร
        file_name (str): ชื่อไฟล์ที่จะแสดงบนหัวกระดาษ

    Returns:
        PIL.Image: ภาพผืนใหม่ที่มี Header ข้อความ
    """
    if not file_name:
        return image

    width, height = image.size
    header_height = 60

    # สร้างผ้าใบอิมเมจใหม่ด้วยโหมด 'RGB' กำหนดพื้นหลังสีขาว
    canvas_height = height + header_height
    combined_canvas = Image.new("RGB", (width, canvas_height), color=(255, 255, 255))

    # วางภาพให้อยู่ด้านล่างพื้นที่ส่วนหัว
    combined_canvas.paste(image, (0, header_height))

    draw = ImageDraw.Draw(combined_canvas)

    try:
        if platform.system() == "Windows":
            font = ImageFont.truetype("arial.ttf", 18)
        else:
            font = ImageFont.load_default()
    except IOError:
        font = ImageFont.load_default()

    text_color = (0, 0, 0)  # สีดำ

    try:
        bbox = draw.textbbox((0, 0), file_name, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except AttributeError:
        text_width, text_height = draw.textsize(file_name, font=font)

    x = (width - text_width) // 2
    y = (header_height - text_height) // 2

    draw.text((x, y), file_name, font=font, fill=text_color)

    return combined_canvas


def concatenate_images_side_by_side(
    image_left: Image.Image, image_right: Image.Image, pair_name: str = ""
) -> Image.Image:
    """
    โมดูลการประมวลผลและผสานภาพ:
    คำนวณโครงสร้างและประกอบภาพสองภาพเคียงข้างกันทางแนวนอน (Side-by-side)
    พร้อมวาดชื่อไฟล์ (pair_name) ไว้ตรงกลางด้านบน

    Args:
        image_left (PIL.Image): ภาพ PDF ต้นฉบับที่จะวางฝั่งซ้าย
        image_right (PIL.Image): ภาพ PDF ฉบับแก้ไขที่จะวางฝั่งขวา
        pair_name (str): ชื่อไฟล์ที่จะแสดงบนหัวกระดาษ

    Returns:
        PIL.Image: ภาพผืนใหม่ที่เกิดจากการรวมทั้งสองภาพเข้าด้วยกัน
    """

    # ดึงค่าพิกัดความกว้างและความสูงของภาพทั้งสอง
    width_left, height_left = image_left.size
    width_right, height_right = image_right.size

    # กำหนดพื้นที่ส่วนหัว (Header) สำหรับวาดข้อความ
    header_height = 60 if pair_name else 0

    # คำนวณมิติของผืนผ้าใบใหม่
    # ความกว้าง = เอาความกว้างภาพซ้าย + ภาพขวา
    canvas_width = width_left + width_right
    # ความสูง = ยึดตามภาพที่สูงที่สุด + พื้นที่ส่วนหัว
    canvas_height = max(height_left, height_right) + header_height

    # สร้างผ้าใบอิมเมจใหม่ด้วยโหมด 'RGB' (รองรับ 24-bit color) กำหนดพื้นหลังสีขาว
    combined_canvas = Image.new(
        "RGB", (canvas_width, canvas_height), color=(255, 255, 255)
    )

    # วางภาพต้นฉบับฝั่งซ้าย เริ่มต้นที่จุดใต้ส่วนหัว (0, header_height)
    combined_canvas.paste(image_left, (0, header_height))

    # วางภาพเปรียบเทียบฝั่งขวา เริ่มต้นที่จุด (ความกว้างของภาพซ้าย, header_height)
    combined_canvas.paste(image_right, (width_left, header_height))

    if pair_name:
        draw = ImageDraw.Draw(combined_canvas)

        # พยายามโหลดฟอนต์ระบบ (รองรับ Windows เป็นหลัก เนื่องจากระบบเป็น Windows)
        try:
            if platform.system() == "Windows":
                font = ImageFont.truetype("arial.ttf", 18)
            else:
                # กรณีรันบน OS อื่นที่อาจไม่มี arial
                font = ImageFont.load_default()
        except IOError:
            # ใช้ฟอนต์ปริยายหากโหลดไม่สำเร็จ
            font = ImageFont.load_default()

        text_color = (0, 0, 0)  # สีดำ

        # หักลบหาจุดกึ่งกลางของข้อความ (ใช้ textbbox สำหรับ Pillow เวอร์ชันใหม่)
        try:
            bbox = draw.textbbox((0, 0), pair_name, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:  # เผื่อ Pillow เวอร์ชันเก่า
            text_width, text_height = draw.textsize(pair_name, font=font)

        # พิกัด x ให้กึ่งกลาง canvas, y ให้อยู่กึ่งกลาง header
        x = (canvas_width - text_width) // 2
        y = (header_height - text_height) // 2

        draw.text((x, y), pair_name, font=font, fill=text_color)

    return combined_canvas
