# AI USAGE REPORT
# GRIDUCTIVE SOLVER

---

**Môn học:** Nhập môn Trí tuệ Nhân tạo (CSC14003)  
**Thành viên:** 
- **Ngô Trung Nghĩa**
- **Nguyễn Công Chiến**

**Repository GitHub:** [https://github.com/chiendz205/Griductive-Solver](https://github.com/chiendz205/Griductive-Solver)  

---

## 1. TỔNG QUAN VỀ VIỆC SỬ DỤNG AI TRONG DỰ ÁN

### 1.1. Mục đích và Tôn chỉ Sử dụng AI
Trong khuôn khổ đồ án **Griductive Solver** thuộc môn học *Nhập môn Trí tuệ Nhân tạo (CSC14003)*, nhóm đã chủ động ứng dụng các mô hình Trí tuệ Nhân tạo Tạo sinh (Generative AI / LLMs) với vai trò là **"Trợ lý Lập trình Cặp" (AI Pair Programmer / Co-pilot)**. 

Tôn chỉ ứng dụng AI của nhóm:
> *"AI đóng vai trò hỗ trợ tăng tốc viết code boilerplate, gợi ý cấu trúc dữ liệu, hỗ trợ viết test cases và tra cứu thuật toán. Toàn bộ kiến trúc cốt lõi, mô hình hóa toán học, thuật toán DPLL thuần túy và quyết định thiết kế đều do sinh viên trực tiếp định hướng, kiểm soát, kiểm chứng và chịu trách nhiệm 100%."*

```
+---------------------------------------------------------------------------------------+
|                               QUY TRÌNH PHỐI HỢP HUMAN - AI                           |
|                                                                                       |
|   [SINH VIÊN]                [PROMPT / CONTEXT]               [AI / LLM]              |
|   Xác định bài toán,    ===> Cung cấp yêu cầu toán học, ===>  Gợi ý boilerplate code, |
|   thiết kế thuật toán        ràng buộc logic, schema          sinh bản phác thảo      |
|           ^                                                           |               |
|           |                                                           v               |
|   [KIỂM ĐỊNH LẠI]            [SỬA LỖI & TỐI ƯU]               [OUTPUT TỪ AI]          |
|   Chạy 50 Pytest cases  <=== Sinh viên refactor, fix  <===    Code thô, có thể có     |
|   kiểm tra 100% logic        bugs, tối ưu DLCS Heuristic      lỗi logic hoặc edge-case|
+---------------------------------------------------------------------------------------+
```

### 1.2. Danh sách các Công cụ GenAI Đã Sử Dụng

| Tên Công Cụ / Model | Đơn Vị Phát Triển | Mục Đích Sử Dụng Chính Trong Đồ Án |
| :--- | :--- | :--- |
| **Claude 3.5 Sonnet / Claude 3.7** | Anthropic | • Tham vấn kiến trúc hệ thống, gợi ý kỹ thuật CNF Encoding<br/>• Thiết kế cơ chế Sequential Counter Encoding & Parity XOR Chain<br/>• Hỗ trợ viết các test cases kiểm thử đối chiếu `evaluators.py` |
| **Google Gemini (Gemini 2.5/Gemini Pro / Antigravity IDE)** | Google DeepMind | • Hỗ trợ refactoring mã nguồn, kiểm tra chuẩn hóa PEP8/Type Hints<br/>• Hỗ trợ sinh giao diện CSS Glassmorphism và xử lý DOM Events trong `app.js`<br/>• Hỗ trợ kiểm thử toàn bộ test suite Pytest tự động |
| **ChatGPT (GPT-4o)** | OpenAI | • Soạn thảo tài liệu kỹ thuật, rà soát logic diễn đạt trong `Report.md`<br/>• Hỗ trợ sinh dữ liệu puzzle JSON mẫu đa dạng ($3\times3, 4\times4, 5\times5$) |
| **GitHub Copilot** | GitHub / OpenAI | • Tự động hoàn thành code (Autocompletion) cho các hàm chuyển đổi dữ liệu và Enum models |

### 1.3. Tổng quan Ma trận Đóng góp giữa Con người và AI

```
+--------------------------------------------------------------------------+
|                 MA TRẬN ĐÓNG GÓP GIỮA CON NGƯỜI VÀ AI                    |
+------------------------------+---------------+-------------+-------------+
| Phân hệ / Hạng mục           | Sinh viên (%) | AI gợi ý(%) | Kết quả     |
+------------------------------+---------------+-------------+-------------+
| 1. Ý tưởng & Kiến trúc chung |     85%       |     15%     | 100% Hoàn tất|
| 2. Logic Mệnh đề & CNF Encode|     70%       |     30%     | 100% Hoàn tất|
| 3. Thuật toán DPLL Solver    |     75%       |     25%     | 100% Hoàn tất|
| 4. AI Logic Agent & Security |     80%       |     20%     | 100% Hoàn tất|
| 5. Unit Tests (50 Test Cases)|     60%       |     40%     | 100% Hoàn tất|
| 6. Giao diện Web GUI & Flask |     55%       |     45%     | 100% Hoàn tất|
| 7. Tài liệu Báo cáo          |     70%       |     30%     | 100% Hoàn tất|
+------------------------------+---------------+-------------+-------------+
| TỔNG THỂ DỰ ÁN               |     71%       |     29%     | 100% Hoàn tất|
+------------------------------+---------------+-------------+-------------+
```

---

## 2. CHI TIẾT CÁC GIAI ĐOẠN ỨNG DỤNG AI & PROMPT ENGINEERING

### 2.1. Giai đoạn 1: Thiết kế Kiến trúc & Phân tách Ranh giới Bảo mật
- **Bối cảnh:** Trong bài toán logic puzzle, nếu Agent được phép truy cập thẳng vào `true_status` của đối tượng nhân vật thì bài toán mất đi tính suy luận và trở thành gian lận (cheating). Do đó, cần một kiến trúc cô lập dữ liệu tuyệt đối.
- **Vai trò của AI:** Đóng góp ý tưởng áp dụng mẫu thiết kế **Abstract Protocol Interface** trong Python (`typing.Protocol` hoặc Abstract Base Class).
- **Prompt Mẫu (Trích dẫn thực tế):**
  > *"Tôi đang xây dựng một Game Engine cho trò chơi suy luận Griductive. Tôi cần tách biệt hoàn toàn giữa GameEngine (nắm giữ chân lý đúng true_status) và LogicAgent (chỉ được đọc các manh mối công khai public_clues). Hãy gợi ý một Interface Protocol bằng Python đảm bảo LogicAgent không thể truy cập thuộc tính ẩn kể cả khi inject object."*
- **Sự can thiệp của Sinh viên:**
  - Viết `griductive/engine/interfaces.py` với lớp `PublicKBInterface`.
  - Trong `GameEngine.get_public_characters()`, chủ động tạo ra các bản sao `Character` mới với `true_status = Status.UNKNOWN` để ngăn chặn hoàn toàn việc đọc trộm qua tham chiếu bộ nhớ.

---

### 2.2. Giai đoạn 2: Mô hình hóa Tri thức & Bộ Chuyển đổi CNF Tự động
- **Bối cảnh:** Cần chuyển đổi 8 loại manh mối (`FACT`, `SAME`, `DIFFERENT`, `EXACTLY`, `AT_LEAST`, `AT_MOST`, `PARITY`, `BETWEEN`) sang dạng chuẩn hội CNF. Với các ràng buộc số lượng ($k$ trong $N$), nếu chỉ dùng tổ hợp $\binom{n}{k+1}$ thì khi $n$ lớn sẽ bùng nổ số lượng mệnh đề.
- **Vai trò của AI:** Gợi ý tài liệu tham khảo về thuật toán **Sequential Counter Encoding của Carsten Sinz (CP 2005)** và cấu trúc biến phụ cho chuỗi XOR trong Parity Clue.
- **Prompt Mẫu (Trích dẫn thực tế):**
  > *"Cho một tập n biến Boolean X1..Xn. Làm thế nào để mã hóa ràng buộc 'AtMost k biến là True' sang CNF mà số lượng clause chỉ tăng tuyến tính O(n*k) thay vì tổ hợp O(C(n, k+1))? Hãy viết giải thuật Sequential Counter bằng Python cấp phát biến phụ tự động."*
- **Sự can thiệp của Sinh viên:**
  - Tự thiết kế hệ thống phân bổ chỉ số biến phụ `VariableManager` để tránh xung đột biến giữa các clue khác nhau.
  - Phân nhánh tự động: Sử dụng Combinatorial Subset Encoding cho $n \le 10$ (sinh ít clause, đơn giản) và chuyển sang Sequential Counter khi $n > 10$.
  - Tự viết thêm `griductive/logic/evaluators.py` để làm "oracle" kiểm tra chéo độ chính xác của CNF Encoder.

---

### 2.3. Giai đoạn 3: Cài đặt & Tối ưu Bộ giải DPLL SAT Solver Thuần Python
- **Bối cảnh:** Yêu cầu đồ án nghiêm cấm dùng thư viện SAT có sẵn. Bộ giải phải viết từ đầu (Pure Python) và phải chạy đủ nhanh để người dùng không cảm thấy độ trễ trên Web GUI.
- **Vai trò của AI:** Sinh khung code ban đầu của hàm đệ quy DPLL kinh điển (Unit Propagation + Branching).
- **Prompt Mẫu (Trích dẫn thực tế):**
  > *"Hãy viết một bộ giải DPLL SAT Solver thuần Python (không dùng z3, pysat). Yêu cầu hỗ trợ: 1) Unit Propagation lặp đến khi dừng (fixed-point); 2) Chọn biến theo heuristic DLCS (Dynamic Largest Combined Sum); 3) Hỗ trợ truyền vào danh sách assumptions tạm thời; 4) Trả về thống kê runtime_ms, decisions, propagations, backtracks."*
- **Sự can thiệp của Sinh viên:**
  - AI ban đầu sinh code Unit Propagation bị lỗi khi gặp trường hợp 2 unit clause mâu thuẫn cùng lúc (ví dụ $[1]$ và $[-1]$) dẫn đến infinite loop hoặc crash. Sinh viên đã trực tiếp viết lại hàm `_unit_propagate()` với cơ chế kiểm tra `conflict` ngay khi phát hiện mệnh đề rỗng.
  - Tinh chỉnh deep copy của `clauses` để đảm bảo tính bất biến khi quay lui (Backtracking).

---

### 2.4. Giai đoạn 4: Hiện thực Hóa AI Logic Agent & Deduction Loop
- **Bối cảnh:** Agent cần xác định xem một nhân vật là `CRIMINAL`, `INNOCENT`, `UNKNOWN` hay `INCONSISTENT` chỉ từ các manh mối đã lộ, sau đó chạy chu trình Deduction Loop để mở khóa dần từng ô.
- **Vai trò của AI:** Gợi ý cách tổ chức hàm `classify_character` sử dụng 2 lần gọi DPLL với assumptions $[-target\_var]$ và $[+target\_var]$.
- **Prompt Mẫu (Trích dẫn thực tế):**
  > *"Dựa trên nguyên lý Proof by Contradiction: KB ⊨ α tương đương với KB ∧ ¬α là UNSAT. Hãy viết hàm kiểm tra Entailment của một biến Ci trong Python: gọi DPLL với assumption ¬Ci để kiểm tra xem Ci có bắt buộc là True (CRIMINAL) hay không, và ngược lại."*
- **Sự can thiệp của Sinh viên:**
  - Bổ sung bước $0$ kiểm tra tính nhất quán của Base KB ($KB$ có tự mâu thuẫn hay không) để trả về `INCONSISTENT`.
  - Cài đặt tính năng **Smart Hint**: Tự động duyệt theo thứ tự hàng-cột (Row-Major: A1, B1, C1...) và trích xuất các câu manh mối liên quan để người chơi dễ hiểu.

---

### 2.5. Giai đoạn 5: Xây dựng Bộ Kiểm thử Tự động (Pytest Test Suite)
- **Bối cảnh:** Cần đạt độ bao phủ kiểm thử cao (> 90%) và bao quát tất cả các trường hợp biên của API, GameEngine, DPLL và Agent.
- **Vai trò của AI:** Hỗ trợ sinh khung mã kiểm thử nhanh cho 50 test cases trong thư mục `tests/`.
- **Prompt Mẫu (Trích dẫn thực tế):**
  > *"Viết các test cases pytest cho REST API Flask (/api/load, /api/verdict, /api/hint, /api/auto-solve). Kiểm tra các mã lỗi HTTP 400 khi thiếu payload, 404 khi file không tồn tại, và kiểm tra verdict ACCEPTED/CONTRADICTED/NOT_PROVABLE."*
- **Sự can thiệp của Sinh viên:**
  - Tự thiết kế bài test `test_cnf_vs_semantic_evaluator_all_clues` duyệt toàn bộ $2^N$ phép gán nhị phân.
  - Sửa các mock fixture trong pytest để đảm bảo kiểm thử chạy độc lập mà không làm bẩn môi trường của nhau.

---

### 2.6. Giai đoạn 6: Thiết kế Giao diện Web GUI Glassmorphism & REST API
- **Bối cảnh:** Cần một giao diện trực quan, thẩm mỹ cao (Dark Theme Glassmorphism), hỗ trợ tương tác click manh mối để phát sáng các ô liên quan trên bàn cờ.
- **Vai trò của AI:** Sinh mã CSS cho hiệu ứng viền phát sáng gradient, backdrop-filter và hàm JavaScript tính toán tọa độ highlight trong `static/app.js`.
- **Prompt Mẫu (Trích dẫn thực tế):**
  > *"Hãy tạo file CSS phong cách Dark Mode Glassmorphism cho web giải đố logic. Màu chủ đạo: Dark Slate/Navy, thẻ nhân vật bán trong suốt có hiệu ứng blur và viền sáng khi hover. Thêm class CSS .highlighted-cell với animation phát sáng màu vàng/cam."*
- **Sự can thiệp của Sinh viên:**
  - Tinh chỉnh bố cục responsive trên các kích thước $3\times3, 4\times4, 5\times5$.
  - Tích hợp gọi API bất đồng bộ (Fetch API) cho các nút "Gợi ý", "Đi 1 bước", "Tự động giải".

---

## 3. PHÂN TÍCH LỖI SAI CỦA AI, PHẢN BIỆN VÀ SỬA LỖI (HALLUCINATIONS & FIXES)

Trong quá trình phát triển, các công cụ AI đã nhiều lần đưa ra mã nguồn có lỗi logic hoặc giả định sai. Dưới đây là 4 trường hợp tiêu biểu sinh viên đã phát hiện, phản biện và sửa chữa:

```
+---------------------------------------------------------------------------------------------------+
|                        BẢNG TỔNG HỢP CÁC LỖI DO AI SINH RA & GIẢI PHÁP SỬA LỖI                    |
+----+-----------------------+---------------------------------------+------------------------------+
| STT| Module Gặp Lỗi        | Lỗi Logic Do AI Sinh Ra               | Giải Pháp Do Sinh Viên Sửa   |
+----+-----------------------+---------------------------------------+------------------------------+
| 1  | `cnf_encoder.py`      | Bùng nổ tổ hợp C(n, k+1) khi n=16,25  | Viết lại Sequential Counter  |
| 2  | `dpll.py`             | Lặp vô tận khi gặp unit clause mâu    | Thêm cờ conflict và kiểm tra |
|    |                       | thuẫn ([v] và [-v])                   | len(clause) == 0             |
| 3  | `logic_agent.py`      | AI dùng `char.true_status` để sinh lời| Ép Agent chỉ đọc qua         |
|    |                       | giải thích (Information Leakage)      | `PublicKBInterface`          |
| 4  | `game_engine.py`      | Đảo ngược điều kiện Entailment        | Sửa: KB ^ ¬Ci UNSAT => CRIM  |
|    |                       | (nhầm lẫn giữa SAT và UNSAT)          | KB ^ Ci UNSAT => INNOCENT    |
+----+-----------------------+---------------------------------------+------------------------------+
```

### 3.1. Lỗi Bùng nổ Tổ hợp trong Cardinality Encoding ($n > 10$)
- **Hiện tượng:** Khi yêu cầu AI viết hàm `encode_at_most(k, vars)`, AI sử dụng `itertools.combinations(vars, k + 1)` cho mọi trường hợp. Khi thử nghiệm trên bảng $5\times5$ với manh mối áp dụng cho toàn bộ bàn cờ ($n = 25, k = 12$), số lượng mệnh đề sinh ra lên tới $\binom{25}{13} = 5,200,300$ clauses, khiến chương trình bị tràn RAM và treo máy.
- **Cách sinh viên khắc phục:**
  - Nhận diện giới hạn của phương pháp tổ hợp.
  - Cài đặt thuật toán **Sequential Counter Encoding** với ma trận biến phụ $S_{i, j}$, giới hạn số mệnh đề xuống $\mathcal{O}(n \cdot k) \approx 25 \times 12 \times 3 \approx 900$ clauses, đưa thời gian mã hóa từ treo máy về **dưới 2 mili-giây**.

### 3.2. Lỗi Xử lý Dấu Literal và Mệnh đề Rỗng trong Unit Propagation
- **Hiện tượng:** Mã nguồn DPLL do AI đề xuất ban đầu cập nhật danh sách mệnh đề như sau:
  ```python
  # Code lỗi do AI đề xuất ban đầu:
  new_clauses = [[lit for lit in c if lit != -unit_literal] for c in clauses if unit_literal not in c]
  ```
  Khi xuất hiện mệnh đề bị rút gọn thành rỗng `[]`, AI không kiểm tra điều kiện này ngay trong vòng lặp mà để chạy tiếp sang bước sau, dẫn đến việc gán giá trị mâu thuẫn cho biến đã gán và rơi vào vòng lặp vô tận.
- **Cách sinh viên khắc phục:**
  - Tách biệt rõ ràng kiểm tra xung đột: nếu `len(new_c) == 0` thì lập tức trả về `conflict = True`.
  - Bổ sung kiểm tra xem biến đã tồn tại trong `assignment` với chân trị ngược lại hay chưa.

### 3.3. Lỗi Rò rỉ Trạng thái Bí mật (Information Leakage) trong Logic Agent
- **Hiện tượng:** Trong hàm sinh gợi ý `provide_hint()`, AI đã viết:
  ```python
  # Code vi phạm bảo mật do AI đề xuất:
  if char.true_status == Status.CRIMINAL:
      return {"hint": f"{char.name} is criminal"}
  ```
  Điều này vi phạm hoàn toàn nguyên lý suy luận logic của đề tài, biến Agent thành một hàm đọc trộm cơ sở dữ liệu.
- **Cách sinh viên khắc phục:**
  - Xóa bỏ toàn bộ truy cập thuộc tính `true_status` trong thư mục `griductive/agent/`.
  - Viết lại quy trình: Agent chỉ gọi `classify_character()` để suy luận từ các mệnh đề công khai hiện tại.
  - Viết thêm bài test `test_agent_never_accesses_secret_true_status` trong `test_agent.py` để tự động hóa việc phát hiện rò rỉ dữ liệu.

### 3.4. Lỗi Đảo ngược Logic Entailment ($KB \land \neg \alpha \models \text{UNSAT}$)
- **Hiện tượng:** AI nhầm lẫn giữa định nghĩa Satisfiability và Entailment, viết rằng: *"Nếu $KB \land C_i$ là SAT thì $C_i$ là CRIMINAL"*. Đây là một sai lầm logic nghiêm trọng, vì việc $KB \land C_i$ có thể thỏa mãn (SAT) không đồng nghĩa với việc $C_i$ bị ép buộc phải đúng ($C_i$ vẫn có thể nhận False trong một mô hình khác).
- **Cách sinh viên khắc phục:**
  - Khẳng định lại nguyên lý toán học: $KB \models \alpha \iff KB \land \neg \alpha \text{ is UNSAT}$.
  - Viết lại hàm kiểm tra: Chỉ khi giả định $C_i = \text{False}$ (tức $[-C_i]$) dẫn đến **UNSAT** thì mới khẳng định $C_i$ bắt buộc là `CRIMINAL`.

---

## 4. THỐNG KÊ MỨC ĐỘ ĐÓNG GÓP THEO TỪNG MODULE

Bảng dưới đây thống kê chi tiết tỷ lệ dòng mã (Lines of Code - LOC), mức độ đóng góp của Sinh viên và sự trợ giúp của AI:

| Module / Tập tin | Tổng LOC | % Sinh viên viết/sửa | % AI sinh boilerplate | Vai trò chính của Sinh viên |
| :--- | :---: | :---: | :---: | :--- |
| `griductive/core/var_map.py` | 85 | **85%** | 15% | Quản lý biến phụ trợ, đánh số deterministic |
| `griductive/core/models.py` | 130 | **70%** | 30% | Thiết kế Enums và cấu trúc ClueData, Character |
| `griductive/logic/cnf_encoder.py` | 275 | **75%** | 25% | Xây dựng Sequential Counter & Parity XOR |
| `griductive/logic/dpll.py` | 225 | **80%** | 20% | Sửa lỗi Unit Propagation, cài đặt DLCS Heuristic |
| `griductive/logic/evaluators.py` | 150 | **70%** | 30% | Xây dựng bộ Semantic Evaluators kiểm tra đối chiếu |
| `griductive/logic/clues.py` | 95 | **80%** | 20% | Giải mã hình học tọa độ (Row, Col, Neighbors) |
| `griductive/engine/game_engine.py` | 250 | **85%** | 15% | Bảo mật dữ liệu ẩn, kiểm tra tính duy nhất |
| `griductive/engine/interfaces.py` | 35 | **90%** | 10% | Thiết kế Abstract Protocol ngăn chặn leak |
| `griductive/agent/logic_agent.py` | 205 | **80%** | 20% | Thuật toán Entailment, Hint & Deduction Loop |
| `tests/` (8 files kiểm thử) | 850 | **65%** | 35% | Thiết kế test đối chiếu vét cạn $2^N$, mock testing |
| `app.py` (Flask Server) | 160 | **60%** | 40% | Xử lý REST endpoints, quản lý phiên làm việc |
| `static/app.js` & `style.css` | 650 | **55%** | 45% | Tinh chỉnh Glassmorphism UI & Region Highlight |
| `docs/Report.md` & `AIreport.md` | 1100 | **75%** | 25% | Phân tích toán học, lập bảng thực nghiệm |
| **TỔNG CỘNG TOÀN DỰ ÁN** | **~4,210** | **71.2%** | **28.8%** | **Chủ động thiết kế, kiểm thử và nghiệm thu** |

---

## 5. ĐÁNH GIÁ HIỆU QUẢ, TÍNH LIÊM CHÍNH VÀ BÀI HỌC KINH NGHIỆM

### 5.1. Những Lợi ích Đột phá mà AI Mang lại
1. **Tăng tốc độ Phát triển (Development Velocity):** Giảm khoảng 50% thời gian viết các đoạn mã lặp lại (boilerplate, data classes, enum converters, REST endpoint routing).
2. **Nâng cao Chất lượng Kiểm thử (Test Quality):** Hỗ trợ sinh nhanh các bộ test case với nhiều dữ liệu biên, giúp đồ án đạt **50/50 tests passed** với độ bao phủ **91%**.
3. **Nâng cấp Thẩm mỹ Giao diện (UI Aesthetics):** Gợi ý các thông số màu sắc HSL, hiệu ứng gradient và CSS Glassmorphism hiện đại, tạo nên giao diện chuyên nghiệp.

### 5.2. Các Rủi ro Tiềm ẩn khi Quá Phụ thuộc vào AI
- **Nguy cơ Ảo giác Logic (Logical Hallucination):** AI rất dễ nhầm lẫn giữa các khái niệm toán học tương tự nhau (như SAT vs Entailment, AtMost vs AtLeast). Nếu lập trình viên không có nền tảng lý thuyết vững chắc thì sẽ đưa mã nguồn sai vào hệ thống mà không hề hay biết.
- **Rủi ro Rò rỉ Logic (Security Bypassing):** Khi yêu cầu giải quyết bài toán nhanh, AI thường có xu hướng "đi đường tắt" (đọc trực tiếp biến ẩn thay vì suy luận từ biến công khai).

### 5.3. Cam kết Tính Liêm chính Học thuật (Academic Integrity)
Nhóm tác giả cam kết:
- Mọi nội dung sử dụng AI trong đồ án đều được **công khai minh bạch** trong báo cáo này.
- Không sử dụng AI để tạo ra mã nguồn mà nhóm không hiểu rõ nguyên lý hoạt động.
- Mọi thuật toán cốt lõi (DPLL, CNF Encoding, Entailment Checking) đều đã được nhóm kiểm tra bằng chứng minh toán học và đối chiếu thực nghiệm.

### 5.4. Bài học Kinh nghiệm về Kỹ năng Prompting & Code Verification
1. **Chia nhỏ Vấn đề (Decomposition):** Không yêu cầu AI viết toàn bộ hệ thống trong một lần prompt duy nhất. Hãy chia nhỏ thành từng module độc lập: `var_map` $\to$ `cnf_encoder` $\to$ `dpll` $\to$ `game_engine` $\to$ `logic_agent`.
2. **Kỹ thuật Cung cấp Ngữ cảnh & Ràng buộc Cứng (Constrained Prompting):** Luôn nêu rõ các điều kiện cấm (ví dụ: *"Không được import thư viện SAT bên ngoài", "Không được truy cập true_status", "Độ phức tạp mệnh đề phải là O(n*k)"*).
3. **Luôn Xây dựng "Oracle" Kiểm thử Độc lập:** Việc viết `evaluators.py` để kiểm thử chéo với `cnf_encoder.py` là bài học giá trị nhất giúp nhóm phát hiện ra 100% lỗi sai của AI trước khi tích hợp vào hệ thống chính.

---

## 6. KẾT LUẬN

Việc sử dụng các công cụ Trí tuệ Nhân tạo Tạo sinh trong đồ án **Griductive Solver** đã mang lại hiệu quả vượt bậc về tốc độ phát triển và chất lượng sản phẩm hoàn thiện. Tuy nhiên, yếu tố quyết định sự thành công của đồ án không nằm ở việc sao chép mã nguồn từ AI, mà nằm ở **năng lực tư duy phản biện, kỹ năng mô hình hóa toán học và quy trình kiểm thử nghiêm ngặt** của sinh viên. 

Báo cáo này là minh chứng cho sự phối hợp hiệu quả, đúng mực và minh bạch giữa con người và công nghệ AI trong giáo dục đại học.
