import base64
import hashlib
import json
from datetime import date
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent
QUESTION_DIR = ROOT / "questions_json"
AUDIT_PATH = ROOT / "data_audits" / "question-images-2026-09-17.json"
SOURCE_DIR = Path(r"C:\Users\admin\Desktop\課程\AIOT\PDF\AIOT-ORI-QUIZ")
MANUAL_SOURCE_DIR = ROOT / "source_assets" / "question_images"

IMAGE_MAP = [
    ("108-2-U2.json", 43, "108-2-U2.pdf", 8, "Apache Tomcat 貓咪商標圖樣"),
    ("109-1-U1.json", 9, "109-1-U1.pdf", 2, "氣體濃度輸入與電壓輸出的磁滯曲線圖"),
    ("109-1-U1.json", 50, "109-1-U1.pdf", 9, "美國 Macy's 賣場商品吊牌照片"),
    ("109-1-U2.json", 13, "109-1-U2.pdf", 3, "樹莓派桌面右上角顯示黃色閃電符號"),
    ("109-1-U2.json", 44, "109-1-U2.pdf", 9, "標示 1、2、3 三層的雲端服務金字塔"),
    ("110-2-U2.json", 9, "110-2-U2.pdf", 2, "Raspberry Pi、micro:bit 與 Arduino 三種嵌入式開發板"),
    ("110-2-U2.json", 30, "110-2-U2.pdf", 6, "CC BY-NC-SA 創用 CC 授權圖示"),
    ("110-2-U2.json", 35, "110-2-U2.pdf", 7, "HC-06 藍牙模組及 VCC、GND、TXD、RXD 接腳"),
    ("111-2-U1.json", 17, "111-2-U1.pdf", 4, "RFID 系統五個運作項目的順序圖"),
    ("111-2-U2.json", 15, "111-2-U2.pdf", 3, "Arduino、按鈕、電阻與 LED 的連接電路"),
    ("111-2-U2.json", 22, "111-2-U2.pdf", 4, "Arduino LED 控制程式碼"),
    ("111-2-U2.json", 27, "111-2-U2.pdf", 6, "樹莓派、麵包板、按鈕與電阻的接線圖"),
    ("112-1-U2.json", 27, "112-1-U2.pdf", 6, "Arduino 驅動極性相反雙色 LED 的電路圖"),
    ("112-2-U1.json", 14, "112-2-U1.pdf", 3, "含 EPC 標誌的一般商品吊牌示意圖"),
    ("112-2-U1.json", 25, "112-2-U1.pdf", 6, "ZigBee Mesh 網路節點與路徑成本圖"),
    ("113-2-U2.json", 33, "113-2-U2.pdf", 7, "具半球形感測罩的紅外線移動感測器"),
    ("113-2-U2.json", 35, "113-2-U2.pdf", 8, "Arduino Uno 與四組按鈕接線選項圖"),
]

MANUAL_IMAGE_MAP = [
    (
        "114-1-U1.json",
        48,
        "114-1-U1-Q48.png",
        "含條碼、SGTIN 資料與 RFID 圖示的商品標籤照片",
    ),
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, value):
    with path.open("w", encoding="utf-8", newline="\r\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def find_question(data, question_id):
    for question in data["questions"]:
        if int(question["id"]) == question_id:
            return question
    raise ValueError(f"找不到第 {question_id} 題")


def extract_question_image(pdf_path, page_number):
    page = PdfReader(pdf_path).pages[page_number - 1]
    candidates = []
    for image in page.images:
        width, height = image.image.size
        if width >= 100 and height >= 80:
            candidates.append((image, width, height))
    if len(candidates) != 1:
        raise ValueError(
            f"{pdf_path.name} 第 {page_number} 頁預期 1 張題圖，實際為 {len(candidates)} 張"
        )
    return candidates[0]


def mime_type_for(image):
    image_format = str(image.image.format or "").upper()
    if image_format in {"JPG", "JPEG"}:
        return "image/jpeg"
    if image_format == "PNG":
        return "image/png"
    raise ValueError(f"不支援的圖片格式：{image_format}")


def main():
    cache = {}
    audit_items = []

    for json_name, question_id, pdf_name, page_number, alt in IMAGE_MAP:
        json_path = QUESTION_DIR / json_name
        pdf_path = SOURCE_DIR / pdf_name
        if not pdf_path.exists():
            raise FileNotFoundError(pdf_path)

        data = cache.setdefault(json_path, load_json(json_path))
        question = find_question(data, question_id)
        image, width, height = extract_question_image(pdf_path, page_number)
        mime_type = mime_type_for(image)
        digest = hashlib.sha256(image.data).hexdigest()
        encoded = base64.b64encode(image.data).decode("ascii")

        question["image"] = {
            "dataUrl": f"data:{mime_type};base64,{encoded}",
            "mimeType": mime_type,
            "alt": alt,
            "width": width,
            "height": height,
            "source": {
                "pdf": pdf_name,
                "page": page_number,
                "sha256": digest,
            },
        }

        audit_items.append(
            {
                "questionFile": json_name,
                "questionId": question_id,
                "sourcePdf": pdf_name,
                "sourcePage": page_number,
                "mimeType": mime_type,
                "width": width,
                "height": height,
                "sha256": digest,
                "alt": alt,
            }
        )

    for json_name, question_id, image_name, alt in MANUAL_IMAGE_MAP:
        json_path = QUESTION_DIR / json_name
        image_path = MANUAL_SOURCE_DIR / image_name
        if not image_path.exists():
            raise FileNotFoundError(image_path)

        data = cache.setdefault(json_path, load_json(json_path))
        question = find_question(data, question_id)
        raw = image_path.read_bytes()
        with Image.open(image_path) as image:
            width, height = image.size
            image_format = str(image.format or "").upper()
        if image_format != "PNG":
            raise ValueError(f"不支援的手動題圖格式：{image_format}")

        mime_type = "image/png"
        digest = hashlib.sha256(raw).hexdigest()
        encoded = base64.b64encode(raw).decode("ascii")
        relative_source = image_path.relative_to(ROOT).as_posix()

        question["image"] = {
            "dataUrl": f"data:{mime_type};base64,{encoded}",
            "mimeType": mime_type,
            "alt": alt,
            "width": width,
            "height": height,
            "source": {
                "imageFile": relative_source,
                "providedBy": "user",
                "sha256": digest,
            },
        }

        audit_items.append(
            {
                "questionFile": json_name,
                "questionId": question_id,
                "sourceType": "user-provided-image",
                "sourceImage": relative_source,
                "mimeType": mime_type,
                "width": width,
                "height": height,
                "sha256": digest,
                "alt": alt,
            }
        )

    for path, data in cache.items():
        save_json(path, data)

    audit = {
        "auditDate": date.today().isoformat(),
        "sourceDirectory": str(SOURCE_DIR),
        "manualSourceDirectory": str(MANUAL_SOURCE_DIR),
        "embeddedImageCount": len(audit_items),
        "modifiedQuestionFileCount": len(cache),
        "items": audit_items,
        "notEmbedded": [
            {
                "questionFile": "111-1-U2.json",
                "questionId": 26,
                "reason": "官方 PDF 沒有獨立題圖；規格內容已完整保留在 JSON 題幹中。",
            },
        ],
    }
    save_json(AUDIT_PATH, audit)

    print(f"embedded={len(audit_items)}")
    print(f"modified_files={len(cache)}")
    print(AUDIT_PATH)


if __name__ == "__main__":
    main()
