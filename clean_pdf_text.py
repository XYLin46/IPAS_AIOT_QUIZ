import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
QUESTION_DIR = ROOT / "questions_json"
AUDIT_DIR = ROOT / "data_audits"
HAN = r"\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
CJK_OPEN = "（《「『【"
CJK_CLOSE = "，。；：、？！）》」』】"

# These are normal repeated phrases, not extraction damage.
DUPLICATE_ALLOWLIST = {
    "一個一個",
    "人人",
    "天天",
    "時時",
    "往往",
    "常常",
    "漸漸",
    "僅僅",
    "剛剛",
    "慢慢",
}

MANUAL_REPAIRS = {
    ("110-1-U1.json", 40, "question"): {
        "cleaned": "關於AI 結合智慧醫療，下列敘述何者「不」正確？",
        "reason": "移除重複的「下列敘述何者」片段",
        "confidence": "high",
        "source": "iPAS 110-1 科目1官方試題",
    },
    ("110-1-U1.json", 40, "option.A"): {
        "cleaned": "可能提高醫院及醫療人員的工作效率，減少工作中的差錯",
        "reason": "移除重複的選項尾段",
        "confidence": "high",
        "source": "iPAS 110-1 科目1官方試題",
    },
    ("110-1-U1.json", 40, "option.B"): {
        "cleaned": "通過遠程醫療、遠程會診，可解決醫療資源區域分配不均問題",
        "reason": "移除重複的選項尾段",
        "confidence": "high",
        "source": "iPAS 110-1 科目1官方試題",
    },
    ("110-2-U1.json", 26, "question"): {
        "cleaned": "依照頻率可將電磁波分為三類，請問無線通訊4G 的行動基地台所發射的電磁波，應屬於下列何類電磁波輻射？",
        "reason": "移除重複的題幹中段與尾段",
        "confidence": "high",
        "source": "iPAS 110-2 科目1官方試題",
    },
    ("110-2-U2.json", 26, "question"): {
        "cleaned": "利用比特幣加密演算法可以提供一套跨平台且具高安全性的物聯網裝置身份辨識與資訊傳輸機制。下列何者為比特幣目前所採用的資料加密方法？",
        "reason": "移除重複的題幹中段",
        "confidence": "high",
        "source": "iPAS 110-2 科目2官方試題",
    },
    ("110-2-U2.json", 50, "option.D"): {
        "cleaned": "使用者不可更改軟體內容用於販售",
        "reason": "移除重複的選項尾段",
        "confidence": "high",
        "source": "iPAS 110-2 科目2官方試題",
    },
    ("111-1-U1.json", 28, "question"): {
        "cleaned": "下列何種電磁波的能量足打斷化學鍵（游離），會破壞生物細胞分子，因此影響人體健康？",
        "reason": "移除重複的題幹中段",
        "confidence": "high",
        "source": "iPAS 111-1 科目1官方試題",
    },
    ("111-1-U1.json", 18, "question"): {
        "cleaned": "物聯網架構「不」包含下列哪一階層？",
        "reason": "移除問句後方重複的題幹片段",
        "confidence": "high",
        "source": "依完整題幹語意及選項交叉確認",
    },
    ("111-1-U1.json", 43, "question"): {
        "cleaned": "台北市停車管理工程處開發「台北好停車」App 來找尋可停車的停車場，下列何者為可能得知停車場中車位使用情況再上傳雲端計算目前可使用車位數？",
        "reason": "將官方原文的「可停車停車場」修復為語意完整的「可停車的停車場」",
        "confidence": "medium",
        "source": "iPAS 111-1 科目1官方試題（官方原文亦含重複字樣）",
    },
}


def clean_spacing(text):
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    previous = None
    while value != previous:
        previous = value
        value = re.sub(rf"(?<=[{HAN}]) (?=[{HAN}])", "", value)
        value = re.sub(rf"(?<=[{HAN}{re.escape(CJK_CLOSE)}]) (?=[{re.escape(CJK_CLOSE)}])", "", value)
        value = re.sub(rf"(?<=[{re.escape(CJK_CLOSE)}]) (?=[{HAN}])", "", value)
        value = re.sub(rf"(?<=[{re.escape(CJK_OPEN)}]) (?=[{HAN}])", "", value)
        value = re.sub(rf"(?<=[{HAN}]) (?=[{re.escape(CJK_OPEN)}])", "", value)
    return value


def duplicate_candidates(text):
    candidates = []
    seen = set()
    compact = clean_spacing(text)

    for size in range(16, 1, -1):
        for start in range(0, len(compact) - size * 2 + 1):
            phrase = compact[start : start + size]
            if compact[start + size : start + size * 2] != phrase:
                continue
            repeated = phrase * 2
            if repeated in DUPLICATE_ALLOWLIST or not re.search(rf"[{HAN}]", phrase):
                continue
            key = (start, phrase)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                {
                    "offset": start,
                    "phrase": phrase,
                    "context": compact[max(0, start - 18) : start + size * 2 + 18],
                }
            )

    # Keep only maximal candidates at a given location.
    maximal = []
    occupied = set()
    for item in candidates:
        span = range(item["offset"], item["offset"] + len(item["phrase"]) * 2)
        if any(position in occupied for position in span):
            continue
        maximal.append(item)
        occupied.update(span)
    return maximal


def iter_text_fields(question):
    yield "question", question, "question"
    for option in question.get("options", []):
        yield f'option.{option.get("id", "?")}', option, "text"


def build_audit(apply_changes=False):
    changes = []
    duplicates = []
    manual_repairs = []
    changed_files = set()

    for path in sorted(QUESTION_DIR.glob("*-U?.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        file_changed = False

        for question in data.get("questions", []):
            for field, owner, key in iter_text_fields(question):
                original = str(owner.get(key, ""))
                cleaned = clean_spacing(original)
                repair = MANUAL_REPAIRS.get((path.name, question.get("id"), field))
                final = repair["cleaned"] if repair else cleaned

                if final != original:
                    reasons = []
                    confidence = "high"
                    if cleaned != original:
                        reasons.append("移除 PDF 換行造成的中文斷詞空格")
                    if repair:
                        reasons.append(repair["reason"])
                        confidence = repair["confidence"]
                    changes.append(
                        {
                            "file": path.name,
                            "questionId": question.get("id"),
                            "field": field,
                            "reason": "；".join(reasons),
                            "confidence": confidence,
                            "original": original,
                            "cleaned": final,
                        }
                    )
                    if apply_changes:
                        owner[key] = final
                        file_changed = True

                if repair:
                    manual_repairs.append(
                        {
                            "file": path.name,
                            "questionId": question.get("id"),
                            "field": field,
                            **repair,
                            "original": original,
                        }
                    )

                for candidate in duplicate_candidates(final):
                    duplicates.append(
                        {
                            "file": path.name,
                            "questionId": question.get("id"),
                            "field": field,
                            "status": "needs_review",
                            **candidate,
                        }
                    )

        if apply_changes and file_changed:
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            changed_files.add(path.name)

    report = {
        "createdAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "scope": "questions_json/*-U?.json 的 question 與 options[].text",
        "applied": apply_changes,
        "recovery": "每筆 changes 同時保存 original 與 cleaned；可依 file、questionId、field 還原。Git 提交前版本亦保留完整原文。",
        "summary": {
            "spacingChanges": len(changes),
            "duplicateCandidates": len(duplicates),
            "manualRepairs": len(manual_repairs),
            "changedFiles": len(changed_files),
            "changesByField": dict(Counter(item["field"].split(".")[0] for item in changes)),
        },
        "changes": changes,
        "manualRepairs": manual_repairs,
        "duplicateCandidates": duplicates,
    }
    return report


def main():
    run_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    parser = argparse.ArgumentParser(description="稽核並修正 PDF 文字擷取造成的空格與重複片段")
    parser.add_argument("--apply", action="store_true", help="套用高信心空格修正並寫入稽核紀錄")
    parser.add_argument(
        "--report",
        default=str(AUDIT_DIR / f"pdf-text-audit-{run_stamp}.json"),
        help="稽核報告輸出路徑",
    )
    args = parser.parse_args()

    report = build_audit(apply_changes=args.apply)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], ensure_ascii=False))
    print(f"report={report_path}")


if __name__ == "__main__":
    main()
