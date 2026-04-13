# Báo Cáo Nhóm — Lab Day 08: RAG Pipeline

**Nhóm:** 09-E403  
**Ngày nộp:** 2026-04-13  
**Repo:** TuNM17421/Nhom09-E403-Day08

---

## 1. Tổng quan hệ thống

Nhóm xây dựng trợ lý nội bộ cho khối CS, IT Helpdesk và IT Security, trả lời câu hỏi về chính sách hoàn tiền, SLA ticket, quy trình cấp quyền, HR policy và FAQ nội bộ. Pipeline hoạt động theo mô hình grounded RAG: tài liệu được chia chunk có metadata, retrieve theo ngữ cảnh, LLM chỉ được trả lời dựa trên context đã retrieve và phải citation hoặc abstain khi thiếu bằng chứng.

### Kiến trúc pipeline

```
[5 Raw Docs (txt)]
    ↓
[index.py: Preprocess → Heading-based Chunk → Embed (OpenAI) → Store]
    ↓
[ChromaDB Vector Store — 29 chunks]
    ↓
[rag_answer.py: Query → Dense/Sparse/Hybrid Retrieve → (Rerank) → Grounded Prompt → LLM]
    ↓
[Answer + Citation hoặc Abstain]
    ↓
[eval.py: Scorecard + A/B Comparison]
```

---

## 2. Phân công và đóng góp

| Thành viên | Vai trò | Đóng góp chính | Branch / Commits |
|---|---|---|---|
| Nguyễn Mạnh Tú (TuNM17421) | Tech Lead | Setup repo & template code, Sprint 1 indexing (`index.py` — preprocess, chunk, embedding placeholder), Sprint 4 eval (`eval.py` — LLM-as-Judge scoring) | `feature/sprint-1`, `feature/compilete-sprint-4`, `main` |
| Hoàng Sơn Lâm (sonlamhg) | Retrieval Owner | Sprint 2 (embed+store vào ChromaDB, `retrieve_dense`, `call_llm`), Sprint 3 (sparse/BM25, hybrid/RRF, rerank, query transform), Sprint 4 (FastAPI backend + Web UI với SSE streaming) | `feature/retrieval` (4 commits) |
| Lê Tuấn Đạt (Le Tuan Dat) | Eval Owner | Mở rộng `test_questions.json` (10→20 câu), chạy eval pipeline, tạo `scorecard_baseline.md`, `scorecard_variant.md`, `ab_comparison.csv`, implement paragraph-based chunking with overlap | `datletuan` (3 commits) |
| Lưu Linh Ly (luulinhly) | Documentation Owner | Điền chi tiết `docs/architecture.md` và `docs/tuning-log.md` với dữ liệu thực từ các lần chạy eval | `feature/docs` (3 commits) |

---

## 3. Quyết định kỹ thuật chính

### 3.1 Chunking

| Tham số | Giá trị | Lý do |
|---|---|---|
| Chunk size | 400 tokens (~1600 ký tự) | Nằm trong khoảng gợi ý 300-500, đủ giữ nguyên một policy section hoàn chỉnh |
| Overlap | 80 tokens (~320 ký tự) | Giữ ngữ cảnh khi section buộc phải tách, giảm rủi ro mất ngoại lệ/điều kiện ở ranh giới |
| Strategy | Heading-based trước, char-based fallback | Tài liệu nguồn có heading rõ (`=== Điều ... ===`), ưu tiên giữ cấu trúc nghiệp vụ |
| Metadata | source, section, department, effective_date, access | Phục vụ citation, freshness reasoning, debug retrieval |

Kết quả: 5 tài liệu → 29 chunks. Với corpus nhỏ này, hầu hết section đều vừa trong một chunk nên heading-based strategy hoạt động tốt, char-based fallback chưa cần kích hoạt nhiều.

### 3.2 Embedding & Storage

- **Model:** OpenAI `text-embedding-3-small`
- **Vector store:** ChromaDB PersistentClient, collection `rag_lab`, cosine similarity
- **Rebuild strategy:** Xóa collection cũ rồi upsert lại toàn bộ để tránh dữ liệu lẫn

### 3.3 Retrieval — Baseline vs Variant

**Baseline (Sprint 2):** Dense retrieval, top_k_search=10, top_k_select=3, không rerank.

**Các variant đã thử nghiệm (Sprint 3):**

| Config | Faithfulness | Relevance | Context Recall | Completeness | Kết luận |
|---|---|---|---|---|---|
| **Baseline (dense)** | 4.80/5 | 4.55/5 | 5.00/5 | 4.25/5 | Mốc so sánh |
| Variant 1 (hybrid only) | 4.90/5 | 4.40/5 | 5.00/5 | 4.00/5 | Relevance & Complete giảm → **Loại** |
| **Variant 2 (dense+rerank)** | **4.90/5** | **4.70/5** | **5.00/5** | **4.25/5** | Faith +0.10, Rel +0.15 → **Chọn** |
| Exploratory (hybrid+rerank) | 4.90/5 | 4.40/5 | 5.00/5 | 4.05/5 | Rel & Complete giảm → **Loại** |

**Variant được chọn: Dense + Rerank** (chỉ đổi 1 biến `use_rerank: False → True`)

**Lý do:**
- Cải thiện faithfulness (+0.10) và relevance (+0.15) mà không làm giảm recall hay completeness.
- Rerank bằng LLM giúp chọn chunk trả lời đúng trọng tâm hơn, đặc biệt ở q06 (escalation P1: 4→5) và q08 (remote policy: Complete 4→5).
- Hybrid-only thất bại trên test set này vì recall đã 5.00/5 từ baseline — vấn đề không nằm ở recall mà ở quality của chunks được chọn.

### 3.4 Generation

- **Model:** `gpt-4o-mini`, temperature=0, max_tokens=512
- **Prompt strategy:** Grounded prompt — bắt buộc trả lời từ context, citation bằng `[1]`, abstain khi thiếu bằng chứng
- Model này cũng được dùng cho rerank (chấm relevance 0-10) và query transformation

---

## 4. Phân tích kết quả Evaluation

### 4.1 Điểm mạnh

- **Context Recall = 5.00/5 xuyên suốt** tất cả config: retriever luôn tìm đúng source mong đợi, cho thấy indexing và embedding hoạt động tốt trên corpus này.
- **Faithfulness cao (4.80-4.90/5):** Pipeline hiếm khi bịa thông tin, nhờ grounded prompt ép LLM chỉ dùng context.
- Các câu fact retrieval trực tiếp (q01, q02, q03, q05, q08, q13-q15, q17-q20) đạt gần tuyệt đối ở mọi config.

### 4.2 Điểm yếu — Failure modes chính

Lỗi chính của pipeline **không nằm ở retrieval mà ở generation**:

| Câu | Vấn đề | Root cause | Config nào cũng mắc |
|---|---|---|---|
| q04 (digital refund) | Faith=3, Complete=2-3 | Generation thêm ngoại lệ "trừ khi có lỗi nhà sản xuất" — không có trong docs | Có |
| q07 (Approval Matrix) | Complete=2 | Retrieve đúng source nhưng LLM không nêu được tên mới "Access Control SOP" | Có |
| q09 (ERR-403-AUTH) | Rel=1-5, Complete=1-2 | Câu thiếu context — baseline fabricate, variant abstain quá ngắn | Có |
| q10 (VIP refund) | Rel=1, Complete=2-3 | Câu thiếu policy đặc biệt — LLM nói "không biết" thay vì dẫn quy trình chuẩn | Có |
| q16 (laptop phí) | Rel=1, Complete=1 | Abstain đúng nhưng không đưa thông tin hữu ích nào | Có |

**Nhận xét:** Cả 5 câu yếu nhất đều có Context Recall = 5/5 (hoặc None vì không có expected source). Bottleneck rõ ràng ở bước generation: LLM đôi khi diễn giải quá mức, thiếu chi tiết quan trọng, hoặc abstain không đủ hữu ích.

### 4.3 So sánh Baseline vs Variant chi tiết

Variant dense+rerank cải thiện rõ ở các câu cần chọn lọc chunk chính xác:

| Câu | Metric | Baseline | Dense+Rerank | Giải thích |
|---|---|---|---|---|
| q06 (escalation P1) | Faithfulness | 4 | 5 | Rerank chọn đúng chunk mô tả escalation flow |
| q08 (remote policy) | Completeness | 4 | 5 | Rerank ưu tiên chunk chứa đủ điều kiện (probation + Team Lead) |
| q09 (ERR-403-AUTH) | Relevance | 3 | 5 | Rerank giảm noise → answer grounded hơn |
| q10 (VIP refund) | Relevance | 2 | 3 | Rerank giúp trả lời đúng trọng tâm hơn |

Không có câu nào bị giảm điểm khi thêm rerank — đây là lý do chọn variant này.

---

## 5. Bài học rút ra (nhóm)

1. **Retrieval recall không phải bottleneck trên corpus nhỏ.** Với 29 chunks và embedding tốt, dense retrieval đã đạt recall tuyệt đối. Hybrid không cải thiện thêm mà còn gây noise. Điều này có thể khác trên corpus lớn hơn.

2. **Rerank có giá trị thực sự** khi retriever trả về nhiều chunks liên quan nhưng khác mức độ trọng tâm. Rerank giúp đẩy chunk "đúng ý nhất" lên đầu, cải thiện chất lượng generation mà không thay đổi recall.

3. **Generation là bottleneck chính.** Cả 5 câu yếu nhất đều retrieve đúng source nhưng LLM trả lời chưa tối ưu. Cải thiện prompt engineering (đặc biệt cho abstain cases) sẽ có ROI cao hơn việc tiếp tục tune retrieval.

4. **A/B rule quan trọng.** Khi thử hybrid+rerank (đổi 2 biến cùng lúc), kết quả khó giải thích vì không biết cải thiện/giảm sút đến từ biến nào. Chạy từng biến riêng giúp nhóm tự tin hơn khi chọn config cuối.

5. **LLM-based rerank đắt nhưng hiệu quả trên corpus nhỏ.** Với 10 chunks/query, chi phí chấp nhận được. Trên corpus lớn (hàng trăm chunks), nên chuyển sang cross-encoder để tiết kiệm cost và latency.

---

## 6. Nếu có thêm thời gian

1. **Cải thiện prompt cho abstain cases (q09, q10, q16):** Thêm instruction cụ thể trong grounded prompt để khi LLM không tìm thấy answer, vẫn phải đưa gợi ý hữu ích (ví dụ: "liên hệ IT Helpdesk") thay vì chỉ nói "Tôi không biết". Evidence: 3 câu abstain đều có Relevance=1 và Completeness=1.

2. **Thay LLM rerank bằng cross-encoder:** Hiện rerank gọi GPT cho từng chunk (10 API calls/query). Dùng `sentence-transformers` CrossEncoder sẽ nhanh hơn nhiều lần, cho phép iterate nhanh hơn trong eval loop.

3. **Cache BM25 index:** Hiện `retrieve_sparse()` rebuild BM25 index mỗi lần query. Với corpus tĩnh, nên cache index để giảm latency khi dùng hybrid mode.
