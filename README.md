# LinProSolv — Trình giải Quy hoạch Tuyến tính (LP Solver)

Ứng dụng web bằng **Flask** giúp giải và **trực quan hóa** các bài toán Quy hoạch Tuyến tính (Linear Programming). Toàn bộ tính toán dùng **phân số chính xác** (`fractions.Fraction`) nên kết quả không bị sai số làm tròn, kèm theo **lời giải từng bước** chi tiết bằng tiếng Việt.

## ✨ Tính năng

- Giải bài toán LP với mục tiêu **Max** hoặc **Min**.
- Hai phương pháp giải:
  - **Đơn hình 2 pha** (Two-Phase Simplex) theo **quy tắc Bland** (tránh xoay vòng).
  - **Đối ngẫu** (Duality) — tự động chuyển bài toán gốc sang đối ngẫu rồi giải.
- Hỗ trợ ràng buộc `≤`, `≥`, `=` và biến **không âm / không dương / tự do**.
- Nhập hệ số dạng **phân số** (ví dụ `1/2`, `-3/4`).
- **Lời giải từng bước**: in ra toàn bộ quá trình biến đổi từ vựng (dictionary) ở mỗi bước lặp.
- **Đồ thị tương tác** (Plotly) cho bài toán 2 biến: miền khả thi, các đường ràng buộc, điểm tối ưu và đường đi qua các đỉnh.
- Phân loại nghiệm: tối ưu duy nhất, vô số nghiệm, vô nghiệm, không giới nội.
- Giao diện một trang, có **chế độ sáng/tối**.

## 🛠️ Công nghệ

- **Backend:** Python, Flask
- **Tính toán:** `fractions.Fraction`, NumPy
- **Đồ thị:** Plotly (render ra HTML nhúng)
- **Giao diện:** HTML + Tailwind CSS (CDN)
- **Production server:** Gunicorn

## 🚀 Chạy ở máy (local)

> Yêu cầu: Python 3.10+ (khuyến nghị 3.12).

```bash
cd linprosolv-project
pip install -r ../requirements.txt
python app.py
```

Mở trình duyệt tại **http://127.0.0.1:2026**.

## 📂 Cấu trúc thư mục

```
.
├── linprosolv-project/
│   ├── app.py               # Điểm vào Flask, route /api/solve, đọc & kiểm tra form
│   ├── solve_two_phase.py   # Đơn hình 2 pha (Bland's rule)
│   ├── duality.py           # Chuyển đổi & giải bài toán đối ngẫu
│   ├── plot_graph.py        # Vẽ đồ thị 2D bằng Plotly
│   └── templates/
│       └── index.html       # Giao diện một trang
├── requirements.txt
├── render.yaml              # Cấu hình deploy cho Render
└── README.md
```

## 🌐 Triển khai (Deploy)

Dự án đã cấu hình sẵn cho **[Render](https://render.com)** qua file `render.yaml`:

1. Đẩy code lên GitHub.
2. Trên Render: **New → Blueprint**, chọn repo này.
3. Render tự đọc `render.yaml` và bấm **Apply**.

Lệnh chạy ở production:

```bash
gunicorn --chdir linprosolv-project app:app
```

> Lưu ý: gói **free** của Render sẽ "ngủ" sau ~15 phút không truy cập, lần mở đầu tiên sau đó mất ~30 giây để khởi động lại.

## 📖 Cách dùng

1. Chọn mục tiêu (**Max**/**Min**) và **phương pháp giải**.
2. Nhập số biến, số ràng buộc.
3. Điền hệ số hàm mục tiêu, ma trận ràng buộc, vế phải và dấu của từng biến.
4. Bấm **Giải** → xem kết quả, các bước giải và đồ thị (nếu là 2 biến).

---

*Giao diện và toàn bộ output bằng tiếng Việt.*
