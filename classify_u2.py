import argparse
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
QUESTION_DIR = ROOT / "questions_json"

CATEGORIES = [
    {
        "id": "U2-1",
        "name": "系統元件與架構",
        "description": "感測器、控制器、通訊模組、閘道器、電源、網路拓撲、系統分層與軟硬體整合",
    },
    {
        "id": "U2-2",
        "name": "簡易系統故障問題判斷與排除",
        "description": "連線、供電、感測、通訊與系統異常的觀察、診斷、測試、維護及排除",
    },
    {
        "id": "U2-3",
        "name": "物聯網資安與隱私權問題",
        "description": "身分與存取控制、加密、攻擊防護、弱點管理、個人資料與隱私保護",
    },
    {
        "id": "U2-4",
        "name": "平台設計",
        "description": "雲端與應用平台、資料庫、API、訊息服務、資料處理、視覺化、部署與擴充性",
    },
]


KEYWORDS = {
    "U2-1": {
        5: [
            "感測器", "致動器", "控制器", "微控制器", "單晶片", "mcu", "處理器",
            "嵌入式", "閘道器", "gateway", "樹莓派", "raspberry pi", "arduino",
            "系統架構", "系統元件", "硬體架構", "網路拓撲", "電路", "gpio",
        ],
        3: [
            "rfid", "nfc", "藍牙", "bluetooth", "zigbee", "lora", "nb-iot",
            "wi-fi", "wifi", "5g", "4g", "乙太網路", "ethernet", "tcp", "udp",
            "ipv4", "ipv6", "mqtt", "coap", "modbus", "opc ua", "通訊協定",
            "感知層", "網路層", "應用層", "邊緣運算", "霧運算", "電源管理",
            "智慧電表", "攝影機", "馬達", "繼電器", "天線", "電池", "記憶體",
            "作業系統", "韌體", "串列", "uart", "i2c", "spi", "adc", "pwm",
            "rs-232", "rs232", "rs-485", "rs485", "調變", "led", "電阻", "電容",
        ],
        1: ["裝置", "設備", "節點", "網路", "訊號", "資料傳輸", "物聯網架構"],
    },
    "U2-2": {
        7: [
            "故障排除", "問題排除", "故障診斷", "問題判斷", "根因分析", "除錯",
            "無法連線", "連線失敗", "無法啟動", "啟動失敗", "無法運作", "沒有回應",
        ],
        5: [
            "故障", "異常", "斷線", "不穩定", "封包遺失", "資料遺失", "訊號不良",
            "延遲過高", "耗電異常", "過熱", "校正", "維修", "維護", "診斷",
            "測試工具", "三用電表", "示波器", "ping", "traceroute", "錯誤訊息",
            "亂碼", "讀取錯誤", "數據不正確", "資料不正確", "誤報率", "燒毀",
        ],
        3: [
            "日誌", "log", "監控", "告警", "備援", "容錯", "復原", "重新啟動",
            "重啟", "韌體更新", "版本更新", "電池壽命", "效能問題", "訊號強度",
            "連線問題", "網路問題", "電源問題", "檢查步驟", "測試", "排查",
        ],
    },
    "U2-3": {
        7: [
            "資訊安全", "網路安全", "物聯網資安", "隱私權", "個人資料", "個資",
            "機密性", "完整性", "可用性", "身分驗證", "存取控制", "權限管理",
            "數位簽章", "多因素驗證", "雙因素驗證", "零信任", "社交工程",
        ],
        5: [
            "資安", "隱私", "加密", "解密", "密碼學", "雜湊", "hash", "憑證",
            "pki", "tls", "ssl", "vpn", "防火牆", "入侵", "惡意程式", "勒索軟體",
            "木馬", "病毒", "釣魚", "弱點", "漏洞", "攻擊", "駭客", "資料外洩",
            "拒絕服務", "ddos", "中間人攻擊", "sql injection", "xss", "金鑰",
        ],
        3: [
            "認證", "存取授權", "帳號", "密碼", "稽核", "風險評估", "安全更新",
            "安全性", "匿名化", "去識別化", "資料最小化", "備份", "iso 27001",
        ],
    },
    "U2-4": {
        6: [
            "平台設計", "雲端平台", "物聯網平台", "資料平台", "應用平台", "中介軟體",
            "資料庫", "資料倉儲", "資料湖", "訊息代理", "node-red", "kubernetes",
        ],
        4: [
            "雲端", "cloud", "iaas", "paas", "saas", "sql", "nosql", "mysql",
            "postgresql", "mongodb", "redis", "api", "restful", "web service", "微服務",
            "容器", "docker", "broker", "dashboard", "儀表板", "資料視覺化",
            "大數據", "hadoop", "spark", "資料分析", "資料探勘", "機器學習",
            "人工智慧", "數位分身", "規則引擎", "負載平衡", "可擴展性", "擴充性",
            "開源軟體", "開放源碼", "開放原始碼", "自由軟體", "著作權", "授權條款",
            "copyleft", "gpl", "apache license", "websocket", "ajax",
        ],
        2: [
            "伺服器", "server", "前端", "後端", "app", "應用程式", "網頁", "服務",
            "資料儲存", "資料處理", "資料格式", "json", "xml", "發布訂閱", "佈署", "部署",
        ],
    },
}

TROUBLE_MARKERS = (
    "故障", "排除", "診斷", "除錯", "無法", "失敗", "異常", "斷線", "不穩定",
    "遺失", "過高", "過熱", "校正", "維修", "維護", "錯誤訊息", "排查",
    "亂碼", "讀取錯誤", "數據不正確", "資料不正確", "誤報率", "燒毀",
)

SECURITY_MARKERS = (
    "資安", "安全", "隱私", "個資", "加密", "解密", "密碼", "憑證", "金鑰",
    "攻擊", "弱點", "漏洞", "入侵", "惡意", "防火牆", "驗證", "存取控制",
)

# Every existing paper was reviewed at the transitions between the four course
# sections. Values are the inclusive end question for U2-1, U2-2 and U2-3.
# The semantic segment finder below remains as a fallback for future papers.
REVIEWED_BOUNDARIES = {
    "108-2-U2": (10, 21, 25),
    "109-1-U2": (12, 22, 27),
    "109-2-U2": (15, 22, 27),
    "110-1-U2": (12, 22, 27),
    "110-2-U2": (12, 23, 27),
    "111-1-U2": (17, 27, 32),
    "111-2-U2": (19, 27, 32),
    "112-1-U2": (10, 20, 25),
    "112-2-U2": (10, 20, 25),
    "113-1-U2": (11, 20, 25),
    "113-2-U2": (10, 20, 25),
    "114-1-U2": (10, 20, 25),
}


def normalize(value):
    return re.sub(r"\s+", "", str(value or "")).lower()


def content_scores(question):
    stem = normalize(question.get("question"))
    correct = normalize(" ".join(
        option.get("text", "") for option in question.get("options", []) if option.get("isCorrect")
    ))
    all_options = normalize(" ".join(option.get("text", "") for option in question.get("options", [])))
    scores = Counter()

    for category_id, weighted_groups in KEYWORDS.items():
        for weight, keywords in weighted_groups.items():
            for keyword in keywords:
                token = normalize(keyword)
                if not token:
                    continue
                if token in stem:
                    scores[category_id] += weight * 5
                elif token in correct:
                    scores[category_id] += weight * 3
                elif token in all_options:
                    scores[category_id] += weight

    # A troubleshooting classification needs a symptom, diagnostic action or failure context;
    # a generic word such as「測試」alone must not pull conceptual questions into this category.
    has_trouble_context = any(normalize(marker) in stem for marker in TROUBLE_MARKERS)
    if has_trouble_context:
        scores["U2-2"] += 30

    # Security and privacy remain in their own course category even when the scenario also
    # describes a system failure or a platform feature.
    has_security_context = any(normalize(marker) in stem for marker in SECURITY_MARKERS)
    if has_security_context:
        scores["U2-3"] += 30

    # With no distinguishing evidence, course-level component/architecture is the safest
    # category for general IoT devices, applications and integration questions.
    return {category["id"]: scores[category["id"]] for category in CATEGORIES}


def choose_segments(questions, source):
    """Find four ordered course sections while allowing year-specific boundaries."""
    ordered = sorted(questions, key=lambda question: int(question["id"]))
    if [int(question["id"]) for question in ordered] != list(range(1, len(ordered) + 1)):
        raise ValueError("U2 question IDs must be contiguous and start at 1")

    evidence = [content_scores(question) for question in ordered]
    prefix = {category["id"]: [0] for category in CATEGORIES}
    for scores in evidence:
        for category in CATEGORIES:
            category_id = category["id"]
            prefix[category_id].append(prefix[category_id][-1] + scores[category_id])

    def segment_score(category_id, start, end):
        return prefix[category_id][end] - prefix[category_id][start]

    candidates = []
    total_questions = len(ordered)
    for first_end in range(5, min(20, total_questions - 16) + 1):
        for second_end in range(first_end + 5, min(first_end + 18, total_questions - 11) + 1):
            for third_end in range(second_end + 3, min(second_end + 10, total_questions - 8) + 1):
                score = (
                    segment_score("U2-1", 0, first_end)
                    + segment_score("U2-2", first_end, second_end)
                    + segment_score("U2-3", second_end, third_end)
                    + segment_score("U2-4", third_end, total_questions)
                )
                # Historical papers tend toward 10/10/5/25, but the penalty is
                # intentionally small so clear topic evidence can move boundaries.
                lengths = (
                    first_end,
                    second_end - first_end,
                    third_end - second_end,
                    total_questions - third_end,
                )
                expected = (10, 10, 5, 25)
                score -= sum(abs(actual - target) for actual, target in zip(lengths, expected)) * 0.5
                candidates.append((score, first_end, second_end, third_end))

    candidates.sort(reverse=True)
    _, detected_first, detected_second, detected_third = candidates[0]
    first_end, second_end, third_end = REVIEWED_BOUNDARIES.get(
        source,
        (detected_first, detected_second, detected_third),
    )
    assignment = {}
    for index, question in enumerate(ordered, start=1):
        if index <= first_end:
            category_id = "U2-1"
        elif index <= second_end:
            category_id = "U2-2"
        elif index <= third_end:
            category_id = "U2-3"
        else:
            category_id = "U2-4"
        assignment[int(question["id"])] = category_id

    confidence_margin = candidates[0][0] - candidates[1][0]
    return assignment, (first_end, second_end, third_end), confidence_margin, evidence


def classify(apply_changes=False):
    category_by_id = {category["id"]: category for category in CATEGORIES}
    counts = Counter()
    audits = []
    total = 0

    for path in sorted(QUESTION_DIR.glob("*-U2.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        assignment, boundaries, confidence_margin, evidence = choose_segments(
            data.get("questions", []),
            path.stem,
        )
        audits.append((path.stem, boundaries, confidence_margin))
        for question in data.get("questions", []):
            category_id = assignment[int(question["id"])]
            category = category_by_id[category_id]
            counts[category_id] += 1
            total += 1
            if apply_changes:
                question["categoryId"] = category_id
                question["categoryName"] = category["name"]

        if apply_changes:
            data["subject"] = "U2"
            data["categorySchemaVersion"] = 1
            # Existing question banks use CRLF; preserve it to keep classification
            # diffs limited to the added category metadata.
            with path.open("w", encoding="utf-8", newline="\r\n") as output:
                output.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    catalog = {
        "source": "https://collegeplus.itri.org.tw/course/1146#/",
        "sourceTitle": "物聯網系統與應用－工研院產業學院雲端教室",
        "subject": "U2",
        "categories": [
            {**category, "questionCount": counts[category["id"]]}
            for category in CATEGORIES
        ],
    }
    if apply_changes:
        with (QUESTION_DIR / "u2-categories.json").open(
            "w",
            encoding="utf-8",
            newline="\r\n",
        ) as output:
            output.write(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")

    print(f"questions={total} apply={apply_changes}")
    print("counts=" + json.dumps(dict(counts), ensure_ascii=False, sort_keys=True))
    for source, boundaries, confidence_margin in audits:
        first_end, second_end, third_end = boundaries
        print(
            f"{source}: U2-1=1-{first_end}, U2-2={first_end + 1}-{second_end}, "
            f"U2-3={second_end + 1}-{third_end}, U2-4={third_end + 1}-50, "
            f"boundary_margin={confidence_margin:.1f}"
        )


def main():
    parser = argparse.ArgumentParser(description="Classify U2 questions using the four ITRI course categories.")
    parser.add_argument("--apply", action="store_true", help="Write category fields and the U2 catalog.")
    args = parser.parse_args()
    classify(apply_changes=args.apply)


if __name__ == "__main__":
    main()
