# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Lê Tuấn Đạt  
**Vai trò trong nhóm:** Eval Owner  
**Ngày nộp:** 13/04/2026  

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Trong dự án RAG Helpdesk, tôi phụ trách xuyên suốt Sprint 4: Đánh giá và Đo lường (Evaluation & Scorecard). Cụ thể, tôi đã chuẩn bị bộ 20 test case đa dạng vào file `test_questions.json`, bao gồm cả những câu hỏi dễ, khó và cả những câu hỏi dạng "bẫy" (không có trong tài liệu) để thử thách mô hình. 

Công việc chính của tôi là hoàn thiện hệ thống chấm điểm tự động (LLM-as-Judge) để định lượng hiệu năng trên 4 tiêu chí: Faithfulness, Answer Relevance, Context Recall và Completeness trong file `eval.py`. Tôi phối hợp trực tiếp với kết quả từ Sprint 2 (Baseline) và Sprint 3 (Variant của Tech Lead) để chạy A/B Testing, xuất bảng so sánh, từ đó rút ra kết luận hệ thống có thực sự hoạt động tốt hơn nhờ Hybrid Retrieval & Rerank hay không và ghi vào Tuning Log.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Tôi thực sự vỡ lẽ và hiểu sâu sắc hơn về khái niệm **Faithfulness** và **Relevance** trong việc đo lường ảo giác (hallucination). 

Trước đây, tôi có định kiến rằng một model xịn là phải luôn luôn trả lời được mọi thứ người dùng hỏi (Relevance). Tuy nhiên, sau lab này, tôi hiểu kiến trúc RAG bắt buộc đề cao Faithfulness (Sự trung thành): Chatbot phải tuyệt đối phục tùng vào các mẩu cắt (Context chunks) cung cấp mớm cho nó. Việc mạnh dạn nói "Tôi không biết" khi ngữ cảnh không cung cấp dữ liệu không hề là sự thất bại, ngược lại, đó là một tín hiệu cực kỳ đáng tin cậy. Bảo vệ pipeline RAG không phải là cố gắng vắt não model tự suy luận, mà là quản trị giới hạn hiểu biết của nó thật an toàn.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Điều bất ngờ nhất và cũng làm tôi mất thời gian suy nghĩ nhất là sự cứng nhắc của các vị "Giám khảo AI" (LLM-as-judge). 

Khi RAG model hoạt động hoàn hảo - nó phát hiện ra câu hỏi bẫy và đáp khéo léo "Tôi không biết", thì thay vì được biểu dương, vị giám khảo ảo (script evaluation) lại cho ngay 1/5 điểm ở tiêu chí Relevance và Completeness vì cho rằng *"Answer does not address the question at all"*. Giả thuyết ban đầu của tôi là mô hình giám khảo của OpenAI đủ thông minh để tự linh hoạt theo ngữ cảnh, nhưng thực tế, prompt đánh giá của giám khảo cần được mài dũa (prompt engineering) cực kỳ tinh tế, giống hệt như cách ta tinh chỉnh prompt cho chatbot hệ thống vậy.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** [q09] `ERR-403-AUTH là lỗi gì và cách xử lý?`

**Phân tích:**
Đây là một câu đánh bẫy cực mạnh mà tôi bỏ vào, vì mã lỗi này hoàn toàn CỐ TÌNH bị loại bỏ khỏi 5 file policy gốc.
- Ở **Baseline (Dense Mode)**: Hệ thống bị hở sườn nghiêm trọng ở chặng Generation. Model nhận được đoạn ngữ cảnh không liên quan nhưng đã tự tin "bịa" ra rằng *"ERR-403-AUTH là lỗi liên quan đến quyền truy cập..."* (vì model nó tự đoán chữ AUTH là Auth). Điểm Faithfulness tụt xuống 3 và hoàn toàn sai nguyên tắc RAG.
- Ở **Variant (Hybrid + Rerank)**: Cấu hình mới đã tìm không ra keyword BM25 và cross-encoder chấm điểm tương quan của các đoạn tài liệu đều ở mức 0. Nhờ bằng chứng bị chặn triệt để, Chatbot không có dữ liệu mớm nên đã ngoan ngoãn chốt hạ: *"Tôi không biết."*. Điểm Faithfulness lập tức vọt lên điểm tuyệt đối 5/5. Sự thay đổi ấn tượng này chứng minh sức mạnh của Rerank trong việc giảm thiểu Hallucination từ tận gốc.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Với vị thế là Eval Owner, tôi sẽ cải thiện lại toàn bộ khối lệnh Prompt trong hàm đánh giá của Giám thị AI. Bằng cách thêm điều kiện rõ ràng vào prompt của `score_completeness` và `score_answer_relevance`: *"Hãy trao trọn 5/5 điểm nếu expected answer yêu cầu từ chối trả lời và Model thực sự đã từ chối trả lời hợp lệ"*. Điều này sẽ giúp Scorecard trở nên chuẩn mực thực tế hơn và không bắt lỗi oan cho Chatbot của nhóm. Trang bị thêm thư viện Ragas (RAG Assessment) chuẩn quốc tế cũng là kế hoạch tôi muốn tích hợp vào hệ thống về sau.
