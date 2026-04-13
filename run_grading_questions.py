import json
from datetime import datetime
from pathlib import Path

from rag_answer import rag_answer


DATA_PATH = Path(__file__).parent / "data" / "grading_questions.json"
LOGS_DIR = Path(__file__).parent / "logs"
OUTPUT_PATH = LOGS_DIR / "grading_run.json"

# Dung cau hinh tot nhat hien tai theo tuning log.
BEST_CONFIG = {
    "retrieval_mode": "dense",
    "use_rerank": True,
    "top_k_search": 10,
    "top_k_select": 3,
}


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Khong tim thay grading_questions.json tai: {DATA_PATH}"
        )

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    log = []
    for q in questions:
        result = rag_answer(
            q["question"],
            retrieval_mode=BEST_CONFIG["retrieval_mode"],
            top_k_search=BEST_CONFIG["top_k_search"],
            top_k_select=BEST_CONFIG["top_k_select"],
            use_rerank=BEST_CONFIG["use_rerank"],
            verbose=False,
        )
        log.append(
            {
                "id": q["id"],
                "question": q["question"],
                "answer": result["answer"],
                "sources": result["sources"],
                "chunks_retrieved": len(result["chunks_used"]),
                "retrieval_mode": result["config"]["retrieval_mode"],
                "use_rerank": result["config"]["use_rerank"],
                "timestamp": datetime.now().isoformat(),
            }
        )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print(f"Da luu grading log tai: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()