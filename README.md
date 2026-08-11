# Griductive Solver — Logic Deduction & DPLL SAT Agent (CSC14003)

**Griductive Solver** là một dự án Python hoàn chỉnh cho môn học **Introduction to AI (CSC14003)**. Dự án kết hợp Trò chơi Suy luận Logic dạng lưới ($N \times N$, $N \in \{3,4,5\}$) cùng một **AI Logic Agent** tự động giải puzzle bằng **Mệnh đề Logic (Propositional Logic)**, **CNF Encoding tự động**, và **DPLL SAT Solver thuần Python** (không sử dụng bất kỳ thư viện SAT bên ngoài nào).

---

## 🌟 Cấu trúc Thư mục Dự án

```
project 2/
├── griductive/                    # Gói mã nguồn chính (Core Package)
│   ├── core/                      # Data Models & Quản lý Biến Mệnh đề
│   │   ├── __init__.py
│   │   ├── models.py              # Enums (Status, VerdictStatus, RegionType, ClueType), Character, ClueData
│   │   └── var_map.py             # VariableManager: Ánh xạ biến C_i và auxiliary vars một cách deterministic
│   ├── logic/                     # Toán học Logic & DPLL SAT Solver
│   │   ├── __init__.py
│   │   ├── clues.py               # Helper giải mã Region (ROW, COL, NEIGHBORS, EXPLICIT, BETWEEN)
│   │   ├── evaluators.py          # Semantic evaluators tính giá trị chân lý trực tiếp (dùng kiểm thử đối chiếu)
│   │   ├── cnf_encoder.py         # Encoder chuyển đổi tự động 8 loại clue sang CNF
│   │   └── dpll.py                # Scratch DPLL SAT Solver (Unit prop, DLCS heuristic, backtrack, stats)
│   ├── engine/                    # Game Engine & Bảo mật Dữ liệu
│   │   ├── __init__.py
│   │   ├── interfaces.py          # PublicKBInterface Protocol (Abstract Interface chuẩn)
│   │   └── game_engine.py         # GameEngine quản lý dữ liệu ẩn, kiểm tra verdict & expose public KB
│   ├── agent/                     # AI Logic Agent
│   │   ├── __init__.py
│   │   └── logic_agent.py         # LogicAgent (entailment check, deduction loop, hint, uniqueness check)
│   └── __init__.py
├── data/                          # Puzzle JSON Files & Schema
│   ├── puzzle_schema.json         # JSON Schema chuẩn hóa dữ liệu puzzle
│   ├── puzzle_3x3_easy.json       # Puzzle mẫu 3x3 mức Dễ
│   ├── puzzle_3x3_hard.json       # Puzzle mẫu 3x3 mức Khó
│   ├── puzzle_4x4_medium.json     # Puzzle mẫu 4x4 mức Trung bình
│   └── puzzle_5x5_expert.json     # Puzzle mẫu 5x5 mức Chuyên gia
├── tests/                         # Hệ thống Kiểm thử Độc lập (Unit Tests)
│   ├── test_cnf_encoder.py        # Test đối chiếu CNF Encoder với Semantic Evaluators
│   ├── test_dpll.py               # Test DPLL SAT Solver (SAT, UNSAT, Assumptions)
│   ├── test_engine.py             # Test GameEngine (Hiding secret data, verdict responses)
│   └── test_agent.py              # Test LogicAgent (Entailment classification & Deduction loop)
├── templates/                     # HTML View cho Web GUI
│   └── index.html
├── static/                        # CSS & JavaScript cho Web GUI
│   ├── style.css
│   └── app.js
├── app.py                         # Flask Server REST API & Web GUI Entry Point
├── requirements.txt               # Danh sách thư viện phụ thuộc (Flask, pytest)
└── README.md                      # Hướng dẫn chạy và tài liệu thuyết minh
```

---

## 🚀 Hướng dẫn Chạy Ứng dụng

### 1. Cài đặt Phụ thuộc
Đảm bảo đã cài đặt Python (3.9+). Cài đặt các gói phụ thuộc bằng lệnh:
```bash
py -3 -m pip install -r requirements.txt
```

### 2. Chạy Kiểm thử Unit Test
Chạy toàn bộ bộ test kiểm định thuật toán:
```bash
py -3 -m pytest -v
```

### 3. Khởi chạy Giao diện Web GUI
Chạy server ứng dụng Flask:
```bash
py -3 app.py
```
Sau đó mở trình duyệt web và truy cập: **`http://127.0.0.1:5000`**

---

## 🧠 Thuyết minh Thuật toán & Kiến trúc (Phục vụ Vấn đáp)

### 1. Tách biệt 2 Vai trò (GameEngine vs LogicAgent)
- **GameEngine**: Đóng vai trò là "Trọng tài". Nắm giữ trạng thái thật (`true_status`) và tất cả clue chưa lộ.
- **LogicAgent**: Chỉ giao tiếp qua giao diện `PublicKBInterface`. **Tuyệt đối không truy cập trực tiếp trạng thái ẩn**. 
- Khi Người chơi/Agent gửi verdict `submit_verdict(character_id, claimed_status)`:
  - GameEngine dùng lý thuyết Entailment kiểm tra trên **KB công khai hiện tại**.
  - Trả về `ACCEPTED` (nếu mệnh đề bị ép buộc), `CONTRADICTED` (nếu chiều ngược lại bị ép buộc), hoặc `NOT_PROVABLE` (chưa đủ dữ kiện).

### 2. Biến Mệnh đề (Propositional Variables)
- $C_i$ (với $i \in \{1 \dots N^2\}$): Là biến Boolean chính. $C_i = \text{True}$ nếu nhân vật $i$ là **CRIMINAL**, $C_i = \text{False}$ nếu là **INNOCENT**.
- Tên nhân vật được sắp xếp theo thứ tự bảng chữ cái để tạo variable mapping chuẩn hóa (Deterministic Mapping).
- Các biến phụ $A_k$ ($N^2 + 1, N^2 + 2, \dots$) được cấp phát tự động cho phép mã hóa CNF của các ràng buộc phức tạp (Cardinality, Parity).

### 3. 8 Loại Clue & Mã hóa CNF (CNF Encoding)
1. **FACT(person, status)**: Unit clause $C_i$ hoặc $\neg C_i$.
2. **SAME(i, j)**: $C_i \leftrightarrow C_j \equiv (\neg C_i \lor C_j) \land (C_i \lor \neg C_j)$.
3. **DIFFERENT(i, j)**: $C_i \oplus C_j \equiv (C_i \lor C_j) \land (\neg C_i \lor \neg C_j)$.
4. **EXACTLY(k, region)**: Kết hợp `AT_LEAST(k)` và `AT_MOST(k)`. Mã hóa kết hợp (Combinatorial Subset) hoặc Sequential Counter.
5. **AT_LEAST(k, region)**: Mọi tập con kích thước $n - k + 1$ phải chứa ít nhất 1 biến dương.
6. **AT_MOST(k, region)**: Mọi tập con kích thước $k + 1$ không thể cùng đúng (chứa các biến âm).
7. **PARITY(parity_type, region)** *(Extension)*: Số lượng criminal trong region là EVEN/ODD. Được mã hóa bằng chuỗi XOR qua các biến phụ.
8. **BETWEEN(char1, char2, status)** *(Extension)*: Các ô nằm giữa 2 nhân vật chỉ định (cùng hàng/cột) được gán unit clause trực tiếp.

### 4. Semantic Evaluator kiểm thử đối chiếu
Mỗi loại clue đều có hàm `evaluate_clue_semantically(...)` tính trực tiếp truth value trên một complete assignment. Bộ test `test_cnf_encoder.py` sẽ sinh ra tất cả $2^N$ assignment để kiểm tra xem mệnh đề CNF do Encoder sinh ra có khớp $100\%$ với Semantic Evaluator hay không.

### 5. Thuật toán DPLL SAT Solver tự viết
DPLL Solver được cài đặt thuần Python trong `griductive/logic/dpll.py`:
- **Unit Propagation**: Khử liên tục các unit clause ($[L]$).
- **Variable Selection Heuristic**: DLCS (Dynamic Largest Combined Sum) chọn biến xuất hiện nhiều nhất trong các clause chưa thỏa.
- **Recursive Branching + Backtracking**: Thử $V = \text{True}$, nếu UNSAT thì backtrack thử $V = \text{False}$.
- **Ghi log**: Báo cáo đầy đủ `decisions_count`, `propagations_count`, `backtracks_count`, và `runtime_ms`.

### 6. Phân loại Entailment (Entailment Classification)
Đối với nhân vật $C_i$ chưa lộ tại bước $t$:
- $KB_t \land \neg C_i$ là **UNSAT** $\rightarrow$ Kết luận $C_i$ là **CRIMINAL**.
- $KB_t \land C_i$ là **UNSAT** $\rightarrow$ Kết luận $C_i$ là **INNOCENT**.
- Cả 2 đều **SAT** $\rightarrow$ **UNKNOWN** (chưa đủ dữ kiện).
- $KB_t$ tự nó là **UNSAT** $\rightarrow$ **INCONSISTENT** (KB mâu thuẫn).

---

## 📸 Giao diện Web GUI
- **Game Board**: Hiển thị lưới $N \times N$, tọa độ $A1, B2, \dots$, thẻ nhân vật với hiệu ứng glassmorphism.
- **Verdict Click**: Người dùng click chọn nhân vật + bấm INNOCENT / CRIMINAL để thử sức suy luận.
- **Highlight Region**: Click hoặc hover chuột vào bất kỳ clue nào trong Public KB để highlight các ô thuộc region tương ứng trên bảng.
- **Hint**: Agent phân tích KB công khai và gợi ý bước đi tiếp theo kèm lý giải và thông số DPLL Solver.
- **Auto Step / Auto Solve**: Agent tự động suy luận theo deduction loop và hiển thị trace chi tiết từng bước.
