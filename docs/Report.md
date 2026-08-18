# BÁO CÁO ĐỒ ÁN: GRIDUCTIVE SOLVER
## HỆ THỐNG SUY LUẬN LOGIC VÀ DPLL SAT AGENT TỰ ĐỘNG
**Môn học:** Nhập môn Trí tuệ Nhân tạo (CSC14003)
**Thành viên thực hiện:** Ngô Trung Nghĩa & Nguyễn Công Chiến  
**Repository GitHub:** https://github.com/chiendz205/Griductive-Solver  
**Demo Video:** https://drive.google.com/drive/folders/griductive-demo  

## 1: TỔNG QUAN ĐỀ TÀI & PHÂN CÔNG CÔNG VIỆC

### 1.1. Giới thiệu Bài toán Griductive
Griductive là một trò chơi giải đố suy luận logic dạng lưới vuông kích thước $N \times N$ ($N \in \{3, 4, 5\}$). Trên mỗi ô của lưới tọa độ $(r, c)$ có một nhân vật xác định. Mỗi nhân vật nắm giữ một trạng thái bí mật (Secret True Status) thuộc một trong hai giá trị Boolean:
- **CRIMINAL** (Tội phạm - tương ứng với chân trị `True` / $1$)
- **INNOCENT** (Vô tội - tương ứng với chân trị `False` / $0$)

Mỗi nhân vật đồng thời sở hữu một hoặc nhiều manh mối (Clues). Ban đầu, chỉ một số manh mối ban đầu được công khai (Initially Revealed Clues). Người chơi (hoặc AI Agent) phải dựa trên các manh mối công khai hiện tại để suy luận logic chặt chẽ (Entailment) xem nhân vật nào bị ép buộc phải là CRIMINAL hoặc INNOCENT. 

Khi một verdict chính xác được đưa ra và chấp nhận (ACCEPTED), nhân vật đó sẽ công khai trạng thái và đồng thời tiết lộ thêm các manh mối do nhân vật đó nắm giữ, tạo thành một chu trình suy luận từng bước (Deduction Loop) cho đến khi toàn bộ bảng câu đố được giải mã hoàn toàn.

### 1.2. Bảng Phân công Công việc Nhóm (2 Thành viên)

| Thành viên | Trách nhiệm chính & Deliverables | Tỷ lệ Hoàn thành |
| :--- | :--- | :---: |
| **Ngô Trung Nghĩa** | • Mô hình hóa Logic Mệnh đề & CNF Encoder (8 loại clue cốt lõi và mở rộng)<br/>• Bộ giải DPLL SAT Solver thuần Python (Unit Propagation, DLCS heuristic, Backtracking)<br/>• Thuật toán kiểm tra Entailment ($KB \models \alpha$) và kiểm tra tính duy nhất (Uniqueness Check)<br/>• Hệ thống kiểm thử tự động Pytest (50 unit tests, 91% code coverage) | **100%** |
| **Nguyễn Công Chiến** | • Thiết kế kiến trúc GameEngine và cô lập bảo mật qua `PublicKBInterface`<br/>• Xây dựng AI Logic Agent & Chu trình suy luận tự động (Deduction Loop)<br/>• Tính năng Smart Hint kèm trích xuất giải thích tự nhiên và thông số DPLL<br/>• Thiết kế Giao diện Web GUI (Flask REST API, Dark Theme Glassmorphism, Region Highlight)<br/>• Thực nghiệm benchmark hiệu năng trên các bộ câu đố $3\times3, 4\times4, 5\times5$ và tài liệu báo cáo | **100%** |

---

## 2: BIỂU DIỄN TRI THỨC BẰNG LOGIC MỆNH ĐỀ (PROPOSITIONAL LOGIC)

### 2.1. Quản lý Biến Mệnh đề (Variable Manager)
Để biểu diễn trạng thái của $N \times N$ ô trong lưới, hệ thống ánh xạ mỗi nhân vật $i$ sang một biến mệnh đề chính (Main Propositional Variable) $C_i$:
- $C_i = 1$ ($\text{True}$) $\iff$ Nhân vật $i$ là **CRIMINAL**.
- $\neg C_i = 1$ ($C_i = 0 / \text{False}$) $\iff$ Nhân vật $i$ là **INNOCENT**.

Việc ánh xạ biến được thực hiện một cách xác định (Deterministic Mapping) theo thứ tự từ điển của mã nhân vật (A1, A2, ..., C3).
Đối với các ràng buộc phức tạp (Cardinality, Parity), hệ thống sử dụng cơ chế cấp phát biến phụ (Auxiliary Variables) $A_k$ bắt đầu từ chỉ số $N^2 + 1$ để giữ nguyên tính chuẩn tắc CNF mà không làm bùng nổ số lượng mệnh đề con.

### 2.2. Quy tắc Chuyển đổi 8 Loại Manh mối sang CNF (CNF Encoding Rules)

Hệ thống hỗ trợ 6 loại manh mối cốt lõi và 2 loại manh mối mở rộng:

| Loại Clue | Cấu trúc Tham số | Ý nghĩa Logic | Mệnh đề CNF tương đương |
| :--- | :--- | :--- | :--- |
| **FACT** | `person`, `status` | Xác nhận trạng thái cụ thể của 1 người | $[C_i]$ (nếu CRIMINAL) hoặc $[\neg C_i]$ (nếu INNOCENT) |
| **SAME** | `person1`, `person2` | Hai người cùng trạng thái ($C_1 \leftrightarrow C_2$) | $[\neg C_1, C_2] \land [C_1, \neg C_2]$ |
| **DIFFERENT** | `person1`, `person2` | Hai người khác trạng thái ($C_1 \oplus C_2$) | $[C_1, C_2] \land [\neg C_1, \neg C_2]$ |
| **EXACTLY** | $k$, `region` | Đúng $k$ người trong vùng là CRIMINAL | $\text{AtMost}(k, V) \land \text{AtLeast}(k, V)$ |
| **AT_LEAST** | $k$, `region` | Ít nhất $k$ người trong vùng là CRIMINAL | Mọi tập con $(n - k + 1)$ biến phải có $\ge 1$ biến True |
| **AT_MOST** | $k$, `region` | Nhiều nhất $k$ người trong vùng là CRIMINAL | Mọi tập con $(k + 1)$ biến không thể đồng thời True |
| **PARITY** | `EVEN`/`ODD`, `region` | Tổng số criminal trong vùng là Chẵn / Lẻ | Chuỗi XOR qua các biến phụ $A_j$: $A_j \leftrightarrow (A_{j-1} \oplus V_j)$ |
| **BETWEEN** | `char1`, `char2`, `status` | Tất cả ô nằm giữa 2 nhân vật mang trạng thái | Unit clauses trực tiếp cho các ô trung gian trên cùng hàng/cột |

### 2.3. Mã hóa Ràng buộc Số lượng (Cardinality Encoding)
- **Combinatorial Subset Encoding (cho $n \le 10$):**
  - $\text{AtMost}(k, V)$: Với mọi tập con $S \subseteq V$ có kích thước $|S| = k + 1$, thêm mệnh đề $[\neg v_1, \neg v_2, \dots, \neg v_{k+1}]$.
  - $\text{AtLeast}(k, V)$: Với mọi tập con $S \subseteq V$ có kích thước $|S| = n - k + 1$, thêm mệnh đề $[v_1, v_2, \dots, v_{n-k+1}]$.
- **Sequential Counter Encoding (cho $n > 10$):**
  - Sử dụng ma trận biến phụ $S_{i, j}$ biểu diễn bộ đếm nhị phân lũy tiến, đảm bảo số mệnh đề sinh ra chỉ tăng tuyến tính $\mathcal{O}(n \cdot k)$ thay vì tổ hợp mũ $\mathcal{O}\binom{n}{k+1}$.

---

## 3: THUẬT TOÁN DPLL SAT SOLVER TỰ XÂY DỰNG

Thuật toán DPLL trong `griductive/logic/dpll.py` là bộ giải SAT kinh điển được tối ưu hóa cho bài toán suy luận logic:

```
Function DPLL(Clauses, Assignment, Variables):
    1. (Clauses, Assignment) = Unit_Propagation(Clauses, Assignment)
    2. If Clauses chứa Mệnh đề Rỗng (Empty Clause []):
           Return (UNSAT, None)
    3. If Clauses là Rỗng (All Clauses Satisfied):
           Return (SAT, Assignment)
    4. V = Choose_Variable_DLCS(Clauses, Variables)
    5. // Nhánh 1: Thử V = True
       (Result, Model) = DPLL(Clauses ∪ {[V]}, Assignment ∪ {V: True})
       If Result == SAT: Return (SAT, Model)
    6. // Nhánh 2: Backtrack, Thử V = False
       (Result, Model) = DPLL(Clauses ∪ {[-V]}, Assignment ∪ {V: False})
       Return (Result, Model)
```

### Các Kỹ thuật Tối ưu Chính:
1. **Unit Propagation (Lan truyền Mệnh đề Đơn vị):** Tìm các clause có kích thước 1 literal $[L]$. Gán giá trị bắt buộc cho literal đó và rút gọn công thức ngay lập tức. Quá trình này lặp lại liên tục (Fixed-point iteration) giúp loại bỏ tới 80% không gian tìm kiếm mà không cần phân nhánh.
2. **DLCS Heuristic (Dynamic Largest Combined Sum):** Chọn biến $V$ xuất hiện nhiều nhất trong cả hai chiều dương và âm ($count(V) + count(\neg V)$) trong các clause chưa được thỏa mãn. Kỹ thuật này giúp phát hiện xung đột sớm nhất có thể.
3. **Đo lường & Giám sát Hiệu năng (Telemetry):** Bộ giải thu thập đầy đủ 4 chỉ số:
   - `decisions_count`: Số lần phải đoán biến và phân nhánh.
   - `propagations_count`: Số lần lan truyền đơn vị thành công.
   - `backtracks_count`: Số lần quay lui do gặp nhánh cụt.
   - `runtime_ms`: Thời gian thực thi chính xác từng mili-giây.

---

## 4: KIẾN TRÚC HỆ THỐNG & GAME ENGINE BẢO MẬT

### 4.1. Phân tách Trách nhiệm (Separation of Concerns)
- **`GameEngine` (Trọng tài):** Nắm giữ trạng thái bí mật (`true_status`) và danh sách toàn bộ manh mối ẩn. Khi người dùng hoặc Agent gửi một verdict, Engine sẽ kiểm tra tính đúng đắn dựa trên suy diễn logic từ cơ sở tri thức công khai hiện tại.
- **`PublicKBInterface` (Giao diện Công khai):** Định nghĩa hợp đồng trừu tượng (Protocol) chỉ cho phép truy xuất:
  - `get_grid_size()`: Kích thước bàn cờ.
  - `get_public_characters()`: Danh sách nhân vật với trạng thái `revealed_status` (trạng thái `true_status` bị ẩn hoàn toàn thành `UNKNOWN`).
  - `get_revealed_clues()`: Danh sách các manh mối đã được kích hoạt/lộ ra.
  - `get_proven_verdicts()`: Lịch sử các phán quyết đã được chấp nhận.

### 4.2. Kiểm tra Kéo theo Logic (Entailment Verification)
Khi nhận một phán quyết cho nhân vật $C_i$ với trạng thái đòi hỏi $S \in \{\text{CRIMINAL}, \text{INNOCENT}\}$:
1. Engine thiết lập $KB_{public}$ hiện tại từ các manh mối đã lộ và các phán quyết đã chứng minh.
2. Kiểm tra $KB_{public} \land \neg C_i$ có **UNSAT** hay không:
   - Nếu UNSAT $\implies C_i$ bắt buộc phải là **CRIMINAL**.
3. Kiểm tra $KB_{public} \land C_i$ có **UNSAT** hay không:
   - Nếu UNSAT $\implies C_i$ bắt buộc phải là **INNOCENT**.
4. **Phân loại Kết quả (Verdict Result):**
   - **`ACCEPTED`:** Nếu trạng thái người chơi gửi trùng với trạng thái bị ép buộc bởi logic. Lúc này nhân vật được mở khóa và các manh mối mới do nhân vật nắm giữ được công khai.
   - **`CONTRADICTED`:** Nếu logic ép buộc trạng thái ngược lại.
   - **`NOT_PROVABLE`:** Nếu cả $C_i$ và $\neg C_i$ đều thỏa mãn (SAT) với $KB_{public}$ hiện tại (chưa đủ dữ liệu để kết luận).

---

## 5: AI LOGIC AGENT & CHU TRÌNH SUY LUẬN TỰ ĐỘNG

### 5.1. Chu trình Suy luận Toàn cục (Full Deduction Loop)
AI Agent hoạt động độc lập theo quy trình:
1. Quét danh sách các nhân vật chưa lộ theo thứ tự xác định hàng-cột (Row-Major: A1, B1, C1, A2...).
2. Với mỗi nhân vật, gọi hàm `classify_character(char_id)` để kiểm tra entailment.
3. Nếu tìm thấy nhân vật $C_k$ có trạng thái bị ép buộc (`CRIMINAL` hoặc `INNOCENT`):
   - Gửi verdict đến `GameEngine`.
   - Nhận về các manh mối mới được kích hoạt.
   - Cập nhật $KB_{public}$ và lặp lại bước 1.
4. Quá trình dừng lại khi toàn bộ $N \times N$ nhân vật đã được giải mã hoặc không còn nhân vật nào có thể suy diễn thêm.

### 5.2. Tạo Gợi ý Thông minh & Giải thích Tự nhiên (Hint & Explanations)
Phương thức `provide_hint()` của Agent phân tích $KB_{public}$, tìm ra nhân vật kế tiếp có thể giải được và tự động trích xuất các manh mối liên quan trực tiếp đến nhân vật đó (dựa trên tên, hàng, cột hoặc vùng lân cận), trả về:
- Nhân vật & Tọa độ gợi ý.
- Trạng thái được suy ra.
- Lời giải thích tự nhiên bằng ngôn ngữ người đọc.
- Danh sách các câu manh mối làm tiền đề.
- Thống kê chi tiết DPLL Solver.

---

## 6: THIẾT KẾ GIAO DIỆN WEB GUI & REST API

### 6.1. Kiến trúc REST API (Flask Backend)
Hệ thống cung cấp đầy đủ các endpoint chuẩn RESTful:
- `GET /`: Giao diện Web GUI chính.
- `GET /api/puzzles`: Danh sách các bài toán có sẵn kèm tiêu đề.
- `POST /api/load`: Tải câu đố từ file JSON, kiểm tra tính duy nhất (Uniqueness Check).
- `POST /api/restart`: Khởi tạo lại trạng thái ban đầu của câu đố.
- `GET /api/state`: Lấy trạng thái hiện tại của bàn cờ và các manh mối công khai.
- `POST /api/verdict`: Người chơi gửi phán quyết cho 1 nhân vật (`character_id`, `status`).
- `GET /api/hint`: Yêu cầu Agent sinh gợi ý và giải thích.
- `POST /api/auto-step`: Agent thực hiện 1 bước suy luận kế tiếp.
- `POST /api/auto-solve`: Agent chạy tự động toàn bộ chu trình suy luận đến khi hoàn thành.

### 6.2. Thiết kế Giao diện Hiện đại
- Giao diện Dark Theme cao cấp kết hợp phong cách Glassmorphism (hiệu ứng kính mờ, viền phát sáng gradient).
- Hiển thị lưới nhân vật linh hoạt theo kích thước $3\times3, 4\times4, 5\times5$.
- Tương tác thông minh: click vào manh mối bất kỳ sẽ tự động highlight vùng ô tương ứng (Region Highlight) trên bàn cờ.

---

## 7: THỰC NGHIỆM, ĐÁNH GIÁ HIỆU NĂNG & KIỂM THỬ (TEST COVERAGE)

### 7.1. Kết quả Thực nghiệm trên Bộ Dữ liệu Mẫu

| Tên Bài toán | Kích thước | Số Biến chính | Số Mệnh đề CNF | Số Bước Giải | Số Lời giải Duy nhất | Thời gian Giải (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `puzzle_01_3x3_easy.json` | $3 \times 3$ | 9 | 18 | 9 | 1 (Duy nhất) | 8.2 ms |
| `puzzle_02_3x3_hard.json` | $3 \times 3$ | 9 | 24 | 9 | 1 (Duy nhất) | 11.4 ms |
| `puzzle_03_4x4_easy.json` | $4 \times 4$ | 16 | 38 | 16 | 1 (Duy nhất) | 18.7 ms |
| `puzzle_04_4x4_medium.json`| $4 \times 4$ | 16 | 45 | 16 | 1 (Duy nhất) | 24.1 ms |
| `puzzle_05_5x5_medium.json`| $5 \times 5$ | 25 | 62 | 25 | 1 (Duy nhất) | 39.5 ms |
| `puzzle_06_5x5_expert.json`| $5 \times 5$ | 25 | 86 | 25 | 1 (Duy nhất) | 58.3 ms |
| `puzzle_07_3x3_neighbors.json`| $3 \times 3$ | 9 | 22 | 9 | 1 (Duy nhất) | 9.1 ms |

### 7.2. Đánh giá Độ bao phủ Kiểm thử (Unit Test Coverage)
Hệ thống kiểm thử tự động với `pytest` đạt **50/50 test cases PASSED** với độ bao phủ mã nguồn tổng thể **91%**:
- `test_api.py`: 17 tests kiểm tra toàn bộ REST API, status codes (200, 400, 404), các luồng dữ liệu hợp lệ và ngoại lệ.
- `test_agent.py`: 9 tests kiểm tra Agent hint, deterministic order, phân loại logic, và tính cô lập bảo mật.
- `test_engine.py`: 9 tests kiểm tra GameEngine, schema validation, restart, và kiểm định tính duy nhất.
- `test_status_cases.py`: 5 tests kiểm tra chuyên biệt các trạng thái `ACCEPTED`, `CONTRADICTED`, `NOT_PROVABLE`, `INCONSISTENT`, `UNKNOWN`.
- `test_puzzles.py`: 4 tests tự động duyệt toàn bộ file JSON trong `data/`, xác thực JSON schema, tính duy nhất và khả năng giải thành công 100%.
- `test_cnf_encoder.py`: Đối chiếu sinh $2^N$ assignments giữa CNF Encoder và Semantic Evaluator.
- `test_dpll.py`: Kiểm tra DPLL Solver trên các mô hình SAT, UNSAT và Assumptions.

---

## TÀI LIỆU THAM KHẢO
1. Stuart Russell and Peter Norvig, *Artificial Intelligence: A Modern Approach (4th Edition)*, Chapter 7: Logical Agents, Pearson, 2020.
2. Martin Davis, George Logemann, and Donald Loveland, *A Machine Program for Theorem-Proving*, Communications of the ACM, 5(7):394–397, 1962.
3. Armin Biere, Marijn Heule, Hans van Maaren, and Toby Walsh, *Handbook of Satisfiability*, IOS Press, 2009.
4. Giáo trình môn học Nhập môn Trí tuệ Nhân tạo (CSC14003), Khoa Công nghệ Thông tin, Trường Đại học Khoa học Tự nhiên - ĐHQG-HCM.
