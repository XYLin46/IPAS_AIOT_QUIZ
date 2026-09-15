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
    (["智慧電表", "能源消耗", "能源需求"], "智慧能源監測", "智慧電表能持續量測並記錄用電資料，再把資料提供給能源管理或預測模型；一般電力感測器只負責量測，UPS 則著重備援供電。"),
    (["P2P", "點對點", "中央伺服器"], "點對點架構", "P2P 架構讓節點直接交換資料，不必把所有通訊都送經中央伺服器；集中式與客戶端—伺服器架構則依賴中央服務。"),
    (["低占空比", "Low Duty Cycle", "睡眠模式", "電池壽命", "低電壓元件"], "低功耗設計", "低功耗裝置會讓處理器與無線模組大部分時間休眠，只在排定時段喚醒收發資料；降低工作電壓、縮短通訊時間也能減少耗電。"),
    (["NoSQL", "PostgreSQL", "MongoDB", "JSON", "關聯式資料庫", "非關聯式資料庫"], "SQL 與 NoSQL", "PostgreSQL 是關聯式資料庫；MongoDB 是文件型 NoSQL 資料庫，能以類 JSON 文件保存彈性結構。NoSQL 也涵蓋鍵值、欄族與圖形等模型，通常強調水平擴充。"),
    (["RESTful", "REST API", "GET", "POST", "PUT", "DELETE", "HTTP 方法"], "RESTful API", "REST 常以 HTTP 方法操作資源：GET 讀取、POST 新增、PUT 更新或取代、DELETE 刪除。GET 參數常出現在網址與紀錄中，不適合直接承載機敏資料。"),
    (["WebSocket"], "WebSocket", "WebSocket 建立後可在同一連線上由伺服器與瀏覽器雙向即時傳送資料，避免反覆輪詢造成的額外負擔；加密與驗證仍須另外使用 WSS 等安全措施。"),
    (["I2C", "SDA", "SCL", "Inter-Integrated"], "I2C 匯流排", "I2C 是使用 SDA 資料線與 SCL 時脈線的同步匯流排，可用位址連接多個裝置；兩條線通常為開漏輸出，因此都需要上拉電阻接至 VCC。"),
    (["SPI", "MISO", "MOSI", "SCLK", "SS", "菊花鏈"], "SPI 介面", "SPI 以時脈同步傳輸，常用 SCLK、MOSI、MISO 與晶片選擇線，通常可全雙工且沒有內建確認交握；記憶卡與顯示器都是常見周邊。"),
    (["RS-232", "8/N/1", "同位位元", "起始位元", "停止位元"], "RS-232 非同步序列通訊", "RS-232 是點對點非同步序列通訊，雙方必須設定相同鮑率、資料位元、同位檢查與停止位元；8/N/1 表示 8 個資料位元、無同位檢查、1 個停止位元。"),
    (["邏輯分析儀", "Logic Analyzer", "三用電表", "歐姆檔", "示波器"], "電路與通訊量測", "三用電表的歐姆／導通檔適合檢查斷路或短路；邏輯分析儀可解碼 I2C、SPI 等數位時序；示波器則用來觀察電壓波形及訊號品質。"),
    (["Stop-and-Wait", "flow control", "流量控制", "緩衝"], "停止等待流量控制", "Stop-and-Wait 每送出一筆資料就等待對方確認後再傳下一筆，因此只需很小的緩衝空間；代價是長延遲鏈路的利用率較低。"),
    (["Interrupt", "Polling", "中斷", "輪詢"], "中斷與輪詢", "輪詢由處理器反覆查詢周邊狀態；中斷則由周邊在事件發生時提出要求，使處理器可先執行其他工作，再轉入中斷服務程序。"),
    (["Flash Memory", "快閃記憶體", "NAS", "Network Attached Storage"], "非揮發性與網路儲存", "快閃記憶體斷電後仍能保存資料，通常以區塊為單位抹除；NAS 將儲存服務獨立接入網路，讓多個使用者或伺服器共享資料。"),
    (["自由軟體", "Free Software", "Open Source", "開放源碼", "開源軟體", "公共領域軟體", "IIS Web Server"], "自由與開源軟體", "自由軟體著重使用、研究、修改與再散布的自由；開源軟體要求授權符合開源定義。公開原始碼不等於毫無授權條件，IIS 則不是自由或開源軟體。"),
    (["LED", "發光二極體", "七段顯示器", "三色LED"], "LED 電路", "LED 必須注意極性並以串聯電阻限制電流；降低電阻會增加電流與亮度，但仍不可超過額定值。含小數點的七段顯示器共有八個發光區段。"),
    (["電阻", "電感", "電容", "被動元件", "電晶體", "R、L、C"], "基本電子元件", "R、L、C 分別代表電阻、電感與電容，屬於被動元件；電晶體能放大或切換訊號，通常歸為主動元件。"),
    (["Software defined network", "SDN", "NFV", "NRF", "網路功能虛擬化"], "軟體定義與虛擬化網路", "SDN 將控制邏輯集中並與資料轉送分離，便於自動化配置；NFV 則以軟體實作網路功能。5G 核心網的 NRF 負責網路功能服務的登錄與探索。"),
    (["虛擬主機", "虛擬化", "Private Cloud", "Public Cloud", "Hybrid Cloud", "Community Cloud", "私有雲", "公有雲", "混合雲", "社群雲"], "虛擬化與雲端部署", "虛擬化可在較少實體硬體上隔離多個工作負載，降低設備與維運成本。混合雲結合私有環境的控制性與公有雲的彈性容量。"),
    (["5G", "4G", "URLLC", "毫米波", "mmWave", "3500MHz", "10 Gbps", "頻譜利用率"], "5G 行動通訊", "5G 以增強行動寬頻、大量機器型通訊及超可靠低延遲通訊支援不同情境；毫米波具較大頻寬但覆蓋較短，不能視為一般低功耗長距離技術。"),
    (["NFC", "Near Field Communication", "Peer-to-Peer Mode", "Eddystone"], "NFC 與近距互動", "NFC 支援讀寫器、卡片模擬及點對點模式；因通訊距離極短、交換資料量小，裝置端耗電通常低於 Wi-Fi、行動網路及持續連線的 Bluetooth，適合感應支付、門禁與近距資料交換。"),
    (["條碼", "二維條碼", "一維條碼", "QR Code"], "條碼辨識", "二維條碼可在較小面積容納較多資料並具一定錯誤修復能力；能否由掃描器讀取並非二維條碼相對一維條碼的獨有優點。"),
    (["虹膜", "眼球辨識", "指紋", "聲音", "身份識別", "身分確認"], "生物特徵辨識", "虹膜辨識比對眼睛虹膜紋理，指紋辨識比對脊線特徵；各種生物特徵需要相應感測器與活體、防偽機制，不能僅憑一般手機硬體推定皆可獨立使用。"),
    (["GPS", "全球定位", "AOA", "Angle of Arrival", "到達角", "SLAM", "同步定位"], "定位技術", "GPS 以多顆衛星訊號求得位置；AOA 由訊號到達角配合幾何定位；SLAM 則讓裝置在未知環境中同時建立地圖並估算自身位置。"),
    (["PPG", "ECG", "心率", "心跳", "光學感測式心率"], "生理訊號量測", "PPG 以光線觀察血容量隨心搏的變化，ECG 量測心臟電位。光學量測會受配戴鬆緊、膚色、刺青、環境光與動作影響。"),
    (["霍爾", "Hall", "法拉第", "磁電式", "磁通密度"], "磁場感測", "霍爾元件利用霍爾效應感測磁場，常用於電流、位置與轉速量測；磁電式感測器則可依電磁感應的法拉第定律產生電壓。"),
    (["開路", "短路", "過熱", "當機", "亂碼", "接頭鬆脫"], "基本故障判斷", "排除故障應先從供電、接線、溫度與通訊設定逐層檢查。斷線或接頭鬆脫通常造成無資料，鮑率或格式不一致才較容易形成可見亂碼。"),
    (["ambient backscatter", "背向散射", "零耗電傳輸"], "環境背向散射", "環境背向散射不自行產生射頻載波，而是調變環境中既有的無線電波並反射訊號，可大幅降低通訊端耗電；可擷取的能量來源仍須符合實際射頻能量轉換原理。"),
    (["UWB", "Ultra-Wideband", "超寬頻"], "UWB 超寬頻", "UWB 以極短脈衝跨越寬頻帶傳輸，時間解析度高，適合短距離精密測距與定位；其發射功率譜密度受到規範限制。"),
    (["HTTP", "連線自動斷線"], "HTTP 通訊", "HTTP 採請求—回應模式；傳統非持續連線會在完成回應後關閉連線，而持續連線可重複使用。需要伺服器主動即時推送時，通常使用 WebSocket 等機制。"),
    (["OAuth", "Certificate Pinning", "憑證綁定"], "應用程式授權與連線驗證", "OAuth 用權杖委派資源存取權限，而 Certificate Pinning 讓應用程式只信任指定憑證或公鑰，降低偽造憑證與中間人攻擊風險。"),
    (["光纖", "抗電干擾"], "有線傳輸介質", "光纖以光傳遞資料，不導電且不受一般電磁干擾，適合高頻寬或強電磁雜訊環境；雙絞線與同軸電纜仍以電訊號傳輸。"),
    (["LiDAR", "光達", "毫米波雷達", "攝影鏡頭"], "車載環境感知", "攝影鏡頭依賴可見光，容易受黑暗、雨霧與逆光影響；光達以雷射測距，毫米波雷達對惡劣天候通常較穩定，多感測器融合可互補限制。"),
    (["感測器網路", "無線感測網路"], "感測器網路", "感測器網路由多個節點量測環境並透過網路回傳資料，設計時通常優先考量低功耗、覆蓋、可靠性及節點數量。"),
    (["智慧家居", "冷凍車隊", "智慧製造", "智慧生產", "智慧農業", "車聯網"], "AIoT 場域應用", "AIoT 應用會依場域整合感測、連線、資料分析與控制；智慧家居著重住宅設備，冷凍車隊管理則屬物流與運輸場域，兩者不能混為同一應用領域。"),
    (["流體", "壓力", "液位", "流量"], "流體與壓力量測", "流量、壓力與液位是不同物理量，會使用壓差、渦輪、電磁、超音波或壓力元件等相應原理，應依被測介質與量測目的選擇。"),
    (["pH", "氫離子", "OH⁻", "Na⁺", "Cl⁻"], "酸鹼值感測", "pH 是氫離子活度的負對數；pH 感測電極量測與氫離子活度相關的電位差，因此主要對應氫離子，而不是氫氧根、鈉或氯離子。"),
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
    (["Node-RED", "流程編輯"], "低程式碼流程整合", "Node-RED 以節點與流程連接輸入、處理及輸出，適合快速整合感測資料、通訊協定與儀表板；部署時仍需管理憑證、權限、錯誤處理與資源使用。"),
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


def fallback_concept(question):
    category_fallbacks = {
        "U2-1": ("系統元件與架構", "判斷系統元件時，要把題目要求的輸入、處理、通訊、儲存或輸出功能，對應到元件實際負責的工作。"),
        "U2-2": ("故障判斷與排除", "故障排除應由電源、接線與環境開始，再檢查訊號、通訊參數與軟體紀錄，以量測結果逐步縮小問題範圍。"),
        "U2-3": ("物聯網資安與隱私", "資安判斷需分辨身分驗證、權限控制、加密、完整性與稽核的目的，並依最小權限及資料最小化原則降低風險。"),
        "U2-4": ("平台設計", "平台設計需依資料來源、傳輸方式、儲存模型、即時性與擴充需求選擇元件，並清楚區分各元件的責任。"),
    }
    chapter_fallbacks = {
        "3-1": ("AI 基礎概念", "判斷 AI 技術時，需分辨資料、模型訓練、推論及評估各階段，以及監督式、非監督式與強化學習的不同。"),
        "3-2": ("AIoT 應用", "AIoT 應用把感測資料、網路傳輸與分析決策串成流程，重點是資料如何轉化為預測、控制或服務。"),
        "4-1": ("物聯網架構", "物聯網系統通常由感知、通訊、平台處理與應用服務組成，應依題目描述的功能辨認其所在層級。"),
        "4-2": ("網路與通訊", "選擇通訊技術時需比較距離、資料率、功耗、拓樸、可靠性與頻段，不能只看單一特性。"),
        "4-3": ("識別與工業通訊", "識別與工業通訊技術各有特定頻段、資料模型和控制角色，應依標準所定義的功能判斷。"),
        "4-4": ("中介軟體與平台", "平台透過訊息交換、儲存、API 與裝置管理整合資料；選型時要依元件職責與服務模型判斷。"),
        "4-5": ("資安與隱私", "資安機制分別處理機密性、完整性、可用性、身分與權限，應依威脅與保護目標選擇。"),
        "5-1": ("感測技術", "感測器將特定物理或化學量轉為可處理訊號，選用時需核對量測原理、範圍、精度與環境限制。"),
        "5-2": ("感測訊號", "感測訊號需經適當放大、濾波、取樣或介面傳輸；解析度、雜訊與時序都會影響結果。"),
    }
    return category_fallbacks.get(question.get("categoryId"), chapter_fallbacks.get(question.get("chapterId"), ("AIoT 基礎判斷", "應依題目要求的功能、條件與限制，對照技術的實際定義後判斷。")))


def choose_concept(question):
    stem = normalize(question["question"])
    correct_text = normalize(" ".join(option["text"] for option in question["options"] if option.get("isCorrect")))
    ranked = []
    for index, (keywords, title, insight) in enumerate(CONCEPTS):
        matches = [keyword for keyword in keywords if normalize(keyword) in stem or normalize(keyword) in correct_text]
        score = sum(
            len(normalize(keyword))
            * (
                6
                if normalize(keyword) in correct_text
                else 4
            )
            for keyword in matches
        )
        ranked.append((score, len(matches), -index, title, insight))
    score, _, _, title, insight = max(ranked)
    if score == 0:
        return fallback_concept(question)
    return title, insight


def add_explanation(question):
    concept_title, insight = choose_concept(question)
    correct_options = [option for option in question["options"] if option.get("isCorrect")]
    correct_texts = "、".join(option["text"] for option in correct_options)
    asks_negative = any(marker in question["question"] for marker in NEGATIVE_MARKERS)
    if not correct_texts:
        question["explanation"] = "原始題庫缺少正確選項文字，暫時無法提供可靠詳解。"
    elif asks_negative:
        question["explanation"] = (
            f"答案是「{correct_texts}」。{insight}"
            f"題目要求找出錯誤或不適用的敘述；「{correct_texts}」與上述原理不符，因此是本題答案。"
        )
    else:
        question["explanation"] = f"答案是「{correct_texts}」。{insight}"
    question.pop("optionExplanations", None)


def enrich_question(question, chapter_by_id):
    # Preserve reviewed classifications when regenerating explanations after
    # mechanical text cleanup. Only classify questions that do not yet have a
    # valid chapter id.
    chapter_id = question.get("chapterId")
    if chapter_id not in chapter_by_id:
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
