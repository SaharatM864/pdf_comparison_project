import os
import sys

# เพิ่มโฟลเดอร์ปัจจุบันเข้าไปใน path เพื่อให้ python หามอพดูล src เจอ
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.ui.app import PDFComparisonApp

if __name__ == "__main__":
    app = PDFComparisonApp()
    app.mainloop()
