# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Mạnh Tú  
**Vai trò trong nhóm:** Tech Lead  
**Ngày nộp:** 2026-04-13  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Trong lab này tôi đảm nhận vai trò Tech Lead, nên công việc chính của tôi là giữ nhịp triển khai và nối các phần của nhóm thành một pipeline chạy được end-to-end. Ở giai đoạn đầu, tôi tạo repo, xác định structure của project, break down task theo từng sprint và phân role cho từng thành viên để tránh overlap. Về mặt kỹ thuật, tôi trực tiếp làm Sprint 1 và Sprint 4. Ở Sprint 1, tôi tham gia hoàn thiện indexing pipeline gồm preprocess, chunking, embedding và lưu dữ liệu vào ChromaDB. Ở Sprint 4, tôi tập trung vào evaluation loop: tổ chức scorecard, triển khai logic chấm điểm bằng LLM-as-Judge và tổng hợp kết quả baseline so với variant. Phần việc của tôi kết nối trực tiếp với Retrieval Owner và Documentation Owner, vì output của index, answer pipeline và evaluation đều phải thống nhất để phục vụ tuning-log và báo cáo cuối.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Điều tôi hiểu rõ hơn sau lab này là cách hoạt động thực tế của hybrid retrieval, đặc biệt là BM25 và Reciprocal Rank Fusion (RRF). Trước đây tôi hiểu RRF ở mức khái niệm là một cách gộp nhiều danh sách xếp hạng, nhưng sau khi tự triển khai và quan sát output, tôi thấy rõ vì sao nó hữu ích: dense retrieval giỏi bắt nghĩa, còn BM25 giỏi giữ exact keyword hoặc alias. RRF không cộng điểm một cách thô mà kết hợp theo thứ hạng, nên giúp cân bằng giữa semantic match và lexical match. Quan trọng hơn, tôi hiểu rằng hybrid không tự động tốt hơn dense. Nó chỉ có ích khi failure mode thực sự nằm ở recall hoặc alias matching. Nếu bottleneck nằm ở generation hoặc answer shaping, thêm hybrid chưa chắc cải thiện. Đây là điểm tôi thấy có giá trị nhất từ lab này.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Điều làm tôi ngạc nhiên nhất là một số câu hỏi có độ khó `hard` vẫn có thể được xử lý tương đối tốt nếu pipeline retrieve đúng evidence và prompt đủ grounded. Ban đầu tôi có giả thuyết rằng kiến trúc càng phức tạp, ví dụ hybrid kết hợp rerank, thì chất lượng gần như chắc chắn sẽ tốt hơn vì chi phí cao hơn và nhiều thành phần hơn. Tuy nhiên kết quả thực tế lại cho thấy điều ngược lại ở một số case: dense baseline đã cho kết quả chấp nhận được, còn khi thêm hybrid thì có lúc answer lại trôi khỏi trọng tâm. Điều đó khiến tôi rút ra một bài học rõ ràng: không có một architecture tốt nhất cho mọi bài toán, mà chỉ có architecture phù hợp nhất với failure mode đang gặp. Một khó khăn nữa là LLM đôi khi vẫn trả lời thiếu thông tin dù retrieve đã đúng, ví dụ các câu cần nêu đủ điều kiện hoặc ngoại lệ như question 13.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** q16 - laptop mới có bị tính phí không?

**Phân tích:**

Đây là câu tôi thấy thú vị vì nó cho thấy rõ giới hạn của RAG khi dữ liệu thực sự không chứa chính sách tương ứng. Theo tuning log, ở baseline câu này có `Relevance = 1/5` và `Completeness = 1/5`. Điểm đáng chú ý là lỗi chính không nằm ở indexing hay retrieval. Pipeline không fail vì chunk sai hoặc không tìm thấy nguồn liên quan, mà fail vì đây là một câu thiếu context thật sự trong bộ tài liệu. Khi đó generation phải quyết định giữa abstain và suy đoán. Baseline đã đi theo hướng abstain, nhưng câu trả lời chưa đủ hữu ích vì chỉ dừng ở việc không có dữ liệu, chưa hướng người dùng sang bước tiếp theo như liên hệ bộ phận phù hợp hoặc kiểm tra chính sách procurement. Variant dense + rerank không cải thiện nhiều ở câu này, và điều đó hợp lý vì rerank chỉ giúp chọn chunk tốt hơn trong số những gì đã retrieve; nó không thể tạo ra evidence không tồn tại trong corpus. Từ case này tôi rút ra rằng với các câu ngoài phạm vi tài liệu, phần cần cải thiện không phải retrieval mà là thiết kế prompt abstain và fallback policy để câu trả lời vừa an toàn vừa hữu ích hơn cho người dùng.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Nếu có thêm thời gian, tôi muốn thử mở rộng metadata khi insert dữ liệu vào vector store, ví dụ thêm loại tài liệu, phạm vi áp dụng, version và mức độ ưu tiên của policy. Tôi muốn đo xem việc filter hoặc rerank có dùng metadata này sẽ cải thiện được bao nhiêu ở các câu cần reasoning theo ngữ cảnh, thay vì chỉ dựa vào text similarity. Kết quả eval hiện tại cho thấy recall đã tốt, nên bước tiếp theo hợp lý là dùng metadata để làm answer chính xác và đúng phạm vi hơn.
