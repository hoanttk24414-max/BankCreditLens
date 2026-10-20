# BankCreditLens

**BankCreditLens** là dashboard đánh giá tương đối chất lượng tín dụng ngân hàng, nền tảng tài chính và mức độ chuyển đổi số của 5 ngân hàng thương mại Việt Nam trong năm 2025.

Mô hình sử dụng **Bank Credit–Digital Score (BCDS)** trên thang 100 điểm, kết hợp **12 chỉ tiêu tài chính – tín dụng** và **3 tiêu chí chuyển đổi số**.

> BCDS là công cụ phân tích đa tiêu chí trong phạm vi mẫu nghiên cứu, **không phải xếp hạng tín nhiệm chính thức**.

---

## Hướng dẫn tra cứu nhanh

Nếu cần kiểm tra nhanh **kết quả nghiên cứu, dữ liệu đầu vào hoặc mã nguồn tính điểm**, có thể tra cứu theo bảng sau:

| Nội dung cần xem | Vị trí trong repository | Mô tả |
|---|---|---|
| **Kết quả BCDS cuối cùng** | `output/bank_ranking_2025.csv` | FCS, Digital Score, BCDS và thứ hạng của 5 ngân hàng |
| **Điểm theo 4 nhóm tiêu chí** | `output/group_scores_2025.csv` | Chất lượng tín dụng, vốn và nguồn vốn, sinh lời và hiệu quả, chuyển đổi số |
| **Điểm chi tiết 15 tiêu chí** | `output/criterion_scores_2025.csv` | Giá trị chuẩn hóa và điểm đóng góp của từng tiêu chí |
| **Dataset tổng hợp trước khi chấm điểm** | `output/merged_dataset_2025.csv` | Dữ liệu sau khi ghép tài chính – tín dụng và chuyển đổi số |
| **Dữ liệu tài chính sạch** | `output/credit_data_clean.csv` | Bộ dữ liệu tài chính sau xử lý |
| **File Excel dữ liệu tài chính** | `output/credit_data.xlsx` | Dữ liệu tài chính và các chỉ tiêu dưới dạng Excel |
| **Thông tin cấu hình chấm điểm** | `output/scoring_metadata.json` | Trọng số, chiều tác động và metadata của mô hình |
| **Mã nguồn chấm điểm BCDS** | `scoring_model.py` | Chuẩn hóa Min–Max, áp dụng trọng số và tính BCDS |
| **Xử lý dữ liệu tài chính** | `credit_data.py` | Thu thập, làm sạch và tính 12 chỉ tiêu tài chính – tín dụng |
| **Xử lý dữ liệu chuyển đổi số** | `digital_data_equal.py` | Chuẩn hóa dữ liệu D1, D2, D3 |
| **Dataset chuyển đổi số** | `digital_dataset_equal_2025.csv` | Điểm D1–D3 của từng ngân hàng |
| **Minh chứng chuyển đổi số** | `digital_evidence_2025.csv` | Nguồn và minh chứng dùng để chấm D1–D3 |
| **Dashboard chính** | `dashboard/app.py` | File chạy giao diện Streamlit |
| **Biểu đồ dashboard** | `dashboard/charts.py` | Các biểu đồ xếp hạng, heatmap, radar và so sánh |
| **Xử lý dữ liệu cho dashboard** | `dashboard/data_adapter.py` | Đọc và chuẩn hóa dữ liệu đầu ra để hiển thị |
| **Giao diện dashboard** | `dashboard/ui_components.py`, `dashboard/styles.css` | Thành phần UI và định dạng giao diện |
| **Chạy local trên Windows** | `run_local.bat` | Double-click để khởi động dashboard local |

### Trình tự đề xuất khi kiểm tra repository

```text
README.md
   ↓
output/bank_ranking_2025.csv
   ↓
output/group_scores_2025.csv
   ↓
output/criterion_scores_2025.csv
   ↓
scoring_model.py
   ↓
credit_data.py / digital_data_equal.py
   ↓
dashboard/app.py
```

> Nếu chỉ cần xem kết quả cuối cùng, hãy mở `output/bank_ranking_2025.csv`.  
> Nếu muốn kiểm tra vì sao một ngân hàng có số điểm cụ thể, xem thêm `output/group_scores_2025.csv` và `output/criterion_scores_2025.csv`.  
> Nếu muốn kiểm tra cách tính điểm, xem `scoring_model.py`.

---

## 1. Phạm vi nghiên cứu

Các ngân hàng được đánh giá:

- Vietcombank (`VCB`)
- Techcombank (`TCB`)
- VietinBank (`CTG`)
- MBBank (`MBB`)
- BIDV (`BID`)

Kỳ đánh giá chính: **năm tài chính 2025**.

---

## 2. Cấu trúc mô hình BCDS

BCDS gồm 4 nhóm tiêu chí:

| Nhóm tiêu chí | Trọng số | Chỉ tiêu |
|---|---:|---|
| Chất lượng tín dụng | 35% | NPL, Group 2, LLR/NPL, CoR |
| Vốn và nguồn vốn | 20% | CAR, Equity/Assets, CASA, Deposits/Liabilities |
| Sinh lời và hiệu quả | 20% | ROA, ROE, NIM, CIR |
| Chuyển đổi số | 25% | D1, D2, D3 |
| **Tổng cộng** | **100%** | **15 tiêu chí** |

### D1–D3

- **D1:** Số hóa định danh và onboarding
- **D2:** Số hóa quy trình tín dụng/cho vay
- **D3:** Ứng dụng AI, Big Data và Machine Learning trong tín dụng và quản trị rủi ro

Các tiêu chí tài chính được chuẩn hóa theo phương pháp **Min–Max**.  
D1–D3 được chấm trên thang **0–3** và chuẩn hóa theo `score / 3`.

---

## 3. Kết quả BCDS 2025

| Hạng | Ngân hàng | BCDS / 100 |
|---:|---|---:|
| 1 | Vietcombank | 71.97 |
| 2 | Techcombank | 64.20 |
| 3 | VietinBank | 52.82 |
| 4 | MBBank | 51.95 |
| 5 | BIDV | 31.49 |

Điểm số mang tính **tương đối trong phạm vi 5 ngân hàng** và phụ thuộc vào mẫu so sánh, phương pháp chuẩn hóa, trọng số và chất lượng dữ liệu đầu vào.

---

## 4. Chức năng dashboard

Dashboard Streamlit gồm các trang chính:

- **Tổng quan:** xếp hạng BCDS, KPI tổng hợp và hồ sơ ngân hàng dẫn đầu.
- **So sánh ngân hàng:** heatmap điểm nhóm, tổng điểm và mức độ phân hóa.
- **Chi tiết tiêu chí:** xem giá trị gốc, điểm chuẩn hóa và điểm đóng góp của từng tiêu chí.
- **Chuyển đổi số D1–D3:** so sánh điểm số và minh chứng chuyển đổi số.
- **Nguồn dữ liệu & phương pháp:** thông tin dữ liệu, trạng thái minh chứng và phương pháp chấm điểm.

Dashboard **đọc các output đã được tạo sẵn**, không tự thay đổi dữ liệu nguồn khi người dùng chỉ mở giao diện.

---

## 5. Cấu trúc thư mục

```text
BankCreditLens/
│
├── backend.py
├── credit_data.py
├── digital_data_equal.py
├── scoring_model.py
├── digital_dataset_equal_2025.csv
├── digital_evidence_2025.csv
├── Requirements.txt
├── run_local.bat
├── README.md
│
├── dashboard/
│   ├── app.py
│   ├── charts.py
│   ├── config.py
│   ├── data_adapter.py
│   ├── ui_components.py
│   ├── styles.css
│   ├── requirements.txt
│   └── assets/
│
└── output/
    ├── bank_ranking_2025.csv
    ├── criterion_scores_2025.csv
    ├── group_scores_2025.csv
    ├── merged_dataset_2025.csv
    ├── scoring_metadata.json
    ├── credit_data_clean.csv
    └── credit_data.xlsx
```

---

## 6. Chạy local trên Windows

### Cách nhanh nhất

Sau khi clone hoặc tải project về máy:

1. Mở thư mục `BankCreditLens`.
2. Double-click file:

```text
run_local.bat
```

File này sẽ tự:

- chuyển terminal về đúng thư mục project;
- tạo `.venv` nếu chưa có;
- kiểm tra/cài các thư viện cần thiết cho dashboard;
- chạy Streamlit tại:

```text
http://localhost:8501
```

Để dừng server, nhấn `Ctrl + C` trong cửa sổ terminal.

---

## 7. Chạy local thủ công

### Bước 1 — Tạo virtual environment

PowerShell:

```powershell
py -3 -m venv .venv
```

### Bước 2 — Kích hoạt môi trường

```powershell
.\.venv\Scripts\Activate.ps1
```

Nếu PowerShell chặn script, có thể chạy trực tiếp Python trong `.venv` mà không cần activate.

### Bước 3 — Cài thư viện dashboard

```powershell
python -m pip install -r dashboard\requirements.txt
```

### Bước 4 — Chạy Streamlit

```powershell
python -m streamlit run dashboard\app.py
```

Sau đó truy cập:

```text
http://localhost:8501
```

---

## 8. Tạo lại dữ liệu và kết quả chấm điểm

Nếu chỉ muốn xem dashboard với dữ liệu đã có trong `output/`, **không cần chạy lại pipeline**.

Nếu muốn thu thập/xử lý dữ liệu lại từ đầu, cài thêm các dependency ở root:

```powershell
python -m pip install -r Requirements.txt
```

Sau đó chạy lần lượt:

```powershell
python credit_data.py
python digital_data_equal.py
python scoring_model.py
```

Cuối cùng chạy dashboard:

```powershell
python -m streamlit run dashboard\app.py
```

> Việc chạy lại pipeline có thể làm thay đổi các file trong `output/` nếu dữ liệu đầu vào hoặc nguồn dữ liệu được cập nhật.

---

## 9. Nguồn dữ liệu

Dữ liệu tài chính – tín dụng được tổng hợp từ:

- dữ liệu báo cáo tài chính có cấu trúc;
- báo cáo tài chính hợp nhất/kiểm toán;
- báo cáo thường niên;
- các công bố chính thức của ngân hàng.

Các tiêu chí chuyển đổi số D1–D3 được xây dựng từ các minh chứng công bố của từng ngân hàng và được lưu trong:

```text
digital_evidence_2025.csv
digital_dataset_equal_2025.csv
```

---

## 10. Các file output chính

### `output/bank_ranking_2025.csv`

Bảng xếp hạng cuối cùng của 5 ngân hàng theo BCDS.

### `output/criterion_scores_2025.csv`

Điểm theo từng tiêu chí, bao gồm giá trị chuẩn hóa và điểm đóng góp.

### `output/group_scores_2025.csv`

Điểm tổng hợp theo 4 nhóm tiêu chí.

### `output/merged_dataset_2025.csv`

Dataset sau khi ghép cấu phần tài chính – tín dụng và chuyển đổi số.

### `output/scoring_metadata.json`

Thông tin phương pháp, cấu hình trọng số và metadata của quá trình chấm điểm.

---

## 11. Công nghệ sử dụng

- **Python**
- **Pandas**
- **NumPy**
- **OpenPyXL**
- **Streamlit**
- **Plotly**
- **VNStock / dữ liệu báo cáo tài chính**
- **Git & GitHub**

---

## 12. Deploy bằng Streamlit Community Cloud

Thiết lập deploy:

```text
Repository: hoanttk24414-max/BankCreditLens
Branch: main
Main file path: dashboard/app.py
```

Streamlit sẽ cài các dependency từ file:

```text
dashboard/requirements.txt
```

Sau mỗi lần cập nhật code:

```bash
git add .
git commit -m "Update BankCreditLens"
git push
```

Streamlit Community Cloud sẽ nhận thay đổi từ GitHub và cập nhật ứng dụng.

---

## 13. Lưu ý phương pháp

- Min–Max làm cho điểm tài chính phụ thuộc vào phạm vi mẫu.
- Điểm `0` không có nghĩa ngân hàng không đáp ứng yêu cầu an toàn; đó là vị trí thấp nhất trong mẫu ở tiêu chí tương ứng.
- D1–D3 phản ánh mức độ đáp ứng tiêu chí dựa trên minh chứng nghiên cứu.
- Trọng số thể hiện thiết kế của mô hình BCDS, không phải hệ số tác động nhân quả.
- Kết quả không thay thế xếp hạng tín nhiệm, đánh giá thanh tra hoặc kết luận của cơ quan quản lý.

---