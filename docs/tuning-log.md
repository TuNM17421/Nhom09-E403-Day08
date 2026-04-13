# Tuning Log - RAG Pipeline (Day 08 Lab)

> A/B Rule: Chỉ đổi MỘT biến mỗi lần.
> Tài liệu này được điền theo snapshot repo hiện tại ngày 2026-04-13. Các ô điểm số dùng `N/A` là do scorecard thực tế chưa được sinh trong repo ở thời điểm mình tổng hợp.

---

## Baseline (Sprint 2)

**Ngày:** 2026-04-13  
**Config:**
```text
retrieval_mode = "dense"
chunk_size = 400 tokens
overlap = 80 tokens
top_k_search = 10
top_k_select = 3
use_rerank = False
llm_model = "gpt-4o-mini"
```

**Scorecard Baseline:**
| Metric | Average Score |
|--------|--------------|
| Faithfulness | N/A - `score_faithfulness()` chưa chấm tự động |
| Answer Relevance | N/A - `score_answer_relevance()` chưa implement |
| Context Recall | N/A - chưa có run baseline thực tế trong `results/` |
| Completeness | N/A - `score_completeness()` chưa implement |

**Trạng thái hiện tại của repo:**
- `retrieve_dense()` và `call_llm()` trong `rag_answer.py` vẫn chưa được implement, nên chưa thể chạy baseline end-to-end để sinh scorecard thật.
- `results/scorecard_baseline.md` và `results/scorecard_variant.md` hiện chưa tồn tại trong repo.
- Vì vậy, phần dưới đây ghi theo dạng pre-eval analysis: nêu câu hỏi có rủi ro thấp/cao và giả thuyết tuning trước khi có số liệu thật.

**Câu hỏi dự kiến yếu nhất (theo phân tích test set và corpus):**
- `q07 (Approval Matrix → Access Control SOP)` - nhiều khả năng dense recall thấp vì query dùng alias/tên cũ, trong khi tài liệu chính dùng tên mới.
- `q09 (ERR-403-AUTH)` - cần abstain chặt. Nếu generation không được ép đủ mạnh, model dễ suy diễn từ prior knowledge thay vì nói thiếu dữ liệu.
- `q10 (refund khẩn cấp cho VIP)` - câu hỏi có phần "VIP" không có trong docs; pipeline phải giữ được phần chuẩn hóa quy trình nhưng không bịa quy trình đặc biệt.

**Giả thuyết nguyên nhân (Error Tree):**
- [ ] Indexing: Chunking cắt giữa điều khoản
- [ ] Indexing: Metadata thiếu `effective_date`
- [x] Retrieval: Dense bỏ lỡ exact keyword / alias
- [ ] Retrieval: Top-k quá ít nên thiếu evidence
- [x] Generation: Prompt cần abstain đủ mạnh để tránh bịa ở câu thiếu context
- [ ] Generation: Context quá dài → lost in the middle

Lý do đánh dấu: corpus hiện tại đã được chia rất sát theo heading và mỗi section đang nằm gọn trong một chunk, nên rủi ro lớn hơn nằm ở retrieval recall với alias/keyword và ở khả năng abstain của bước generation.

---

## Variant 1 (Sprint 3)

**Ngày:** 2026-04-13  
**Biến thay đổi:** `retrieval_mode: "dense" -> "hybrid"`  
**Lý do chọn biến này:**
Biến đầu tiên nên thử là retrieval mode vì nó tác động trực tiếp tới recall nhưng chưa làm thay đổi prompt, model hoặc cách chấm. Test set có một số tín hiệu rất rõ cho hybrid:
- `q07` dùng tên cũ "Approval Matrix" trong khi tài liệu hiện hành ghi "Access Control SOP".
- Corpus chứa nhiều exact term như `P1`, `VPN`, `Flash Sale`, `Admin Access`, `IT-ACCESS`.
- Hybrid giúp kết hợp semantic match của dense với keyword match của BM25, phù hợp hơn dense thuần cho corpus nghiệp vụ kiểu policy + SOP + FAQ.

**Config thay đổi:**
```text
retrieval_mode = "hybrid"
top_k_search = 10
top_k_select = 3
use_rerank = False
llm_model = "gpt-4o-mini"
```

**Scorecard Variant 1:**
| Metric | Baseline | Variant 1 | Delta |
|--------|----------|-----------|-------|
| Faithfulness | N/A | N/A | N/A |
| Answer Relevance | N/A | N/A | N/A |
| Context Recall | N/A | N/A | N/A |
| Completeness | N/A | N/A | N/A |

**Nhận xét trước khi chạy thật:**
- Kỳ vọng cải thiện rõ nhất ở `q07`, vì đây là trường hợp alias/name drift điển hình của retrieval.
- Các câu có keyword mạnh như `q01` và `q06` (P1, escalation) nhiều khả năng không giảm chất lượng vì dense vốn đã hợp với chúng; hybrid chỉ bổ sung thêm tín hiệu sparse.
- `q09` không nên "cải thiện" theo kiểu trả lời dài hơn; thành công ở câu này là retrieve ít noise và abstain đúng.
- Nếu hybrid kéo về quá nhiều chunk chứa keyword nhưng ít liên quan về ngữ nghĩa, faithfulness có thể không tăng tương ứng với context recall. Đó là lý do chưa bật rerank trong Variant 1.

**Kết luận:**
Variant 1 là lựa chọn hợp lý nhất cho vòng tune đầu vì:
- Nó bám đúng A/B rule: chỉ đổi một biến là retrieval mode.
- Nó có giả thuyết rõ ràng, xuất phát từ cấu trúc query/corpus chứ không đổi ngẫu nhiên.
- Nó dễ giải thích trong report: nếu delta tăng ở `context_recall` và `completeness`, ta có thể quy phần lớn cải thiện cho hybrid retrieval.

Điều kiện để giữ Variant 1 làm cấu hình cuối:
- `Context Recall` tăng ở các câu alias/keyword-heavy.
- `Faithfulness` không giảm đáng kể.
- Không làm pipeline kém ổn định ở các câu easy vốn dense đã xử lý tốt.

---

## Variant 2 (nếu có thời gian)

**Biến thay đổi:** bật `use_rerank = True` sau khi hybrid đã ổn định  
**Config:**
```text
retrieval_mode = "hybrid"
top_k_search = 10
top_k_select = 3
use_rerank = True
```

**Mục tiêu của Variant 2:**
- Giảm noise khi hybrid mang về nhiều chunk có keyword đúng nhưng không phải chunk trả lời trực tiếp.
- Giữ top-3 chunks đưa vào prompt gọn hơn, tăng khả năng generation bám đúng evidence.

**Khi nào mới nên thử Variant 2:**
- Chỉ sau khi Variant 1 đã có scorecard thật.
- Chỉ khi thấy `context_recall` đã ổn nhưng `faithfulness` hoặc `completeness` chưa tăng tương xứng.

---

## Tóm tắt học được

1. **Lỗi phổ biến nhất trong pipeline này là gì?**  
   Với snapshot repo hiện tại, rủi ro lớn nhất không nằm ở chunking mà nằm ở retrieval recall cho alias/keyword và khả năng abstain ở câu hỏi thiếu context.

2. **Biến nào có tác động lớn nhất tới chất lượng?**  
   Retrieval mode là biến có tác động kỳ vọng lớn nhất, vì test set chứa cả câu semantic (`refund policy`, `remote work`) lẫn câu exact-term/alias (`Approval Matrix`, `P1`, `ERR-403-AUTH`).

3. **Nếu có thêm 1 giờ, nhóm sẽ thử gì tiếp theo?**  
   Hoàn thiện `retrieve_dense()`, `call_llm()`, và các hàm scoring để sinh scorecard thật; sau đó chạy hybrid-only trước, rồi mới thử rerank như một experiment thứ hai tách biệt.
