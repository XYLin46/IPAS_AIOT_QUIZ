import json
from collections import Counter, defaultdict
from pathlib import Path


root = Path(__file__).resolve().parent / "questions_json"
catalog = json.loads((root / "u1-chapters.json").read_text(encoding="utf-8"))
u2_catalog = json.loads((root / "u2-categories.json").read_text(encoding="utf-8"))
chapter_ids = {chapter["id"] for chapter in catalog["chapters"]}
catalog_counts = {chapter["id"]: chapter["questionCount"] for chapter in catalog["chapters"]}
u2_category_ids = {category["id"] for category in u2_catalog["categories"]}
u2_catalog_counts = {category["id"]: category["questionCount"] for category in u2_catalog["categories"]}

counts = Counter()
u2_counts = Counter()
samples = defaultdict(list)
subject_totals = Counter()

for subject in ("U1", "U2"):
    files = sorted(root.glob(f"*-{subject}.json"))
    assert len(files) == 12, (subject, len(files))

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("subject") == subject, path
        assert len(data["questions"]) == data["questionCount"] == 50, path

        for question in data["questions"]:
            subject_totals[subject] += 1
            explanation = question.get("explanation", "")
            assert len(explanation) >= 40, (path, question["id"])
            assert "作答時要把每個選項" not in explanation, (path, question["id"])
            assert "因此，應以正確選項" not in explanation, (path, question["id"])
            assert "依題庫答案" not in explanation, (path, question["id"])
            assert all(str(option.get("text", "")).strip() for option in question["options"]), (path, question["id"])
            assert "optionExplanations" not in question, (path, question["id"])

            if subject == "U1":
                assert question.get("chapterId") in chapter_ids, (path, question["id"])
                assert question.get("chapterName"), (path, question["id"])
                counts[question["chapterId"]] += 1
                if len(samples[question["chapterId"]]) < 3:
                    samples[question["chapterId"]].append(
                        f'{path.stem} Q{question["id"]}: {question["question"]}'
                    )
            else:
                assert question.get("categoryId") in u2_category_ids, (path, question["id"])
                assert question.get("categoryName"), (path, question["id"])
                assert "chapterId" not in question and "chapterName" not in question, (path, question["id"])
                u2_counts[question["categoryId"]] += 1

assert subject_totals == {"U1": 600, "U2": 600}, subject_totals
assert dict(counts) == {key: value for key, value in catalog_counts.items() if value}, (counts, catalog_counts)
assert dict(u2_counts) == {key: value for key, value in u2_catalog_counts.items() if value}, (u2_counts, u2_catalog_counts)

print("VALIDATION OK")
print("subject totals:", dict(subject_totals))
print("chapter counts:", dict(counts))
print("U2 category counts:", dict(u2_counts))
for chapter in catalog["chapters"]:
    if samples[chapter["id"]]:
        print(f'\n[{chapter["id"]} {chapter["name"]}]')
        print("\n".join(samples[chapter["id"]]))
