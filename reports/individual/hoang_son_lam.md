# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Hoàng Sơn Lâm  
**Vai trò trong nhóm:** Retrieval Owner  
**Ngày nộp:** 2026-04-13  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Tôi chịu trách nhiệm chính cho toàn bộ module retrieval của RAG pipeline, trải dài từ Sprint 2 đến Sprint 4.

Ở **Sprint 2**, tôi hoàn thiện indexing pipeline — implement logic embed chunk và lưu vào ChromaDB, implement `retrieve_dense()` để query bằng embedding vector (cosine similarity), và `call_llm()` để gọi OpenAI API.

Ở **Sprint 3**, tôi implement đầy đủ các chiến lược retrieval nâng cao: `retrieve_sparse()` dùng BM25 cho keyword search, `retrieve_hybrid()` kết hợp dense + sparse bằng Reciprocal Rank Fusion (RRF), `rerank()` dùng LLM chấm điểm relevance từng chunk, và `transform_query()` với 3 strategies (expansion, decomposition, HyDE).

Ở **Sprint 4**, tôi xây dựng FastAPI backend với SSE streaming và Web UI để visualize từng bước thinking của pipeline theo thời gian thực. Công việc của tôi cung cấp retrieval output cho phần generation và evaluation mà các thành viên khác phụ trách.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

**Hybrid Retrieval và RRF** là concept tôi hiểu sâu nhất sau lab. Khi implement riêng lẻ dense (vector) và sparse (BM25), tôi nhận ra mỗi phương pháp có điểm mạnh khác nhau: dense tốt với câu hỏi ngữ nghĩa tự nhiên, còn sparse tốt với keyword chính xác như mã lỗi hay tên tài liệu. Vấn đề là score của hai hệ thống hoàn toàn khác thang đo — cosine similarity nằm trong [0,1] còn BM25 có thể lên hàng chục — nên không thể cộng trực tiếp.

RRF giải quyết điều này bằng cách dùng **rank** thay vì raw score: `1/(K + rank)` với K=60. Cách tiếp cận này scale-invariant, không cần normalize score, và đơn giản để implement. Qua thực nghiệm, tôi thấy hybrid retrieval giúp pipeline robust hơn trên cả hai loại query, dù điểm eval tổng thể không chênh lệch lớn so với baseline dense.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Điều ngạc nhiên lớn nhất là **rerank bằng LLM rất tốn kém và chậm**. Ban đầu tôi kỳ vọng LLM-based reranking sẽ cải thiện rõ rệt chất lượng retrieval, nhưng thực tế mỗi chunk cần 1 API call riêng — với 10 chunks tức 10 lần gọi GPT chỉ cho bước rerank. Điều này làm latency tăng đáng kể và chi phí API cao.

Khó khăn thứ hai là khi implement `retrieve_sparse()` với BM25: tôi phải load toàn bộ document từ ChromaDB rồi build BM25 index mỗi lần query — không hiệu quả về mặt performance. Giả thuyết ban đầu của tôi là ChromaDB sẽ hỗ trợ cả full-text search, nhưng thực tế nó chỉ hỗ trợ vector search, nên phải dùng thư viện `rank_bm25` riêng.

Ngoài ra, kết quả eval cho thấy variant (hybrid + rerank) không vượt trội baseline dense như kỳ vọng — Completeness thậm chí giảm nhẹ từ 4.20 xuống 4.05, cho thấy retrieval tốt hơn không đảm bảo generation tốt hơn.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** q07 — "Approval Matrix để cấp quyền hệ thống là tài liệu nào?"

**Phân tích:**

Đây là câu hỏi **hard** được thiết kế để test hybrid retrieval — query dùng tên cũ "Approval Matrix" trong khi tài liệu thực tế đã đổi tên thành "Access Control SOP" (access-control-sop.md).

**Baseline (dense):** Faithfulness=5, Relevance=5, Context Recall=5, Completeness=**2**. Dense retrieval tìm đúng tài liệu nguồn (recall hoàn hảo) vì embedding nắm được ngữ nghĩa "Approval Matrix" liên quan đến "Access Control". Tuy nhiên, LLM chỉ mô tả chung về tài liệu mà không nêu được thông tin quan trọng nhất: tài liệu đã đổi tên thành "Access Control SOP".

**Variant (hybrid + rerank):** Kết quả gần tương tự — Completeness vẫn chỉ **2**. Hybrid retrieval vẫn tìm đúng source, nhưng generation vẫn không extract được thông tin đổi tên.

**Lỗi nằm ở generation, không phải retrieval.** Context Recall = 5/5 ở cả hai config chứng tỏ retrieval đã hoàn thành tốt nhiệm vụ. Vấn đề là grounded prompt chưa đủ cụ thể để hướng dẫn LLM trích xuất thông tin về sự thay đổi tên tài liệu. Điều này cho thấy cải thiện retrieval không đủ — cần cải thiện cả prompt engineering ở bước generation.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

1. **Thay LLM reranking bằng cross-encoder** (sentence-transformers CrossEncoder): eval cho thấy rerank không cải thiện đáng kể kết quả, nhưng nếu dùng cross-encoder thay vì gọi GPT từng chunk sẽ nhanh hơn gấp nhiều lần và rẻ hơn, cho phép thử nghiệm nhiều iteration hơn.

2. **Cải thiện BM25 performance**: cache BM25 index thay vì rebuild mỗi query — kết quả eval cho thấy sparse search hoạt động tốt nhưng latency là bottleneck chính khi kết hợp trong hybrid mode.

---

*Lưu file này với tên: `reports/individual/hoang_son_lam.md`*
