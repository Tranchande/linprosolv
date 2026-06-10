# plot_graph.py
import math
from fractions import Fraction
import numpy as np
import plotly.graph_objects as go

# =============================================================================
# HÀM VẼ ĐỒ THỊ 
# =============================================================================
# plot_graph.py

def plot_2d_lp(c, A, b, constraint_types, method='max', var_signs=None, result=None, path_vertices=None, var_char='x'):
    """
    Hàm vẽ đồ thị 2D nhận thêm tham số var_char để đổi tên trục động ('x' hoặc 'y')
    """
    if len(c) != 2: 
        print("Chỉ hỗ trợ đồ thị 2D (2 biến).")
        return None

    # Hàm hỗ trợ chuyển đổi
    def to_f(val):
        try:
            if isinstance(val, str) and '/' in val: return float(Fraction(val))
            return float(val)
        except: return 0.0

    H_full, g_full = [], []
    plot_lines = [] 
    
    # ==========================================
    # BƯỚC 1: TRÍCH XUẤT RÀNG BUỘC & HƯỚNG MŨI TÊN
    # ==========================================
    for i, c_type in enumerate(constraint_types):
        a1, a2 = float(A[i][0]), float(A[i][1])
        val = float(b[i])
        
        # SỬA DÒNG NÀY: Thay vì gán cứng y1, y2 -> Đổi thành var_char
        lhs = f"{a1:g}{var_char}1" + (f" + {a2:g}{var_char}2" if a2 > 0 else f" - {abs(a2):g}{var_char}2")
        op = "≤" if c_type == '<=' else ("≥" if c_type == '>=' else "=")
        label_text = f"{lhs} {op} {val:g}"
        
        if c_type == '<=': 
            H_full.append([a1, a2]); g_full.append(val)
            plot_lines.append({'a1': a1, 'a2': a2, 'val': val, 'label': label_text, 'arrow_dir': [-a1, -a2]})
        elif c_type == '>=': 
            H_full.append([-a1, -a2]); g_full.append(-val)
            plot_lines.append({'a1': a1, 'a2': a2, 'val': val, 'label': label_text, 'arrow_dir': [a1, a2]})
        else: 
            H_full.append([a1, a2]); g_full.append(val)
            H_full.append([-a1, -a2]); g_full.append(-val)
            plot_lines.append({'a1': a1, 'a2': a2, 'val': val, 'label': label_text, 'arrow_dir': None})

    if var_signs is None: var_signs = ['không âm', 'không âm']
    for j in range(2):
        sign = var_signs[j].lower().strip()
        
        # SỬA DÒNG NÀY: Động hóa nhãn điều kiện dấu của ẩn
        label_text = f"{var_char}{j+1} ≥ 0" if sign == 'không âm' else f"{var_char}{j+1} ≤ 0"
        
        a1_sign = 1.0 if j == 0 else 0.0
        a2_sign = 1.0 if j == 1 else 0.0
        
        if sign == 'không âm':
            row = [0.0, 0.0]; row[j] = -1.0
            H_full.append(row); g_full.append(0.0)
            plot_lines.append({'a1': a1_sign, 'a2': a2_sign, 'val': 0.0, 'label': label_text, 'arrow_dir': [a1_sign, a2_sign]})
        elif sign == 'không dương':
            row = [0.0, 0.0]; row[j] = 1.0
            H_full.append(row); g_full.append(0.0)
            plot_lines.append({'a1': a1_sign, 'a2': a2_sign, 'val': 0.0, 'label': label_text, 'arrow_dir': [-a1_sign, -a2_sign]})

    # ==========================================
    # BƯỚC 2: TÌM MIỀN KHẢ THI VỚI HỘP LỚN M (Đã sửa lỗi triệt tiêu sai số)
    # ==========================================
    M = 10.0
    intercepts = []
    for i in range(len(g_full)):
        for j in range(2):
            if abs(H_full[i][j]) > 1e-5:
                intercepts.append(abs(g_full[i] / H_full[i][j]))
    
    if intercepts:
        # Thay vì cộng thêm 1e6 quá lớn gây sai số float, ta dùng hệ số tỷ lệ an toàn
        M = max(intercepts) * 5.0 + 50.0 

    H_box = [[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0], [0.0, -1.0]]
    g_box = [M, M, M, M]
    
    all_H = np.vstack([H_full, H_box])
    all_g = np.concatenate([g_full, g_box])
    
    intersect_pts = []
    num_lines = len(all_g)
    for i in range(num_lines):
        for j in range(i + 1, num_lines):
            A_sys = all_H[[i, j]]
            b_sys = all_g[[i, j]]
            
            if abs(np.linalg.det(A_sys)) < 1e-7: continue
                
            pt = np.linalg.solve(A_sys, b_sys)
            # Tăng nhẹ dung sai lên 1e-3 để bao quát được toàn bộ giao điểm biên của 3 ràng buộc
            if np.all(all_H @ pt <= all_g + 1e-3):
                intersect_pts.append(pt)
                
    pts = np.unique(np.round(intersect_pts, 4), axis=0) if len(intersect_pts) > 0 else np.array([])

   # ==========================================
    # BƯỚC 3: TÍNH TOÁN KHUNG NHÌN (VIEWPORT) - Phiên bản chuẩn hóa 100% sạch lỗi
    # ==========================================
    real_pts, m_pts = [], []
    for p in pts:
        if abs(abs(p[0]) - M) < 1e-1 or abs(abs(p[1]) - M) < 1e-1:
            m_pts.append(p)
        else:
            real_pts.append(p)
            
    view_pts = list(real_pts)
    if path_vertices:
        view_pts.extend(path_vertices)
        
    if len(view_pts) > 0:
        view_pts = np.array(view_pts)
        c_x_min, c_x_max = view_pts[:, 0].min(), view_pts[:, 0].max()
        c_y_min, c_y_max = view_pts[:, 1].min(), view_pts[:, 1].max()
        
        diff_x = c_x_max - c_x_min
        diff_y = c_y_max - c_y_min
        
        pad_x = diff_x * 0.4 if diff_x > 0.5 else 0.5
        pad_y = diff_y * 0.4 if diff_y > 0.5 else 0.5
        
        xlims = [c_x_min - pad_x, c_x_max + pad_x]
        ylims = [c_y_min - pad_y, c_y_max + pad_y]
        
        if c_x_min >= 0 and xlims[0] < -0.2: xlims[0] = -0.2
        if c_y_min >= 0 and ylims[0] < -0.2: ylims[0] = -0.2
        
        for p in m_pts:
            if p[0] > c_x_max: xlims[1] = max(xlims[1], c_x_max + pad_x * 2)
            if p[0] < c_x_min: xlims[0] = min(xlims[0], c_x_min - pad_x * 2)
            if p[1] > c_y_max: ylims[1] = max(ylims[1], c_y_max + pad_y * 2)
            if p[1] < c_y_min: ylims[0] = min(ylims[0], c_y_min - pad_y * 2)
    else:
        xlims, ylims = [-1, 6], [-1, 6]

    # KHẮC PHỤC: Định nghĩa lại x_range để nuôi các hàm vẽ ở Bước 4 và Bước 5
    x_range = np.array([-M, M])
    
    # ==========================================
    # BƯỚC 4: KHỞI TẠO PLOTLY FIGURE VÀ VẼ
    # ==========================================
    fig = go.Figure()

    # 4.1 Vẽ toàn bộ đường ràng buộc và mũi tên hướng bất đẳng thức
    for idx, line in enumerate(plot_lines):
        a1, a2 = line['a1'], line['a2']
        val = line['val']
        lbl = line['label']
        arrow_dir = line['arrow_dir']
        
        # Vẽ đường thẳng kéo dài vô tận (Plotly sẽ tự động phối màu ngẫu nhiên/vòng lặp)
        if abs(a2) > 1e-5:
            y_vals = (val - a1 * x_range) / a2
            fig.add_trace(go.Scatter(x=x_range, y=y_vals, mode='lines', name=lbl, line=dict(width=1.5), opacity=0.7))
        else:
            x_val = val / a1
            fig.add_trace(go.Scatter(x=[x_val, x_val], y=[-M, M], mode='lines', name=lbl, line=dict(width=1.5), opacity=0.7))
            
        # Tính toán định vị và vẽ mũi tên hướng (Chỉ áp dụng với Bất Đẳng Thức)
        if arrow_dir is not None:
            x_min, x_max = xlims[0], xlims[1]
            y_min, y_max = ylims[0], ylims[1]
            valid_pts = []
            
            # Tìm giao điểm của đường thẳng với 4 cạnh Viewport
            if abs(a2) > 1e-5:
                y_left = (val - a1 * x_min) / a2
                if y_min - 1e-5 <= y_left <= y_max + 1e-5:
                    valid_pts.append([x_min, y_left])
                y_right = (val - a1 * x_max) / a2
                if y_min - 1e-5 <= y_right <= y_max + 1e-5:
                    valid_pts.append([x_max, y_right])
                    
            if abs(a1) > 1e-5:
                x_bottom = (val - a2 * y_min) / a1
                if x_min - 1e-5 <= x_bottom <= x_max + 1e-5:
                    valid_pts.append([x_bottom, y_min])
                x_top = (val - a2 * y_max) / a1
                if x_min - 1e-5 <= x_top <= x_max + 1e-5:
                    valid_pts.append([x_top, y_max])
            
            if len(valid_pts) > 0:
                valid_pts = np.unique(np.round(valid_pts, 5), axis=0)
            
            # CHIẾN LƯỢC PHÂN TÁN: Đẩy mũi tên về các đầu mút biên khác nhau
            if len(valid_pts) >= 2:
                # Dựa vào số dư idx % len(valid_pts) để chọn mút biên, các đường khác nhau sẽ đẩy mũi tên ra các hướng khác nhau
                p_edge = valid_pts[idx % len(valid_pts)]
                p_mid = np.mean(valid_pts, axis=0)     
                
                # Tổ hợp lồi: lùi nhẹ 7% vào trong để mũi tên không bị cắt bởi viền đồ thị
                p0 = p_edge + 0.07 * (p_mid - p_edge)
            elif len(valid_pts) == 1:
                p0 = valid_pts[0]
            else:
                x0 = (x_min + x_max) / 2
                y0 = (val - a1 * x0) / a2 if abs(a2) > 1e-5 else (y_min + y_max) / 2
                p0 = np.array([x0, y0])
            
            d_vec = np.array(arrow_dir)
            d_norm = d_vec / np.linalg.norm(d_vec)
            
            # Độ dài mũi tên hướng miền khả thi
            arrow_len = min(x_max - x_min, y_max - y_min) * 0.05
            p1 = p0 + d_norm * arrow_len
            
            # Cấu hình màu sắc dễ nhìn (Bạn có thể đổi 'dimgray' thành biến tham số nếu muốn)
            arrow_color = "dimgray" 
            
            fig.add_annotation(
                x=p1[0], y=p1[1], ax=p0[0], ay=p0[1],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=1.5,
                arrowcolor=arrow_color,
                bgcolor="rgba(0,0,0,0)", text=""
            )

    # 4.2 Tô màu miền chấp nhận được
    if len(pts) >= 3:
        center = pts.mean(axis=0)
        angles = np.arctan2(pts[:,1] - center[1], pts[:,0] - center[0])
        sorted_pts = pts[np.argsort(angles)]
        
        fig.add_trace(go.Scatter(
            x=sorted_pts[:,0].tolist() + [sorted_pts[0,0]],
            y=sorted_pts[:,1].tolist() + [sorted_pts[0,1]],
            fill="toself", fillcolor="rgba(44, 160, 44, 0.25)",
            line=dict(color="rgba(255,255,255,0)"),
            name="Miền chấp nhận được",
            hoverinfo="skip"
        ))

    # ==========================================
    # BƯỚC 5: HÀM MỤC TIÊU & ĐƯỜNG Z
    # ==========================================
    sol = result.get('solution', {}) if result else {}
    status = result.get('status', '') if result else ''
    
    c1, c2 = float(c[0]), float(c[1])
    if abs(c1) > 1e-5 or abs(c2) > 1e-5:
        grad = np.array([c1, c2])
        if method.lower() == 'min': 
            grad = -grad
        grad_norm = grad / np.linalg.norm(grad)

        if c1.is_integer() and c2.is_integer() and c1 != 0 and c2 != 0:
            V = float(math.lcm(int(abs(c1)), int(abs(c2))))
        else:
            V = abs(c1 * c2) if (c1 != 0 and c2 != 0) else max(abs(c1), abs(c2))

        if 'Tối ưu' in status or 'Vô số nghiệm' in status:
            opt_x1 = to_f(sol.get('x1', 0))
            opt_x2 = to_f(sol.get('x2', 0))
            y_opt = np.array([opt_x1, opt_x2])
            
            view_scale = min(xlims[1] - xlims[0], ylims[1] - ylims[0])
            d = 0.2 * view_scale  
            y_shifted = y_opt - d * grad_norm
            V = c1 * y_shifted[0] + c2 * y_shifted[1]
            
        if abs(c2) > 1e-5:
            y_obj = (V - c1 * x_range) / c2
            fig.add_trace(go.Scatter(x=x_range, y=y_obj, mode='lines', line=dict(color='purple', dash='dashdot', width=2), name=f"Hàm mục tiêu z = {V:.2f}"))
        else:
            fig.add_vline(x=V/c1, line=dict(color='purple', dash='dashdot', width=2), name=f"Hàm mục tiêu z = {V:.2f}")

        if abs(c2) > 1e-5:
            x0 = (xlims[0] + xlims[1]) / 2  
            y0 = (V - c1 * x0) / c2
            if y0 < ylims[0] or y0 > ylims[1]:
                y0 = (ylims[0] + ylims[1]) / 2
                x0 = (V - c2 * y0) / c1
        else:
            x0 = V / c1
            y0 = (ylims[0] + ylims[1]) / 2

        p0 = np.array([x0, y0])
        arrow_len = min(xlims[1]-xlims[0], ylims[1]-ylims[0]) * 0.1
        p1 = p0 + grad_norm * arrow_len

        fig.add_annotation(
            x=p1[0], y=p1[1], ax=p0[0], ay=p0[1],
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1.5, arrowwidth=2.0, arrowcolor="purple",
            font=dict(color="purple", size=11), bgcolor="rgba(0,0,0,0)"
        )

    # ==========================================
    # BƯỚC 6: PATH VERTICES (Đã sửa lỗi văng mũi tên)
    # ==========================================
    if path_vertices and len(path_vertices) > 1:
        path = np.array(path_vertices)
        
        # 6.1 Vẽ các chấm tròn tại các đỉnh bước lặp
        fig.add_trace(go.Scatter(
            x=path[:, 0], y=path[:, 1], mode='markers',
            marker=dict(color='blue', size=10, line=dict(color='white', width=1)),
            name='Đỉnh các bước lặp'
        ))
        
        # 6.2 Bắn mũi tên nối đỉnh - Khóa chặt standoff bằng 0 để không bị văng tâm
        for i in range(len(path) - 1):
            p_start, p_end = path[i], path[i+1]
            fig.add_annotation(
                x=p_end[0], y=p_end[1],     # Điểm ngọn mũi tên
                ax=p_start[0], ay=p_start[1], # Điểm đuôi mũi tên
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, 
                arrowhead=3,      # Kiểu mũi tên dũng mãnh
                arrowsize=1.2, 
                arrowwidth=2, 
                arrowcolor="blue",
                standoff=0,       # CRITICAL: Ngọn mũi tên chạm khít tâm chấm xanh
                startstandoff=0,  # CRITICAL: Đuôi mũi tên xuất phát từ đúng tâm chấm xanh
                text=""           # Không chứa văn bản để tránh bị đẩy lệch
            )

    # ==========================================
    # BƯỚC 7: XỬ LÝ KẾT QUẢ VÀ TRƯỜNG HỢP VÔ SỐ NGHIỆM
    # ==========================================
    if 'Vô nghiệm' in status:
        fig.add_annotation(text="MIỀN CHẤP NHẬN ĐƯỢC LÀ RỖNG", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(color="red", size=20))
    elif 'Tối ưu' in status:
        if 'Vô số nghiệm' in status:
            z_vals = np.dot(pts, np.array([c1, c2]))
            opt_val = np.max(z_vals) if method == 'max' else np.min(z_vals)
            best_pts = pts[np.abs(z_vals - opt_val) < 1e-2]
            if len(best_pts) >= 2:
                best_pts = best_pts[np.lexsort((best_pts[:,1], best_pts[:,0]))]
                fig.add_trace(go.Scatter(
                    x=best_pts[:,0], y=best_pts[:,1], mode='lines+markers',
                    line=dict(color='red', width=5), marker=dict(size=8, symbol='circle'), name='Đoạn nghiệm tối ưu'
                ))
        else:
            x1_opt, x2_opt = to_f(sol.get('x1', 0)), to_f(sol.get('x2', 0))
            fig.add_trace(go.Scatter(
                x=[x1_opt], y=[x2_opt], mode='markers',
                marker=dict(color='red', size=15, symbol='star'), name=f'Nghiệm tối ưu ({x1_opt:g}, {x2_opt:g})'
            ))

    # Cấu hình Layout tổng thể
    fig.update_layout(
        title=dict(text=f"Phương pháp hình học bài toán {method.upper()}", font=dict(size=18)),
        # SỬA DÒNG NÀY: Thay đổi tiêu đề trục xaxis và yaxis thành biến var_char động
        xaxis=dict(title=f"{var_char}1", range=xlims, showgrid=True, gridcolor='lightgray', zeroline=False),
        yaxis=dict(title=f"{var_char}2", range=ylims, showgrid=True, gridcolor='lightgray', zeroline=False, scaleanchor="x", scaleratio=1),
        plot_bgcolor='white',
        hovermode="closest",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.05)
    )

    return fig.to_html(full_html=False, include_plotlyjs='inline')