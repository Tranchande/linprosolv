import copy
import matplotlib
matplotlib.use('Agg') 
import numpy as np
from fractions import Fraction
import plotly.graph_objects as go
import math

def convert_to_dual(c, A, b, constraint_types, method, var_signs):
    # 1. Đảo chiều tối ưu
    dual_method = 'min' if method.lower() == 'max' else 'max'
    
    # 2. Hoán vị tham số
    dual_c = b.copy()
    dual_b = c.copy()
    num_primal_vars = len(A[0])
    num_primal_constraints = len(A)
    dual_A = [[A[i][j] for i in range(num_primal_constraints)] for j in range(num_primal_vars)]
    
    # 3. Ánh xạ Ràng buộc gốc -> Dấu của biến đối ngẫu
    dual_var_signs = []
    for ct in constraint_types:
        if method.lower() == 'max':
            if ct == '<=': dual_var_signs.append('không âm')
            elif ct == '>=': dual_var_signs.append('không dương')
            elif ct == '=':  dual_var_signs.append('tự do')
        else: # Bài toán gốc là Min
            if ct == '>=': dual_var_signs.append('không âm')
            elif ct == '<=': dual_var_signs.append('không dương')
            elif ct == '=':  dual_var_signs.append('tự do')
            
    # 4. Ánh xạ Dấu của biến gốc -> Ràng buộc đối ngẫu
    dual_constraint_types = []
    for vs in var_signs:
        if method.lower() == 'max':
            if vs == 'không âm':   dual_constraint_types.append('>=')
            elif vs == 'không dương': dual_constraint_types.append('<=')
            elif vs == 'tự do': dual_constraint_types.append('=')
        else: # Bài toán gốc là Min
            if vs == 'không âm':   dual_constraint_types.append('<=')
            elif vs == 'không dương': dual_constraint_types.append('>=')
            elif vs == 'tự do': dual_constraint_types.append('=')
            
    return dual_c, dual_A, dual_b, dual_constraint_types, dual_method, dual_var_signs

def print_dual_problem(dual_c, dual_A, dual_b, dual_constraint_types, dual_method, dual_var_signs):
    print("\n" + "="*40)
    print("      BÀI TOÁN ĐỐI NGẪU ĐÃ CHUYỂN ĐỔI")
    print("="*40)
    
    # 1. Hàm mục tiêu
    method_str = "Tối đa hóa (Max)" if dual_method == 'max' else "Tối thiểu hóa (Min)"
    print(f"Mục tiêu: {method_str} Z_dual = ", end="")
    terms = [f"{dual_c[j]}*y{j+1}" for j in range(len(dual_c))]
    print(" + ".join(terms))
    
    # 2. Ràng buộc
    print("\nVới các ràng buộc:")
    for i in range(len(dual_b)):
        row = [f"{dual_A[i][j]}*y{j+1}" for j in range(len(dual_c))]
        print(f"  {" + ".join(row)} {dual_constraint_types[i]} {dual_b[i]}")
        
    # 3. Dấu của biến
    print("\nĐiều kiện biến:")
    for j, sign in enumerate(dual_var_signs):
        print(f"  y{j+1} là {sign}")
    print("="*40 + "\n")

# =============================================================================
# HÀM VẼ ĐỒ THỊ 
# =============================================================================
def plot_dual_lp(c, A, b, constraint_types, method='max', var_signs=None, result=None, path_vertices=None):
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
    plot_lines = [] # Danh sách đồng bộ để quản lý việc vẽ đường thẳng và mũi tên hướng
    
    # ==========================================
    # BƯỚC 1: TRÍCH XUẤT RÀNG BUỘC & HƯỚNG MŨI TÊN
    # ==========================================
    for i, c_type in enumerate(constraint_types):
        a1, a2 = float(A[i][0]), float(A[i][1])
        val = float(b[i])
        lhs = f"{a1:g}y1" + (f" + {a2:g}y2" if a2 > 0 else f" - {abs(a2):g}y2")
        op = "≤" if c_type == '<=' else ("≥" if c_type == '>=' else "=")
        label_text = f"{lhs} {op} {val:g}"
        
        if c_type == '<=': 
            H_full.append([a1, a2]); g_full.append(val)
            # Với a1*y1 + a2*y2 <= val, hướng chấp nhận được ngược với vector [a1, a2]
            plot_lines.append({'a1': a1, 'a2': a2, 'val': val, 'label': label_text, 'arrow_dir': [-a1, -a2]})
        elif c_type == '>=': 
            H_full.append([-a1, -a2]); g_full.append(-val)
            # Với a1*y1 + a2*y2 >= val, hướng chấp nhận được cùng chiều vector [a1, a2]
            plot_lines.append({'a1': a1, 'a2': a2, 'val': val, 'label': label_text, 'arrow_dir': [a1, a2]})
        else: 
            H_full.append([a1, a2]); g_full.append(val)
            H_full.append([-a1, -a2]); g_full.append(-val)
            # Phương trình dấu "=" không có mũi tên hướng miền nghiệm
            plot_lines.append({'a1': a1, 'a2': a2, 'val': val, 'label': label_text, 'arrow_dir': None})

    if var_signs is None: var_signs = ['không âm', 'không âm']
    for j in range(2):
        sign = var_signs[j].lower().strip()
        label_text = f"y{j+1} ≥ 0" if sign == 'không âm' else f"y{j+1} ≤ 0"
        
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
    # BƯỚC 2: TÌM MIỀN KHẢ THI VỚI HỘP LỚN M
    # ==========================================
    M = 10.0
    intercepts = []
    for i in range(len(g_full)):
        for j in range(2):
            if abs(H_full[i][j]) > 1e-5:
                intercepts.append(abs(g_full[i] / H_full[i][j]))
    
    if intercepts:
        M = max(intercepts) * 5.0 + 1e6 

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
            if np.all(all_H @ pt <= all_g + 1e-5):
                intersect_pts.append(pt)
                
    pts = np.unique(np.round(intersect_pts, 4), axis=0) if len(intersect_pts) > 0 else np.array([])

    # ==========================================
    # BƯỚC 3: TÍNH TOÁN KHUNG NHÌN (VIEWPORT)
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
        
        pad_x = max((c_x_max - c_x_min) * 0.3, 5.0)
        pad_y = max((c_y_max - c_y_min) * 0.3, 5.0)
        
        xlims = [c_x_min - pad_x, c_x_max + pad_x]
        ylims = [c_y_min - pad_y, c_y_max + pad_y]
        
        for p in m_pts:
            if p[0] > c_x_max: xlims[1] = max(xlims[1], c_x_max + pad_x * 2)
            if p[0] < c_x_min: xlims[0] = min(xlims[0], c_x_min - pad_x * 2)
            if p[1] > c_y_max: ylims[1] = max(ylims[1], c_y_max + pad_y * 2)
            if p[1] < c_y_min: ylims[0] = min(ylims[0], c_y_min - pad_y * 2)
    else:
        xlims, ylims = [-10, 10], [-10, 10]

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
            opt_x1 = to_f(sol.get('y1', 0))
            opt_x2 = to_f(sol.get('y2', 0))
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
    # BƯỚC 6: PATH VERTICES
    # ==========================================
    if path_vertices and len(path_vertices) > 1:
        path = np.array(path_vertices)
        fig.add_trace(go.Scatter(
            x=path[:, 0], y=path[:, 1], mode='markers',
            marker=dict(color='blue', size=10, line=dict(color='white', width=1)),
            name='Đỉnh các bước lặp'
        ))
        for i in range(len(path) - 1):
            p_start, p_end = path[i], path[i+1]
            fig.add_annotation(
                x=p_end[0], y=p_end[1], ax=p_start[0], ay=p_start[1],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=3, arrowsize=1.2, arrowwidth=2, arrowcolor="blue"
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
            x1_opt, x2_opt = to_f(sol.get('y1', 0)), to_f(sol.get('y2', 0))
            fig.add_trace(go.Scatter(
                x=[x1_opt], y=[x2_opt], mode='markers',
                marker=dict(color='red', size=15, symbol='star'), name=f'Nghiệm tối ưu ({x1_opt:g}, {x2_opt:g})'
            ))

    # Cấu hình Layout tổng thể
    fig.update_layout(
        title=dict(text=f"Phương pháp hình học bài toán {method.upper()}", font=dict(size=18)),
        # KHẮC PHỤC: Sử dụng zeroline=False để xóa sạch các trục x=0, y=0 hệ thống mặc định
        xaxis=dict(title="y1", range=xlims, showgrid=True, gridcolor='lightgray', zeroline=False),
        yaxis=dict(title="y2", range=ylims, showgrid=True, gridcolor='lightgray', zeroline=False, scaleanchor="x", scaleratio=1),
        plot_bgcolor='white',
        hovermode="closest",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.05)
    )

       # Trả về HTML string để nhúng vào web, không ghi file
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

# ==========================================
# In từ vựng ra màn hình
# ==========================================
def print_dictionary(N, B, b_dict, C, v, obj, phase_name, step, n_vars, entering=None, leaving=None, var_char='y'):
    """
    Trích xuất và in Từ vựng tại mỗi bước lặp.
    - n_vars: Số lượng biến quyết định ban đầu để map tên biến (x_i hay w_i).
    """
    def format_frac(f):
        if f == float('inf'): return "dương vô cùng"
        if f == float('-inf'): return "âm vô cùng"
        return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"
        
    def var_name(idx):
        if idx == 0: return "x0"
        if 1 <= idx <= n_vars: return f"{var_char}{idx}"
        return f"w{idx - n_vars}" # Các biến bù có chỉ số > n_vars

    print(f"\n[{phase_name}] - BƯỚC LẶP {step}:")
    print(f" - Biến không cơ sở (N): {', '.join(var_name(j) for j in N)}")
    print(f" - Biến cơ sở (B): {', '.join(var_name(i) for i in B)}")
    print(" - TỪ VỰNG:")
    
    # In hàm mục tiêu (W cho Pha 1, Z cho Pha 2)
    obj_name = "epsilon" if "PHA 1" in phase_name else "Z"
    obj_str = f"   {obj_name} = {format_frac(-v[0])}"
    for j in N:
        coef = obj[j]
        if coef != 0:
            # Sửa lại logic xét dấu: dương in "+", âm in "-"
            sign = "-" if coef > 0 else "+"
            obj_str += f" {sign} {format_frac(abs(coef))}{var_name(j)}"
    print(obj_str)

    # In các phương trình biến cơ sở
    for i in B:
        eq_str = f"   {var_name(i)} = {format_frac(b_dict[i])}"
        for j in N:
            coef = C[i][j]
            if coef != 0:
                sign = "+" if coef > 0 else "-"
                eq_str += f" {sign} {format_frac(abs(coef))}{var_name(j)}"
        print(eq_str)
        
    if entering is not None and leaving is not None:
        print(f" => Biến vào: {var_name(entering)} | Biến ra: {var_name(leaving)}")
    elif entering is None:
        print(" => Không có biến vào hợp lệ. Đạt trạng thái tối ưu tại đỉnh này.")
    elif leaving is None:
        print(f" => Biến vào: {var_name(entering)} | KHÔNG CÓ BIẾN RA -> Không giới nội!")
    print("-" * 50)

# ==========================================
# CHUẨN HÓA BÀI TOÁN
# ==========================================
def standardize_problem(c, A, b, constraint_types, method, var_signs=None):
    """
    Chuẩn hóa các ràng buộc về dạng Ax <= b.
    Xử lý dấu của biến và in chú thích đổi biến chi tiết trước khi giải.
    """
    n_orig = len(c)
    m = len(b)
    
    if var_signs is None:
        var_signs = ['không âm'] * n_orig

    print("=== CHÚ THÍCH ĐỔI BIẾN TRƯỚC KHI BẮT ĐẦU GIẢI ===")
    
    # 1. Quét toàn bộ dấu của biến để quyết định ký hiệu (x hay y)
    all_non_negative = all(sign.lower().strip() == 'không âm' for sign in var_signs)
    var_char = 'y' if all_non_negative else 'u'
    
    if all_non_negative:
        print(" - Tất cả các biến đều không âm, không cần đổi tên biến (giữ nguyên hệ ban đầu).")
    
    mapped_c = []
    mapped_A_cols = [[] for _ in range(m)]
    var_mapping = {}
    
    new_var_idx = 1
    for j in range(n_orig):
        sign = var_signs[j].lower().strip()
        col_A = [A[i][j] for i in range(m)]
        orig_name = f"y{j+1}"
        
        if sign == 'không âm':
            # Chỉ in chi tiết nếu hệ bị ép phải dùng biến 'y'
            if not all_non_negative:
                print(f" - Biến {orig_name} là 'không âm': Đặt {var_char}{new_var_idx} = {orig_name} với {var_char}{new_var_idx} >= 0")
            
            mapped_c.append(c[j])
            for i in range(m): mapped_A_cols[i].append(col_A[i])
            var_mapping[j+1] = {'type': '>=0', 'vars': [new_var_idx]}
            new_var_idx += 1
            
        elif sign == 'không dương':
            print(f" - Biến {orig_name} là 'không dương': Đặt {var_char}{new_var_idx} = -{orig_name} với {var_char}{new_var_idx} >= 0 (Thay thế {orig_name} = -{var_char}{new_var_idx})")
            
            mapped_c.append(-c[j])
            for i in range(m): mapped_A_cols[i].append(-col_A[i])
            var_mapping[j+1] = {'type': '<=0', 'vars': [new_var_idx]}
            new_var_idx += 1
            
        elif sign == 'tự do':
            print(f" - Biến {orig_name} là 'tự do': Đặt {orig_name} = {var_char}{new_var_idx} - {var_char}{new_var_idx+1} với {var_char}{new_var_idx}, {var_char}{new_var_idx+1} >= 0")
            
            mapped_c.append(c[j])
            mapped_c.append(-c[j])
            for i in range(m): 
                mapped_A_cols[i].append(col_A[i])
                mapped_A_cols[i].append(-col_A[i])
            var_mapping[j+1] = {'type': 'free', 'vars': [new_var_idx, new_var_idx + 1]}
            new_var_idx += 2
    print("================================================\n")

    # Chuẩn hóa ràng buộc (Hàng)
    new_A = []
    new_b = []
    for i, c_type in enumerate(constraint_types):
        row = [Fraction(x) for x in mapped_A_cols[i]]
        val = Fraction(b[i])
        
        if c_type == '<=':
            new_A.append(row)
            new_b.append(val)
        elif c_type == '>=':
            new_A.append([-x for x in row])
            new_b.append(-val)
        elif c_type == '=':
            new_A.append(row)
            new_b.append(val)
            new_A.append([-x for x in row])
            new_b.append(-val)

    obj_c = []
    for coef in mapped_c:
        val = Fraction(coef)
        obj_c.append(-val if method == 'min' else val)
        
    return obj_c, new_A, new_b, var_mapping, var_char

# ==========================================
# KHỞI TẠO TỪ VỰNG (DICTIONARY)
# ==========================================
def build_initial_dictionary(c, A, b):
    """
    Tạo cấu trúc từ vựng: x_B = b + C * x_N.
    Biến v (hằng số hàm mục tiêu) được bọc trong list [Fraction(0)] để cấp quyền thay đổi (mutable).
    """
    n = len(c)
    m = len(b)
    
    N = list(range(1, n + 1))
    B = list(range(n + 1, n + m + 1))
    
    b_dict = {B[i]: b[i] for i in range(m)}
    C = {B[i]: {N[j]: -A[i][j] for j in range(n)} for i in range(m)}
    
    v = [Fraction(0)]  # Sửa lỗi: Dùng list để truyền tham chiếu
    obj = {N[j]: c[j] for j in range(n)}
    
    return N, B, b_dict, C, v, obj


# ==========================================
# THAO TÁC XOAY CƠ SỞ (PIVOT)
# ==========================================
def pivot(N, B, b_dict, C, v, obj, entering, leaving):
    """
    Thực hiện phép xoay biến: rút biến entering thế vào các phương trình khác.
    """
    C_le = C[leaving][entering]
    
    # Rút biến entering từ phương trình dòng leaving
    new_b_e = -b_dict[leaving] / C_le
    new_C_e = {leaving: Fraction(1) / C_le}
    for j in N:
        if j != entering:
            new_C_e[j] = -C[leaving][j] / C_le
            
    # Thế phương trình mới vào các dòng cơ sở còn lại
    for i in B:
        if i != leaving:
            C_ie = C[i][entering]
            b_dict[i] += C_ie * new_b_e
            C[i][leaving] = C_ie * new_C_e[leaving]
            for j in N:
                if j != entering:
                    C[i][j] += C_ie * new_C_e[j]
            del C[i][entering]
            
    # Thế vào biểu thức hàm mục tiêu hiện tại (Cập nhật trực tiếp vào v[0])
    obj_e = obj[entering]
    v[0] += obj_e * new_b_e  
    obj[leaving] = obj_e * new_C_e[leaving]
    for j in N:
        if j != entering:
            obj[j] += obj_e * new_C_e[j]
    del obj[entering]
    
    # Cập nhật lại cấu trúc Từ vựng và sắp xếp chỉ số theo luật Bland
    b_dict[entering] = new_b_e
    C[entering] = new_C_e
    del b_dict[leaving]
    del C[leaving]
    
    N.remove(entering)
    N.append(leaving)
    N.sort()  # Luật Bland yêu cầu sắp xếp lại chỉ số
    
    B.remove(leaving)
    B.append(entering)
    B.sort()


# ==========================================
# THUẬT TOÁN XOAY ĐƠN HÌNH BLAND
# ==========================================
def simplex_bland(N, B, b_dict, C, v, obj, phase_name, n_vars, var_char='x', start_step=0, path_callback=None):
    """
    Chạy thuật toán Simplex tuân thủ tuyệt đối quy tắc Bland.
    Đã tích hợp hook để trích xuất quá trình biến đổi Từ vựng.
    """
    step = start_step
    while True:
        entering = None
        # Luật Bland 1: Chọn biến tự do có hệ số dương với chỉ số nhỏ nhất
        for j in N:
            if obj[j] > 0:
                entering = j
                break
                
        # Dừng nếu đã đạt phương án tối ưu
        if entering is None:
            print_dictionary(N, B, b_dict, C, v, obj, phase_name, step, n_vars, entering=None, leaving="Tối ưu", var_char=var_char)
            if path_callback: path_callback()
            return 'Tối ưu'
            
        leaving = None
        min_ratio = None
        
        # Luật Bland 2: Duyệt tỷ số, ưu tiên biến cơ sở bị chặn sớm nhất
        for i in B:
            if C[i][entering] < 0:
                ratio = b_dict[i] / (-C[i][entering])
                if min_ratio is None or ratio < min_ratio:
                    min_ratio = ratio
                    leaving = i
                    
        # Dừng nếu miền bị mở rộng ra vô cực
        if leaving is None:
            print_dictionary(N, B, b_dict, C, v, obj, phase_name, step, n_vars, entering, None, var_char=var_char)
            if path_callback: path_callback()
            return 'Không giới nội'
            
        # In từ vựng trước khi thực hiện bước xoay
        print_dictionary(N, B, b_dict, C, v, obj, phase_name, step, n_vars, entering, leaving, var_char=var_char)
        
        # Dịch chuyển sang đỉnh kề
        pivot(N, B, b_dict, C, v, obj, entering, leaving)
        if path_callback: path_callback()
        step += 1

# ==========================================
# XOAY HAI PHA CHO BÀI TOÁN ĐỐI NGẪU
# ==========================================

def solve_duality(c, A, b, constraint_types, method='max', var_signs=None):
    dual_c, dual_A, dual_b, dual_constraint_types, dual_method, dual_var_signs = convert_to_dual(c, A, b, constraint_types, method, var_signs)

    print_dual_problem(dual_c, dual_A, dual_b, dual_constraint_types, dual_method, dual_var_signs)
    # Khởi tạo danh sách lưu hành trình
    path_vertices = []
    n_orig = len(dual_c)

    std_c, std_A, std_b, var_mapping, var_char = standardize_problem(dual_c, dual_A, dual_b, dual_constraint_types, dual_method, dual_var_signs)
    N, B, b_dict, C, v, obj = build_initial_dictionary(std_c, std_A, std_b)

    def get_current_point(b_dict, var_mapping):
        pt = [0.0] * n_orig
        for j in range(1, n_orig + 1):
            v_info = var_mapping[j]
            val = Fraction(0)
            if v_info['type'] == '>=0': val = b_dict.get(v_info['vars'][0], Fraction(0))
            elif v_info['type'] == '<=0': val = -b_dict.get(v_info['vars'][0], Fraction(0))
            elif v_info['type'] == 'free': val = b_dict.get(v_info['vars'][0], Fraction(0)) - b_dict.get(v_info['vars'][1], Fraction(0))
            pt[j-1] = float(val)
        return tuple(pt)

    # Callback lưu trạng thái
    def update_path():
        path_vertices.append(get_current_point(b_dict, var_mapping))

    def format_frac(f):
        if f == float('inf'): return "dương vô cùng"
        if f == float('-inf'): return "âm vô cùng"
        return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"

    n_vars = len(std_c) 
    update_path()

    # ==========================================
    # KHỞI TẠO PHA 1 CHO BÀI TOÁN ĐỐI NGẪU
    # ==========================================
    if any(b_dict[i] < 0 for i in B):
        N.insert(0, 0)
        for i in B:
            C[i][0] = Fraction(1)
            
        orig_obj = copy.deepcopy(obj)
        orig_v = v[0]
        
        obj = {j: Fraction(0) for j in N}
        obj[0] = Fraction(-1)
        v[0] = Fraction(0)
        
        leaving = min(B, key=lambda i: b_dict[i])
        print_dictionary(N, B, b_dict, C, v, obj, "PHA 1 (Khởi tạo bổ trợ)", 0, n_vars, entering=0, leaving=leaving, var_char=var_char)
        pivot(N, B, b_dict, C, v, obj, 0, leaving)
        update_path()
        
        simplex_bland(N, B, b_dict, C, v, obj, "PHA 1", n_vars, start_step=1, path_callback=update_path, var_char=var_char)
        
        x0_val = b_dict[0] if 0 in B else Fraction(0)
        print(f"\n=== KẾT THÚC PHA 1 ===")
        print(f" -> Giá trị của biến giả x0 = {format_frac(x0_val)}")
        
        if x0_val != 0:
            print(" -> Vì x0 khác 0, kết luận bài toán ĐỐI NGẪU VÔ NGHIỆM.")
            status = 'Vô nghiệm'
        else:
            print(" -> Vì x0 = 0, bài toán có nghiệm. Tiến hành chuyển sang Pha 2.")
            status = 'Khả thi'
            
        if status == 'Khả thi' and 0 in B:
            for j in N:
                if C[0][j] != 0:
                    print_dictionary(N, B, b_dict, C, v, obj, "PHA 1 (Đẩy x0 khỏi cơ sở)", "Phụ", n_vars, entering=j, leaving=0, var_char=var_char)
                    pivot(N, B, b_dict, C, v, obj, j, 0)
                    update_path()
                    break
                    
        if status == 'Khả thi' and 0 in N:
            N.remove(0)
            for i in B:
                del C[i][0]
                
        if status == 'Khả thi':
            v_new = orig_v
            obj_new = {j: Fraction(0) for j in N}
            for j in orig_obj:
                if j in N:
                    obj_new[j] += orig_obj[j]
                else:
                    v_new += orig_obj[j] * b_dict[j]
                    for k in N:
                        obj_new[k] += orig_obj[j] * C[j][k]
                        
            v[0] = v_new
            obj = obj_new
    else:
        print("\n=== BỎ QUA PHA 1 ===")
        print(" -> Mọi b_i >= 0, hệ ban đầu khả thi (x0 mặc định bằng 0). Chuyển thẳng sang Pha 2.")
        status = 'Khả thi'

    # ==========================================
    # KÍCH HOẠT PHA 2 CHO BÀI TOÁN ĐỐI NGẪU
    # ==========================================
    if status != 'Vô nghiệm':
        status = simplex_bland(N, B, b_dict, C, v, obj, "PHA 2", n_vars, start_step=0, path_callback=update_path, var_char=var_char)
    current_sol_dict = {}
    if status == 'Vô nghiệm':
        z_display = "âm vô cùng" if method == 'max' else "dương vô cùng"
        solution = {}
        print("\n=== KẾT LUẬN ===")
        print(f"Trạng thái: Vô nghiệm | Z = {z_display}")
    elif status == 'Không giới nội':
        z_display = "dương vô cùng" if method == 'max' else "âm vô cùng"
        solution = {}
        print("\n=== KẾT LUẬN ===")
        print(f"Trạng thái: Không giới nội | Z = {z_display}")
    else:
        z_val = -v[0] if method == 'min' else v[0]
        z_display = format_frac(z_val)
        
        print("\n=== TRẠNG THÁI HỆ BIẾN ĐỔI TẠI TỪ VỰNG TỐI ƯU ===")
        final_phase_vars = [f"{var_char}{j} = {format_frac(b_dict.get(j, Fraction(0)))}" for j in range(1, n_vars + 1)]
        print(" - Các biến chuẩn hóa: " + ", ".join(final_phase_vars))
        final_slack_vars = [f"w{i} = {format_frac(b_dict.get(n_vars + i, Fraction(0)))}" for i in range(1, len(std_b) + 1)]
        print(" - Các biến bù (Slack): " + ", ".join(final_slack_vars))
        print(f" - Giá trị hàm mục tiêu tối ưu (W/Z): {format_frac(v[0])}")

        fake_zero_vars = set()
        for v_info in var_mapping.values():
            if v_info['type'] == 'free':
                pos_var, neg_var = v_info['vars']
                if pos_var in B and neg_var in N:
                    fake_zero_vars.add(neg_var)
                elif neg_var in B and pos_var in N:
                    fake_zero_vars.add(pos_var)

        zero_obj_vars = [j for j in N if obj[j] == 0 and j not in fake_zero_vars]
        print("\n=== KẾT LUẬN BÀI TOÁN ĐỐI NGẪU ===")
        

        # Hàm bổ trợ lấy giá trị hiện tại của biến trong từ vựng
        def get_val(idx):
            return b_dict[idx] if idx in B else Fraction(0)

        # Định nghĩa hàm đặt tên biến nhất quán với biến trạng thái var_char
        def var_name(idx):
            if idx == 0: return "x0"
            if 1 <= idx <= n_vars: return f"y{idx}"
            return f"w{idx - n_vars}"

        # TRÍCH XUẤT NGHIỆM GỐC KHÔNG BỊ LỆCH CHỈ SỐ
        for orig_idx, v_info in var_mapping.items():
            display_idx = orig_idx if (isinstance(orig_idx, int) and orig_idx > 0) else orig_idx + 1
            
            if v_info['type'] == '>=0':
                val = get_val(v_info['vars'][0])
            elif v_info['type'] == '<=0':
                val = -get_val(v_info['vars'][0])
            elif v_info['type'] == 'free':
                val = get_val(v_info['vars'][0]) - get_val(v_info['vars'][1])
            
            val_str = format_frac(val)
            current_sol_dict[f'x{display_idx}'] = val_str  
            current_sol_dict[f'y{display_idx}'] = val_str  
        
        # PHÂN NHÁNH TRẠNG THÁI TỐI ƯU
        if zero_obj_vars:
            status = 'Tối ưu (Vô số nghiệm)'
            solution = current_sol_dict 
            
            print(f"Trạng thái: BÀI TOÁN CÓ VÔ SỐ NGHIỆM (ALTERNATIVE OPTIMA)")
            print(f" => Giá trị tối ưu Z = {z_display}")
            
            for k, v_str in solution.items():
                if k.startswith('y'): 
                    print(f" - Một điểm cực biên tối ưu: {k} = {v_str}")
                
            zero_names = [var_name(j) for j in zero_obj_vars]
            print(f"\nTồn tại các biến không cơ sở {', '.join(zero_names)} có hệ số hàm mục tiêu bằng 0.")
            print(f"Do đó, đa diện nghiệm chứa một tập lồi (cạnh/mặt) mà tại đó Z không đổi.")
            print("Miền nghiệm tổng quát (trên không gian chuẩn hóa) được định nghĩa bởi hệ:")
            
            for i in B:
                eq_str = f"{var_name(i)} = {format_frac(b_dict[i])}"
                for j in zero_obj_vars:
                    coef = C[i][j]
                    if coef != 0:
                        sign = "+" if coef > 0 else "-"
                        eq_str += f" {sign} {format_frac(abs(coef))}*{var_name(j)}"
                print(f"    {eq_str}  (điều kiện: >= 0)")
            print(f"Điều kiện tham số: {', '.join([f'{name} >= 0' for name in zero_names])}")
            print("(Tất cả các biến không cơ sở khác bị gán chặt bằng 0)")

        else:
            status = 'Tối ưu (Nghiệm duy nhất)'
            solution = current_sol_dict
            
            print(f"Trạng thái: Tối ưu (Nghiệm duy nhất)")
            for k, v_str in solution.items():
                if k.startswith('y'): 
                    print(f" - Điểm cực biên tối ưu: {k} = {v_str}")
            print(f" => Giá trị tối ưu Z = {z_display}")

    # Tạo dual_result_dict (đã có current_sol_dict ở cả 3 nhánh)
    dual_result_dict = {
        'status': status, 
        'z': format_frac(v[0]) if status not in ['Vô nghiệm', 'Không giới nội'] else z_display, 
        'solution': current_sol_dict
    }
    # =========================================================================
    # ÁP DỤNG CÁC ĐỊNH LÝ ĐỐI NGẪU VÀ ĐỘ LỆCH BÙ ĐỂ KẾT LUẬN BÀI TOÁN GỐC
    # =========================================================================
    print("ÁP DỤNG ĐỊNH LÝ ĐỐI NGẪU BIỆN LUẬN BÀI TOÁN GỐC")
    
    primal_status = ""
    primal_z_display = ""
    primal_solution = {}
    
    if status == 'Vô nghiệm':
        print("Trạng thái đối ngẫu: VÔ NGHIỆM")
        print("Theo Định lý đối ngẫu: Khi bài toán đối ngẫu vô nghiệm, bài toán gốc KHÔNG GIỚI NỘI.")
        primal_status = "Không giới nội"
        primal_z_display = "dương vô cùng" if method == 'max' else "âm vô cùng"
        
    elif status == 'Không giới nội':
        print("Trạng thái đối ngẫu: KHÔNG GIỚI NỘI")
        print("Theo Định lý đối ngẫu mạnh: Vì bài toán đối ngẫu KHÔNG GIỚI NỘI, bài toán gốc VÔ NGHIỆM.")
        primal_status = "Vô nghiệm"
        primal_z_display = "âm vô cùng" if method == 'max' else "dương vô cùng"
        
    else: 
        print("Trạng thái đối ngẫu: TỐI ƯU (HỮU HẠN)")
        dual_z_val = -v[0] if dual_method == 'min' else v[0]
        primal_z_val = dual_z_val
        primal_z_display = format_frac(primal_z_val)
        print(f"Theo Định lý đối ngẫu mạnh: Giá trị tối ưu Bài toán gốc trùng Bài toán đối ngẫu = {primal_z_display}")
        
        # Trích xuất vector nghiệm tối ưu đối ngẫu y* dưới dạng Fraction chính xác
        y_opt = []
        for j in range(1, n_orig + 1):
            v_info = var_mapping[j]
            val = Fraction(0)
            if v_info['type'] == '>=0': val = b_dict.get(v_info['vars'][0], Fraction(0))
            elif v_info['type'] == '<=0': val = -b_dict.get(v_info['vars'][0], Fraction(0))
            elif v_info['type'] == 'free': val = b_dict.get(v_info['vars'][0], Fraction(0)) - b_dict.get(v_info['vars'][1], Fraction(0))
            y_opt.append(val)
        print(" -> Nghiệm tối ưu đối ngẫu y* =", [format_frac(y) for y in y_opt])
        
        # =====================================================================
        # KIỂM TRA TÍNH DUY NHẤT CỦA NGHIỆM ĐỐI NGẪU
        # =====================================================================
        fake_zero_vars = set()
        for v_info in var_mapping.values():
            if v_info['type'] == 'free':
                pos_var, neg_var = v_info['vars']
                if pos_var in B and neg_var in N: fake_zero_vars.add(neg_var)
                elif neg_var in B and pos_var in N: fake_zero_vars.add(pos_var)

        # Tìm các biến không cơ sở có hệ số mục tiêu (reduced cost) bằng 0
        zero_obj_vars = [j for j in N if obj[j] == 0 and j not in fake_zero_vars]
        is_dual_unique = (len(zero_obj_vars) == 0)

        if not is_dual_unique:
            print("\n-> Bài toán đối ngẫu có VÔ SỐ NGHIỆM tối ưu.")
            print(" -> Do y* không duy nhất, việc áp dụng hệ độ lệch bù từ một đỉnh đối ngẫu bất kỳ không đảm bảo khôi phục được chính xác x*.")
            primal_status = 'Tối ưu (Suy biến hoặc Vô số nghiệm)'
            primal_solution = "Không thể giải duy nhất qua hệ độ lệch bù tuyến tính"
            print(f" => Giá trị tối ưu Z = {primal_z_display}")
            
        else:
            # ---------------------------------------------------------------------
            # ĐIỀU KIỆN ĐỘ LỆCH BÙ (COMPLEMENTARY SLACKNESS) ĐỂ TÌM x*
            # ---------------------------------------------------------------------
            print("\n-> Nghiệm đối ngẫu là duy nhất. Phân tích Điều kiện độ lệch bù:")
            n_primal_vars = len(c)
            n_primal_constraints = len(b)
            
            M = []
            v_rhs = []
            
            # Điều kiện 1: Nếu độ lệch của ràng buộc đối ngẫu j khác 0, thì biến gốc x_j = 0
            for j in range(n_primal_vars):
                A_trans_y_j = sum(Fraction(A[i][j]) * y_opt[i] for i in range(n_primal_constraints))
                slack_j = Fraction(0)
                vs = var_signs[j]
                
                if method.lower() == 'max':
                    if vs == 'không âm': slack_j = A_trans_y_j - Fraction(c[j])
                    elif vs == 'không dương': slack_j = Fraction(c[j]) - A_trans_y_j
                else: # min
                    if vs == 'không âm': slack_j = Fraction(c[j]) - A_trans_y_j
                    elif vs == 'không dương': slack_j = A_trans_y_j - Fraction(c[j])
                    
                if slack_j != 0:
                    row = [0.0] * n_primal_vars
                    row[j] = 1.0
                    M.append(row)
                    v_rhs.append(0.0)
            
            # Điều kiện 2: Nếu biến đối ngẫu y_i != 0 hoặc ràng buộc gốc ban đầu là dấu '=', ràng buộc gốc i phải chặt
            for i in range(n_primal_constraints):
                if y_opt[i] != 0 or constraint_types[i] == '=':
                    row = [float(A[i][j]) for j in range(n_primal_vars)]
                    M.append(row)
                    v_rhs.append(float(b[i]))
            
            # Giải hệ ràng buộc độ lệch bù bằng bình phương tối thiểu để kiểm tra tính duy nhất
            if len(M) >= n_primal_vars:
                M_arr = np.array(M, dtype=float)
                v_arr = np.array(v_rhs, dtype=float)
                x_floats, residuals, rank, s = np.linalg.lstsq(M_arr, v_arr, rcond=None)
                
                if rank == n_primal_vars:
                    primal_status = 'Tối ưu (Nghiệm duy nhất)'
                    for j in range(n_primal_vars):
                        val_frac = Fraction.from_float(x_floats[j]).limit_denominator()
                        primal_solution[f'x{j+1}'] = format_frac(val_frac)
                        print(f" - Nghiệm tối ưu duy nhất bài toán gốc: x{j+1} = {primal_solution[f'x{j+1}']}")
                    print(f" => Giá trị tối ưu Z = {primal_z_display}")
                else:
                    primal_status = 'Tối ưu (Vô số nghiệm)'
                    primal_solution = "Miền vô số nghiệm"
                    print(" -> Hệ phương trình phụ thuộc tuyến tính (Bài toán gốc có vô số nghiệm).")
            else:
                primal_status = 'Tối ưu (Vô số nghiệm)'
                primal_solution = "Hệ thiếu phương trình độc lập"
                print(" -> Không đủ ràng buộc chặt độc lập để xác định duy nhất nghiệm x* (Bài toán gốc vô số nghiệm).")
            
         # Đóng gói kết quả - GỘP CẢ NGHIỆM GỐC (x) VÀ ĐỐI NGẪU (y)
    full_solution = {}
    
    # Thêm nghiệm gốc (x) từ primal_solution
    for k, v in primal_solution.items():
        if k.startswith('x'):
            full_solution[k] = str(v)
    
    # Thêm nghiệm đối ngẫu (y) từ dual_result_dict['solution'] (current_sol_dict)
    for k, v in dual_result_dict.get('solution', {}).items():
        if k.startswith('y'):
            full_solution[k] = str(v)
    
    # Nếu primal_solution rỗng nhưng current_sol_dict có x, thì lấy luôn
    if not full_solution:
        for k, v in dual_result_dict.get('solution', {}).items():
            full_solution[k] = str(v)
    
    result_dict = {
        'status': primal_status,
        'z': primal_z_display,
        'solution': full_solution,  # Dùng full_solution thay vì primal_solution
        'path_vertices': path_vertices,
        'plot_html': None
    }
    
    # Vẽ đồ thị bài toán đối ngẫu nếu có 2 biến
    if len(dual_c) == 2:
        plot_html = plot_dual_lp(
            dual_c, dual_A, dual_b, 
            dual_constraint_types, dual_method, dual_var_signs,
            dual_result_dict, path_vertices
        )
        result_dict['plot_html'] = plot_html
    
    return result_dict