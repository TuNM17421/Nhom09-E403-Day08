# Tuning Log - RAG Pipeline (Day 08 Lab)

> A/B Rule: Chỉ đổi MỘT biến mỗi lần.
> Tài liệu này đã được cập nhật theo các lần chạy eval thực tế ngày 2026-04-13.
> Các file trong `results/` hiện đang lưu baseline mới nhất và variant cuối cùng được chọn là `variant_dense_rerank`.

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
| Faithfulness | 4.80 / 5 |
| Answer Relevance | 4.55 / 5 |
| Context Recall | 5.00 / 5 |
| Completeness | 4.25 / 5 |

**Nhận xét baseline:**
- Baseline dense hoạt động ổn định trên phần lớn bộ 20 câu hỏi, đặc biệt mạnh ở các câu fact retrieval trực tiếp như `q01`, `q02`, `q03`, `q05`, `q13` đến `q20`.
- `Context Recall = 5.00/5` cho thấy retriever đã mang về đúng nguồn mong đợi ở tất cả các câu có expected source. Điều này khá quan trọng vì nó cho thấy bottleneck chính của hệ thống không còn nằm ở recall.
- Điểm yếu nằm nhiều hơn ở bước generation và answer shaping: model đôi khi retrieve đúng nhưng trả lời thiếu, diễn giải chưa đúng trọng tâm, hoặc abstain chưa đủ gọn.

**Câu hỏi yếu nhất của baseline:**
- `q04 (digital products refund)` - Faithfulness `3/5`, Completeness `2/5`. Retriever lấy đúng source nhưng answer thêm khả năng ngoại lệ “trừ khi có lỗi do nhà sản xuất”, làm lệch với chính sách cấm hoàn tiền cho hàng kỹ thuật số.
- `q07 (Approval Matrix)` - Recall `5/5` nhưng Completeness `2/5`. Hệ thống retrieve đúng tài liệu Access Control SOP, nhưng answer không nêu rõ đây là tên mới của “Approval Matrix for System Access”.
- `q09 (ERR-403-AUTH)` - Faithfulness `4/5`, Relevance `3/5`, Completeness `3/5`. Answer có xu hướng suy đoán lỗi liên quan đến quyền truy cập thay vì abstain ngắn gọn và hướng người dùng về IT Helpdesk.
- `q16 (laptop mới có bị tính phí không)` - Relevance `1/5`, Completeness `1/5`. Đây là câu thiếu context thật sự; pipeline abstain đúng tinh thần nhưng chưa đưa ra hướng dẫn hữu ích nào thêm.

**Giả thuyết nguyên nhân (Error Tree):**
- [ ] Indexing: Chunking cắt giữa điều khoản
- [ ] Indexing: Metadata thiếu `effective_date`
- [ ] Retrieval: Dense bỏ lỡ exact keyword / alias
- [ ] Retrieval: Top-k quá ít nên thiếu evidence
- [x] Generation: Answer đôi khi diễn giải quá tay dù đã retrieve đúng nguồn
- [x] Generation: Abstain chưa đủ sắc gọn ở câu thiếu context

**Kết luận từ baseline:**
Tập lỗi chính không còn nằm ở retrieval recall mà nằm ở cách model chọn và trình bày thông tin từ context. Vì vậy, các experiment tiếp theo nên tập trung vào việc cải thiện quality của top chunks đưa vào prompt hoặc kiểm soát generation tốt hơn.

---

## Variant 1 (Sprint 3)

**Ngày:** 2026-04-13  
**Biến thay đổi:** `retrieval_mode: "dense" -> "hybrid"`  
**Lý do chọn biến này:**
Đây là vòng A/B đầu tiên để kiểm tra giả thuyết ban đầu: corpus có nhiều exact term và alias như `Approval Matrix`, `P1`, `Flash Sale`, `IT-ACCESS`, nên hybrid (`dense + BM25`) có thể tăng recall hoặc tăng completeness ở các câu keyword-heavy mà không phải đổi prompt hay LLM.

**Config Variant 1:**
```text
retrieval_mode = "hybrid"
top_k_search = 10
top_k_select = 3
use_rerank = False
llm_model = "gpt-4o-mini"
```

**Scorecard Variant 1 (Hybrid Only):**
| Metric | Baseline | Variant 1 | Delta |
|--------|----------|-----------|-------|
| Faithfulness | 4.85/5 | 4.90/5 | +0.05 |
| Answer Relevance | 4.50/5 | 4.40/5 | -0.10 |
| Context Recall | 5.00/5 | 5.00/5 | 0.00 |
| Completeness | 4.15/5 | 4.00/5 | -0.15 |

**Nhận xét:**
- `q04` cải thiện Completeness từ `2 -> 3`.
- `q07` cải thiện Completeness từ `2 -> 3`, cho thấy hybrid có ích phần nào ở câu alias.
- Tuy nhiên `q06` giảm rất mạnh từ `Complete=5` xuống `Complete=1`, cho thấy hybrid có thể kéo về thêm chunk liên quan nhưng lại làm câu trả lời bị trôi khỏi ý chính.
- `q09` cũng kém hơn baseline vì answer chuyển sang abstain quá ngắn, làm giảm Relevance và Completeness.

**Kết luận:**
Variant hybrid-only không được chọn làm cấu hình cuối. Dù có vài cải thiện cục bộ, kết quả tổng thể kém hơn baseline ở `relevance` và `completeness`, trong khi `context_recall` không tăng thêm. Điều này cho thấy giả thuyết “vấn đề chính nằm ở retrieval recall” không đúng với test set này.

---

## Variant 2 (được chọn)

**Biến thay đổi:** `use_rerank: False -> True` trên dense retrieval  
**Config:**
```text
retrieval_mode = "dense"
top_k_search = 10
top_k_select = 3
use_rerank = True
llm_model = "gpt-4o-mini"
```

**Scorecard Variant 2 (Dense + Rerank):**
| Metric | Baseline | Variant 2 | Delta |
|--------|----------|-----------|-------|
| Faithfulness | 4.80/5 | 4.90/5 | +0.10 |
| Answer Relevance | 4.55/5 | 4.70/5 | +0.15 |
| Context Recall | 5.00/5 | 5.00/5 | 0.00 |
| Completeness | 4.25/5 | 4.25/5 | 0.00 |

**Nhận xét:**
- `q06` cải thiện rõ từ `4/5/5/5` lên `5/5/5/5`, tức rerank giúp chọn chunk trả lời đúng trọng tâm escalation hơn.
- `q08` cải thiện Completeness từ `4 -> 5`.
- `q09` cải thiện từ `4/3/None/3` lên `5/5/None/2`: answer grounded hơn và relevant hơn, dù vẫn chưa hoàn hảo ở phần hướng dẫn xử lý.
- `q10` cải thiện Relevance từ `2 -> 3`, nghĩa là rerank giúp model trả lời đúng trọng tâm hơn trong case thiếu policy đặc biệt cho VIP.
- Các câu fact-based còn lại hầu như giữ nguyên, nên rerank không làm hỏng những câu baseline vốn đã tốt.

**Kết luận:**
Dense + rerank là variant tốt nhất trong các thử nghiệm ngày 2026-04-13. Đây cũng là variant được chọn làm cấu hình cuối vì:
- Chỉ đổi đúng một biến so với baseline.
- Cải thiện `faithfulness` và `relevance`.
- Không làm giảm `context_recall`.
- Giữ `completeness` ngang baseline và cải thiện ở một số câu khó.

---

## Ghi chú thêm về exploratory run

Nhóm cũng đã thử một cấu hình `hybrid + rerank`:

```text
retrieval_mode = "hybrid"
use_rerank = True
label = "variant_hybrid_rerank"
```

Kết quả exploratory run này cho:
- Faithfulness: `4.90/5`
- Relevance: `4.40/5`
- Context Recall: `5.00/5`
- Completeness: `4.10/5`

Run này không được chọn vì dù faithfulness tăng nhẹ, relevance và completeness lại thấp hơn baseline, đặc biệt ở `q09` và `q10`. Điều này củng cố nhận định rằng trên bộ test hiện tại, rerank có ích hơn khi áp dụng trên dense baseline ổn định thay vì chồng thêm lên hybrid.

---

## Tóm tắt học được

1. **Lỗi phổ biến nhất trong pipeline này là gì?**  
   Lỗi phổ biến nhất trong bộ test hiện tại không phải là retrieve sai nguồn, mà là answer chưa tối ưu dù đã có đúng evidence: thiếu detail quan trọng, diễn giải quá mức, hoặc abstain chưa đủ đúng trọng tâm.

2. **Biến nào có tác động lớn nhất tới chất lượng?**  
   Trên dữ liệu thực nghiệm ngày 2026-04-13, rerank trên dense baseline là biến có tác động tích cực nhất. Hybrid-only không cải thiện tổng thể, còn dense+rerrank cho delta tốt nhất mà vẫn giữ recall tối đa.

3. **Nếu có thêm 1 giờ, nhóm sẽ thử gì tiếp theo?**  
   Hoàn thiện thêm phần scoring hoặc chuẩn hóa prompt abstain cho các câu thiếu context như `q09`, `q10`, `q16`, sau đó thử một vòng `dense + rerank + prompt abstain chặt hơn` để xem có kéo được `relevance` và `completeness` ở các câu khó hay không.
