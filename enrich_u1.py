import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
QUESTION_DIR = ROOT / "questions_json"

CHAPTERS = [
    ("3-1", "AI 基礎概念", "人工智慧、機器學習、深度學習、資料處理、模型訓練與評估"),
    ("3-2", "AIoT 應用案例", "AI 與物聯網結合後的智慧製造、醫療、城市、交通、農業與生活應用"),
    ("4-1", "物聯網架構與功能", "AIoT／IoT 定義、感知層、網路層、應用層、邊緣與雲端架構"),
    ("4-2", "常見通訊協定與網路層技術", "TCP/IP、IPv4/IPv6、Wi-Fi、Bluetooth、ZigBee、LoRa、NB-IoT、MQTT 與 CoAP"),
    ("4-3", "工業通訊標準與資訊模型", "RFID、EPCglobal、OPC UA、Modbus、工業乙太網路與資訊模型"),
    ("4-4", "中介軟體與平台", "雲端服務、訊息代理、資料庫、API、中介軟體、裝置管理與平台服務"),
    ("4-5", "資安與隱私基本概念", "身分驗證、授權、加密、金鑰、攻擊防護、隱私與風險管理"),
    ("5-1", "感測技術基礎", "感測器原理、量測特性、各類物理量感測與感測器選用"),
    ("5-2", "感測訊號與通訊基礎", "類比／數位訊號、取樣、轉換、濾波、放大、雜訊與感測訊號傳輸"),
]

CHAPTER_KEYWORDS = {
    "3-1": ["人工智慧", "機器學習", "深度學習", "神經網路", "監督式", "非監督式", "強化學習", "訓練資料", "模型", "分類", "迴歸", "分群", "特徵", "混淆矩陣", "精確率", "召回率", "過度擬合", "生成式", "資料前處理"],
    "3-2": ["AIoT", "智慧製造", "智慧醫療", "智慧城市", "智慧交通", "智慧農業", "預測性維護", "瑕疵檢測", "人臉辨識", "影像辨識", "語音辨識", "無人車", "智慧家庭", "智慧電網", "遠端醫療", "行動支付"],
    "4-1": ["物聯網", "感知層", "網路層", "應用層", "三層架構", "四層架構", "五層架構", "邊緣運算", "霧運算", "閘道器", "gateway", "edge", "雲端運算", "M2M", "物與物"],
    "4-2": ["TCP", "UDP", "IPv4", "IPv6", "IP 位址", "IP位址", "Wi-Fi", "WIFI", "802.11", "Bluetooth", "藍牙", "ZigBee", "Zigbee", "LoRa", "NB-IoT", "5G", "4G", "MQTT", "CoAP", "HTTP", "REST", "QoS", "OSI", "封包", "分封", "電路交換", "頻段", "ISM", "通訊協定", "路由", "Beacon", "NFC"],
    "4-3": ["RFID", "EPC", "EPCglobal", "EPCIS", "LLRP", "標籤", "讀取器", "詢答器", "條碼", "ISO 18000", "OPC", "Modbus", "PROFINET", "EtherCAT", "CAN", "工業乙太網", "資訊模型", "SCADA", "PLC"],
    "4-4": ["雲平台", "雲端平台", "雲端服務", "SaaS", "PaaS", "IaaS", "中介軟體", "消息隊列", "訊息交換", "broker", "資料庫", "Redis", "PostgreSQL", "HiveMQ", "ActiveMQ", "API", "RESTful", "裝置管理", "數據傳遞", "大數據", "巨量資料", "資料探勘"],
    "4-5": ["資安", "安全", "隱私", "加密", "解密", "TLS", "SSL", "PKI", "憑證", "金鑰", "密碼", "雜湊", "hash", "認證", "驗證", "授權", "Authentication", "Authorization", "Audit", "AAA", "攻擊", "惡意", "防火牆", "弱點", "漏洞", "個資", "存取權限", "CIA"],
    "5-1": ["感測器", "感測元件", "感測技術", "溫度", "濕度", "壓力", "光敏", "紅外線", "PIR", "超音波", "加速度", "陀螺儀", "氣體感測", "光感測", "雷射感測", "微波感測", "霍爾", "應變規", "熱電偶", "電阻式", "電容式", "感測"],
    "5-2": ["類比", "數位", "ADC", "DAC", "取樣", "量化", "濾波", "放大器", "雜訊", "訊號", "信號", "電壓", "電流", "電阻信號", "解析度", "鮑率", "串列", "UART", "I2C", "SPI", "PWM", "頻率", "波長", "電磁波", "輻射", "背向散射"],
}

CONCEPTS = [
    (["人工智慧", "機器學習", "深度學習", "神經網路", "大規模語言模型", "知識圖譜", "自然語言"], "AI 與機器學習", "人工智慧是讓系統具備感知、學習、推論或決策能力的廣義領域；機器學習由資料找出規律，深度學習以多層神經網路學習複雜表示，語言模型與知識圖譜則可支援自然語言理解及語義連結。"),
    (["監督式", "非監督式", "強化學習", "分類", "迴歸", "分群"], "機器學習任務", "分類與迴歸通常使用帶標籤資料進行監督式學習；分群常屬非監督式學習；強化學習則透過行動後的獎勵訊號改善策略。"),
    (["邊緣運算", "霧運算", "Edge", "edge"], "邊緣運算", "邊緣運算把部分處理放在資料來源附近，可降低延遲、節省回傳頻寬並在斷線時維持局部服務；雲端仍適合跨場域整合與大規模運算。"),
    (["感知層", "網路層", "應用層"], "物聯網分層架構", "感知層負責量測與辨識，網路層負責連接、傳輸與路由，應用層把資料轉換成可用服務。判斷題目時應先辨認動作發生在哪一層。"),
    (["物聯網", "M2M", "物與物"], "物聯網核心概念", "物聯網以可辨識、可感測或可控制的物件為端點，透過網路交換資料，再由平台或應用產生監控、分析與控制價值。"),
    (["MQTT", "QoS", "broker", "消息隊列"], "MQTT 發布／訂閱", "MQTT 由發布者把訊息送到代理伺服器，再依主題分送給訂閱者。QoS 0、1、2 分別代表至多一次、至少一次與恰好一次的傳遞語意，但端到端可靠性仍受網路與應用設計影響。"),
    (["CoAP"], "CoAP", "CoAP 是為資源受限裝置設計的輕量應用層協定，常運行於 UDP，採類 REST 的資源與方法模型，並可用確認訊息提升可靠性。"),
    (["TCP", "UDP", "分封", "電路交換", "封包"], "傳輸與交換方式", "TCP 提供連線導向、排序、重傳與流量控制；UDP 額外負擔較小但不保證送達與順序。分封交換共享鏈路資源，可能產生延遲、壅塞或亂序。"),
    (["IPv4", "IPv6", "IP 位址", "IP位址"], "IP 定址", "IPv4 使用 32 位元位址；IPv6 使用 128 位元以擴充位址空間。私有 IPv4 範圍不會直接在公網路由，通常需經 NAT 對外連線。"),
    (["Wi-Fi", "WIFI", "802.11"], "Wi-Fi", "Wi-Fi 遵循 IEEE 802.11 系列標準，常使用 2.4、5 或 6 GHz 頻段，提供較高資料率，但功耗與覆蓋特性須依場域評估。"),
    (["Bluetooth", "藍牙", "Beacon"], "Bluetooth／BLE", "Bluetooth 適合個人區域短距連線；BLE 以低功耗廣播與連線機制支援感測器及 Beacon，Beacon 多以週期性廣播協助近距辨識或定位。"),
    (["ZigBee", "Zigbee"], "ZigBee", "ZigBee 建立在 IEEE 802.15.4 之上，主打低功耗、低資料率與可組成星狀或網狀網路，常見於大量感測節點。"),
    (["LoRa", "NB-IoT", "LPWAN"], "低功耗廣域網路", "LPWAN 技術以低資料率換取長距離、低功耗與大量節點連線；LoRa/LoRaWAN 使用免執照頻段，NB-IoT 則使用電信業者的授權頻譜。"),
    (["RFID", "標籤", "讀取器", "詢答器", "EPC"], "RFID 與 EPC", "RFID 由標籤與讀取器以無線射頻交換識別資料。被動標籤由讀取器供能，成本較低；UHF 常用於物流遠距、多標籤盤點，HF/NFC 常用於近距卡片應用。"),
    (["EPCIS", "EPCglobal", "LLRP", "Bizstep"], "EPCglobal 資訊交換", "EPCglobal 架構把識別、擷取與事件交換分層；LLRP 管理讀取器盤查與存取，EPCIS 事件則以 What、When、Where、Why 描述供應鏈物件事件。"),
    (["OPC", "Modbus", "PROFINET", "EtherCAT", "PLC", "SCADA"], "工業通訊", "工業通訊除資料交換外，也重視確定性、互通性、設備模型與可維護性。選擇標準時需分辨現場匯流排、工業乙太網路與上層資訊整合的角色。"),
    (["SaaS", "PaaS", "IaaS", "雲端服務", "雲平台", "雲端平台"], "雲端服務模型", "IaaS 提供運算、儲存與網路資源，PaaS 提供應用執行與開發平台，SaaS 則直接交付可使用的軟體服務；責任邊界與管理範圍依模型而異。"),
    (["資料庫", "Redis", "PostgreSQL", "ActiveMQ", "HiveMQ", "中介軟體"], "平台與中介軟體", "物聯網平台常以訊息代理解耦裝置與應用，以資料庫保存狀態或歷史資料，再透過 API、規則引擎與裝置管理功能提供服務。"),
    (["TLS", "SSL", "PKI", "憑證", "加密", "金鑰"], "傳輸加密與信任", "TLS 保護傳輸中的機密性與完整性，憑證與 PKI 協助驗證身分及建立信任。加密、雜湊與數位簽章的目的不同，不應互相混用。"),
    (["Authentication", "Authorization", "Audit", "AAA", "認證", "授權", "驗證"], "身分與存取管理", "Authentication 確認使用者或裝置是誰，Authorization 決定可做什麼，Accounting/Auditing 記錄行為以供追蹤；三者共同降低未授權存取風險。"),
    (["隱私", "個資", "資安", "攻擊", "弱點", "漏洞", "防火牆"], "AIoT 資安與隱私", "AIoT 應採最小權限、分層防護、更新修補、加密通訊與日誌稽核；涉及個人資料時還需落實目的限制、資料最小化及保存期限管理。"),
    (["加速度", "陀螺儀", "慣性"], "慣性感測", "加速度計量測線性加速度，也會感受到重力方向；陀螺儀量測角速度。兩者常搭配融合，以估測姿態與動作。"),
    (["PIR", "紅外線"], "紅外線與 PIR 感測", "PIR 利用熱釋電材料偵測視野內紅外線能量的變化，適合人體移動偵測；它不是主動量距裝置，也不直接量測空氣品質。"),
    (["光敏", "光感測", "照度"], "光感測", "光敏元件會把入射光轉為電阻、電流或電壓變化，可用於照度控制、物件遮斷與光學偵測；應用能力取決於光譜、靈敏度與電路設計。"),
    (["溫度", "熱電偶", "熱敏"], "溫度感測", "不同溫度感測器利用電阻、半導體接面或熱電效應把溫度轉成電訊號；選用時需比較量測範圍、精度、反應時間與校正需求。"),
    (["濕度", "氣體", "PM2.5", "一氧化碳", "二氧化碳", "臭氧"], "環境感測", "環境感測器需針對目標物理量或氣體選擇感測原理，並考慮交叉敏感、暖機、漂移與校正；不同污染物不能只靠同一種感測原理等同量測。"),
    (["超音波", "雷射感測", "微波", "杜卜勒"], "距離與移動感測", "超音波常以飛行時間量距，雷射／光達以光的飛行時間或掃描建立距離資訊，微波移動感測可利用杜卜勒效應；三者適用距離與環境限制不同。"),
    (["類比", "數位", "ADC", "取樣", "量化"], "類比數位轉換", "ADC 先依取樣率擷取連續訊號，再以有限位元量化成數值。取樣率影響可表示頻寬，位元數影響量化解析度，前端仍需適當的訊號調節。"),
    (["濾波", "放大器", "雜訊", "訊號", "信號"], "訊號調節", "感測訊號進入 ADC 前常需放大、偏壓、隔離與濾波。濾波用來抑制非目標頻帶或混疊，放大則要避免同時放大雜訊或造成飽和。"),
    (["頻率", "波長", "電磁波", "輻射"], "電磁波基本關係", "在同一介質中波速約等於頻率乘波長，因此頻率越高、波長越短；單一光子的能量與頻率成正比。游離與非游離輻射需依能量與暴露規範分辨。"),
    (["智慧城市", "智慧交通", "智慧醫療", "智慧家庭", "智慧電網", "智慧農業"], "AIoT 應用判斷", "AIoT 應用必須包含場域資料的感知或取得、通訊傳輸，以及後端分析或控制。判斷選項時可檢查是否真正形成資料閉環，而不只是一般資訊化。"),
    (["Raspberry Pi", "樹莓派", "Arduino", "微控制器", "Micro Controller", "MCU", "單晶片", "嵌入式"], "嵌入式控制平台", "微控制器負責讀取輸入、執行控制程式並驅動輸出；Arduino 是以微控制器為核心的開源原型平台，Raspberry Pi 則是可執行作業系統的單板電腦，兩者的運算能力、介面與即時性不同。"),
    (["setup()", "loop()", "sketch", "C/C++", "程式"], "嵌入式程式流程", "Arduino sketch 以 setup() 執行一次初始化，再由 loop() 持續循環執行主要邏輯。程式需配合腳位模式、資料型別、時序與周邊介面設定。"),
    (["RS232", "serial port", "序列埠", "UART", "USB", "鮑率"], "序列通訊", "UART／RS-232 以序列方式傳送資料，通訊雙方需協調鮑率、資料位元、同位元與停止位元；USB 是另一套主從式匯流排，USB 接頭不代表設備內部一定直接使用 RS-232。"),
    (["WoT", "Web of Things", "Thing Description"], "Web of Things", "WoT 以 Web 技術與 Thing Description 描述裝置的屬性、動作和事件，目的在於提高異質物聯網設備的可發現性與互通性，而不是取代底層感測器或所有通訊協定。"),
    (["Docker", "Kubernetes", "容器", "映像檔", "image", "container"], "容器與部署", "容器以映像檔封裝應用與相依環境，由容器執行引擎建立隔離程序；Kubernetes 等編排平台再處理部署、擴縮、服務發現與故障恢復。"),
    (["公開資料", "open data", "資料品質", "數據不正確", "缺失資料"], "資料品質", "資料來源可能因感測誤差、更新延遲、缺值、格式轉換或來源本身錯誤而失真。應以時間戳、範圍檢查、交叉驗證與異常偵測確認資料品質。"),
    (["GPIO", "PWM", "腳位", "I/O", "輸入輸出"], "數位輸入輸出", "GPIO 可設定為數位輸入或輸出；PWM 以脈衝占空比近似控制平均功率。連接感測器與致動器時要確認電壓準位、電流限制與腳位功能。"),
    (["Node-RED", "流程編輯", "節點"], "低程式碼流程整合", "Node-RED 以節點與流程連接輸入、處理及輸出，適合快速整合感測資料、通訊協定與儀表板；部署時仍需管理憑證、權限、錯誤處理與資源使用。"),
    (["SQL", "NoSQL", "關聯式資料庫", "鍵值", "文件資料庫"], "資料儲存模型", "關聯式資料庫以表格、鍵與交易一致性組織資料；NoSQL 可採鍵值、文件、欄族或圖形模型，選擇時應依查詢模式、資料結構、擴充性與一致性需求評估。"),
    (["微服務", "cloud native", "雲端原生", "可觀察性", "Observability"], "雲端原生架構", "雲端原生常結合容器、微服務、自動化部署與可觀察性，使服務可獨立擴縮與更新；可觀察性透過日誌、指標與追蹤掌握系統狀態。"),
]

NEGATIVE_MARKERS = ("不正確", "錯誤", "不是", "不屬於", "不包括", "較不", "不符合")


def normalize(text):
    return re.sub(r"\s+", "", str(text or "")).lower()


def choose_chapter(question):
    stem = normalize(question["question"])
    text = normalize(question["question"] + " " + " ".join(option["text"] for option in question["options"]))
    scores = {}
    for chapter_id, keywords in CHAPTER_KEYWORDS.items():
        scores[chapter_id] = sum(
            (4 if normalize(keyword) in stem else 1) + min(len(normalize(keyword)) / 8, 1)
            for keyword in keywords
            if normalize(keyword) in text
        )

    if any(normalize(keyword) in text for keyword in ["人工智慧", "機器學習", "深度學習", "神經網路", "監督式", "非監督式", "強化學習", "大規模語言模型", "知識圖譜"]):
        scores["3-1"] += 10
    if any(normalize(keyword) in stem for keyword in ["智慧製造", "智慧醫療", "智慧城市", "智慧交通", "智慧農業", "預測性維護", "瑕疵檢測", "aiot應用"]):
        scores["3-2"] += 12

    # Specific technologies should outrank broad words such as「物聯網」or「感測」。
    priority = {chapter_id: index for index, (chapter_id, _, _) in enumerate(CHAPTERS)}
    best_id = max(scores, key=lambda chapter_id: (scores[chapter_id], priority[chapter_id]))
    if scores[best_id] == 0:
        best_id = "4-1"
    return best_id


def choose_concept(question):
    stem = normalize(question["question"])
    correct_text = normalize(" ".join(option["text"] for option in question["options"] if option.get("isCorrect")))
    text = normalize(question["question"] + " " + " ".join(option["text"] for option in question["options"]))
    ranked = []
    for keywords, title, insight in CONCEPTS:
        matches = [keyword for keyword in keywords if normalize(keyword) in text]
        score = sum(
            len(normalize(keyword))
            * (
                8
                if normalize(keyword) in correct_text
                else 4
                if normalize(keyword) in stem
                else 1
            )
            for keyword in matches
        )
        ranked.append((score, len(matches), title, insight))
    score, _, title, insight = max(ranked)
    if score == 0:
        return "AIoT 系統判斷", "判斷 AIoT 題目時，應先確認題幹要求，再從技術的功能、適用條件、所屬層級與限制逐一排除不相符選項。"
    return title, insight


def add_explanation(question):
    concept_title, insight = choose_concept(question)
    correct_options = [option for option in question["options"] if option.get("isCorrect")]
    correct_texts = "、".join(option["text"] for option in correct_options)
    asks_negative = any(marker in question["question"] for marker in NEGATIVE_MARKERS)
    stem_tip = (
        "題幹含否定語意，作答時要找出不符合該概念的選項；其餘敘述可能本身正確，但不是本題要選的答案。"
        if asks_negative
        else "作答時要把每個選項與該概念的定義、功能與適用條件逐一核對，不能只憑關鍵字相似就選擇。"
    )
    question["explanation"] = (
        f"依題庫答案，正確答案內容為「{correct_texts}」。本題考查「{concept_title}」。{insight}"
        f"{stem_tip}因此，應以正確選項所描述的條件或功能作為判斷基準。"
    )
    question.pop("optionExplanations", None)


def enrich_question(question, chapter_by_id):
    chapter_id = choose_chapter(question)
    question["chapterId"] = chapter_id
    question["chapterName"] = chapter_by_id[chapter_id][0]
    add_explanation(question)


def main():
    chapter_by_id = {chapter_id: (name, description) for chapter_id, name, description in CHAPTERS}
    changed = 0
    explained_u2_files = 0
    total = 0
    counts = {chapter_id: 0 for chapter_id, _, _ in CHAPTERS}

    for path in sorted(QUESTION_DIR.glob("*-U1.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for question in data.get("questions", []):
            enrich_question(question, chapter_by_id)
            counts[question["chapterId"]] += 1
            total += 1
        data["subject"] = "U1"
        data["chapterSchemaVersion"] = 1
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        changed += 1

    # U2 receives review explanations only. Its own category fields are managed
    # by classify_u2.py and must be preserved when this script is rerun.
    for path in sorted(QUESTION_DIR.glob("*-U2.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for question in data.get("questions", []):
            add_explanation(question)
        data["subject"] = "U2"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        explained_u2_files += 1

    catalog = {
        "source": "AIoT應用工程師(初級)-學習指引-科目1_AIoT基礎概論.pdf",
        "subject": "U1",
        "chapters": [
            {"id": chapter_id, "name": name, "description": description, "questionCount": counts[chapter_id]}
            for chapter_id, name, description in CHAPTERS
        ],
    }
    (QUESTION_DIR / "u1-chapters.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"enriched_u1_files={changed} u1_questions={total} explained_u2_files={explained_u2_files}")
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
