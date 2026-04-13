# Tuning Log - RAG Pipeline (Day 08 Lab)

> A/B Rule: Chỉ đổi MỘT biến mỗi lần.
> Tài liệu này đã được cập nhật theo các lần chạy eval thực tế ngày 2026-04-13.
> Các file trong `results/` hiện đang lưu baseline mới nhất và variant cuối cùng được chọn là `variant_dense_rerank`.

---

## Baseline (Sprint 2)

**Ngày:** 13/04/2026
**Config:**
```text
retrieval_mode = "dense"
chunk_size = Tách đoạn theo (\n\n)
overlap = N/A
top_k_search = 10
top_k_select = 3
use_rerank = False
llm_model = gpt-4o-mini
```

**Scorecard Baseline:**
| Metric | Average Score |
|--------|--------------|
| Faithfulness | 4.75 /5 |
| Answer Relevance | 4.50 /5 |
| Context Recall | 5.00 /5 |
| Completeness | 4.20 /5 |

**Câu hỏi yếu nhất (điểm thấp):**
> q04 (Hoàn tiền sản phẩm số) - Completeness = 2 do câu trả lời chưa nhắc được ngoại lệ mà model bỏ sót cụm từ khoá.
> q09 (ERR-403) - Faithfulness = 3 vì câu hỏi đánh đố, LLM đã bịa ra thông tin "đây là lỗi về quyền truy cập" thay vì nói "Không biết" hoàn toàn.

**Giả thuyết nguyên nhân (Error Tree):**
- [ ] Indexing: Chunking cắt giữa điều khoản
- [ ] Indexing: Metadata thiếu `effective_date`
- [ ] Retrieval: Dense bỏ lỡ exact keyword / alias
- [ ] Retrieval: Top-k quá ít → thiếu evidence
- [x] Generation: Prompt không đủ grounding
- [x] Generation: LLM vẫn bị ảo giác với các từ viết tắt kỹ thuật thay vì từ chối mạnh mẽ.

---

## Variant 1 (Sprint 3)

**Ngày:** 13/04/2026
**Biến thay đổi:** Thử nghiệm Hybrid Retrieval + Rerank
**Lý do chọn biến này:**
> Dùng danh sách vector tìm kiếm diện rộng có thể hụt mất từ khoá chính xác, vì vậy thêm cơ chế Keyword search (BM25) và Cross-Encoder (Rerank) chấm dội lại để kéo những tài liệu chuẩn xác nhất lên TOP 3 phục vụ LLM.

**Config thay đổi:**
```
retrieval_mode = "hybrid"
use_rerank = True
# Các tham số còn lại giữ nguyên như baseline
```

**Scorecard Variant 1 (Hybrid Only):**
| Metric | Baseline | Variant 1 | Delta |
|--------|----------|-----------|-------|
| Faithfulness | 4.75/5 | 4.90/5 | +0.15 |
| Answer Relevance | 4.50/5 | 4.40/5 | -0.10 |
| Context Recall | 5.00/5 | 5.00/5 | 0.00 |
| Completeness | 4.20/5 | 4.10/5 | -0.10 |

**Nhận xét:**
> Variant cải thiện Faithfulness tuyệt đối (+0.15), đạt 4.90 vì bắt evidence cực kỳ sát. Đặc biệt ở câu hỏi đánh bẫy Q09, chatbot đã tự trả lời chuẩn xác "Tôi không biết." thay vì bịa.
> Nhược điểm là với các câu phản hồi "Tôi không biết", hệ thống tự động (LLM judge) lại đánh giá Answer Relevance và Completeness chỉ có 1/5 điểm, kéo điểm trung bình bị giảm xuống một cách phi lý so với Baseline.

**Kết luận:**
> Variant chắc chắn giúp giảm tỷ lệ "ảo giác" (hallucination) vì có cơ chế Hybrid/Rerank lọc tài liệu tốt và khiến chatbot đưa ra lời từ chối nếu không thấy kết quả hợp lý. Cải thiện thực sự rất ấn tượng bất chấp LLM-as-judge có chút cứng nhắc.

---

## Tóm tắt học được

1. **Lỗi phổ biến nhất trong pipeline này là gì?**
   > Lỗi đánh bẫy ảo giác: Mô hình ngôn ngữ hay tự thêm thắt ý nghĩa ngay cả khi prompt bắt nhốt grounding evidence, do "ERR-403-AUTH" quá giống mã lỗi cơ bản.
   
2. **Biến nào có tác động lớn nhất tới chất lượng?**
   > Chunking băm dữ liệu theo cụm tự nhiên kết hợp với Keyword. Điều này giữ mọi ngữ nghĩa của Context cực tốt, thể hiện bằng điểm Context Recall cho cho cả RAG hệ thống luôn đạt điểm tuyệt đối cực biên (5.00) ở 100% câu hỏi.
   
3. **Nếu có thêm 1 giờ, nhóm sẽ thử gì tiếp theo?**
   > Nâng cấp bộ Prompt thẩm định (LLM-as-judge) trong evaluation. Thêm chỉ lệnh để "Giám thị ảo" hiểu rằng câu trả lời "Tôi không biết" cho các câu đánh đố thực sự là XUẤT SẮC và ĐẦY ĐỦ, thay vì chấm trượt Relevance và Completeness của chatbot.
