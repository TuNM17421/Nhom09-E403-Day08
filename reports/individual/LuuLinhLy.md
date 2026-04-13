# Báo Cáo Cá Nhân - Lab Day 08: RAG Pipeline

**Họ và tên:** Lưu Linh Ly
**Vai trò trong nhóm:** Documentation Owner  
**Ngày nộp:** 2026-04-13  
**Độ dài yêu cầu:** 500-800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Trong lab này, tôi đảm nhận vai trò Documentation Owner, tập trung vào việc biến các quyết định kỹ thuật của nhóm thành tài liệu có thể nộp và có thể giải thích được. Tôi rà lại `README.md`, `SCORING.md`, `index.py`, `rag_answer.py`, `eval.py` và dữ liệu trong `data/docs/` để hoàn thiện `docs/architecture.md` và `docs/tuning-log.md`. Cụ thể, tôi điền lại phần kiến trúc indexing, retrieval, generation, số chunk thực tế của 5 tài liệu, rồi cập nhật baseline/variant theo code hiện hành. Sau khi nhóm chạy evaluation, tôi chuyển `tuning-log.md` từ mức giả thuyết sang mức có evidence. Công việc của tôi gắn trực tiếp với Tech Lead, Retrieval Owner và Eval Owner vì tài liệu chỉ có giá trị khi khớp code và scorecard.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Sau lab này, tôi hiểu rõ hơn rằng documentation tốt không phải là phần viết sau cùng cho “đẹp repo”, mà là công cụ giúp cả nhóm nhìn ra hệ thống của mình đang mạnh hay yếu ở đâu. Khi đọc `index.py`, tôi thấy chunking không chỉ là thao tác kỹ thuật để chia văn bản, mà còn quyết định việc một chunk có giữ được trọn ý chính sách hay không. Khi đọc `eval.py`, tôi hiểu rõ hơn rằng nếu thay nhiều biến cùng lúc thì score tăng hay giảm cũng khó giải thích. Kết quả thực tế cho thấy `context_recall` đã đạt `5.00/5` từ baseline, nghĩa là bottleneck chính không còn nằm ở retrieval mà ở bước generation và answer shaping. Nhờ đó tôi hiểu rằng tài liệu kiến trúc phải phản ánh đúng failure mode thật, không chỉ lặp lại giả thuyết ban đầu.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Điều làm tôi ngạc nhiên nhất là tốc độ thay đổi của repo trong lúc cả nhóm cùng làm. Một số nhận định ban đầu của tôi đã nhanh chóng lỗi thời khi dense retrieval, BM25, hybrid và rerank được merge vào `main`. Khó khăn lớn nhất của tôi không phải là viết markdown, mà là giữ cho tài liệu luôn trung thực với trạng thái code mới nhất. Nếu viết quá sớm, tài liệu sẽ cũ; nếu đợi quá lâu, cả nhóm lại thiếu tài liệu để thống nhất cách giải thích pipeline. Tôi cũng phải chuyển từ ngôn ngữ “kỳ vọng hybrid sẽ tốt hơn” sang ngôn ngữ dựa trên evidence thật, vì kết quả cuối cùng cho thấy hybrid-only không phải biến tốt nhất.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** `q07 - Approval Matrix để cấp quyền hệ thống là tài liệu nào?`

**Phân tích:**

Tôi chọn `q07` vì đây là câu hỏi phản ánh rất rõ sự khác nhau giữa “retrieve đúng nguồn” và “trả lời đủ ý”. Query dùng tên cũ là “Approval Matrix”, trong khi tài liệu thật ghi rằng tên mới là “Access Control SOP”. Ở baseline dense, hệ thống đã retrieve đúng source nên `context_recall = 5/5`, nhưng `completeness` chỉ đạt `2/5` vì câu trả lời không nói rõ đây là tên mới của tài liệu và cũng không nhắc đến file `access-control-sop.md`. Điều này quan trọng với tôi ở vai trò documentation owner, vì ban đầu đây chính là dạng câu tôi dùng để lập luận rằng hybrid có thể giúp. Tuy nhiên, khi nhóm chạy A/B thật, hybrid-only chỉ nâng `completeness` của `q07` từ `2 -> 3`, trong khi tổng thể variant này vẫn kém baseline ở `relevance` và `completeness`. Từ góc nhìn phân tích lỗi, `q07` cho thấy vấn đề không chỉ nằm ở retrieval alias, mà còn nằm ở cách model diễn đạt phần rename mapping. Vì vậy, trong `tuning-log.md` tôi chuyển kết luận từ “hybrid là hướng chính” sang “dense + rerank là cấu hình cuối”.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Nếu có thêm thời gian, tôi muốn làm hai việc. Thứ nhất, tôi sẽ phối hợp với Eval Owner để chuẩn hóa thêm cách chấm cho các câu thiếu context như `q09`, `q10`, `q16`, vì đây là nơi relevance và completeness còn dao động. Thứ hai, tôi muốn viết luôn `reports/group_report.md` để toàn nhóm có một narrative thống nhất: baseline dense đã đủ tốt về recall, hybrid-only không cải thiện tổng thể, và dense+rerrank là cấu hình cuối cùng được chọn.

---