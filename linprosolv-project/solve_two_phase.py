import copy
import plotly.graph_objects as go
import numpy as np
from fractions import Fraction
import math
from plot_graph import plot_2d_lp

# ==========================================
# In từ vựng ra màn hình
# ==========================================
def print_dictionary(N, B, b_dict, C, v, obj, phase_name, step, n_vars, entering=None, leaving=None, var_char='x'):
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
    var_char = 'x' if all_non_negative else 'y'
    
    if all_non_negative:
        print(" - Tất cả các biến đều không âm, không cần đổi tên biến (giữ nguyên hệ ban đầu).")
    
    mapped_c = []
    mapped_A_cols = [[] for _ in range(m)]
    var_mapping = {}
    
    new_var_idx = 1
    for j in range(n_orig):
        sign = var_signs[j].lower().strip()
        col_A = [A[i][j] for i in range(m)]
        orig_name = f"x{j+1}"
        
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
# XOAY HAI PHA
# ==========================================
def solve_two_phase(c, A, b, constraint_types, method='max', var_signs=None):
    
    # Khởi tạo danh sách lưu hành trình
    path_vertices = []
    n_orig = len(c)

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

    print(f"=== MỤC TIÊU BÀI TOÁN GỐC: TÌM {method.upper()} ===")
    
    std_c, std_A, std_b, var_mapping, var_char = standardize_problem(c, A, b, constraint_types, method, var_signs)
    N, B, b_dict, C, v, obj = build_initial_dictionary(std_c, std_A, std_b)
    
    n_vars = len(std_c) 
    # Ghi lại điểm xuất phát
    update_path()

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
            z_display = "âm vô cùng" if method == 'max' else "dương vô cùng"
            print(" -> Vì x0 khác 0, kết luận bài toán VÔ NGHIỆM.")
            result_dict = {'status': 'Vô nghiệm', 'z': z_display, 'solution': {}}
            if len(c) == 2: plot_2d_lp(c, A, b, constraint_types, method, var_signs, result_dict)
            return result_dict
        else:
            print(" -> Vì x0 = 0, bài toán có nghiệm. Tiến hành chuyển sang Pha 2.")
            
        if 0 in B:
            for j in N:
                if C[0][j] != 0:
                    print_dictionary(N, B, b_dict, C, v, obj, "PHA 1 (Đẩy x0 khỏi cơ sở)", "Phụ", n_vars, entering=j, leaving=0, var_char=var_char)
                    pivot(N, B, b_dict, C, v, obj, j, 0)
                    update_path()
                    break
                    
        if 0 in N:
            N.remove(0)
            for i in B:
                del C[i][0]
                
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

    # ==========================================
    # KÍCH HOẠT PHA 2
    # ==========================================
    status = simplex_bland(N, B, b_dict, C, v, obj, "PHA 2", n_vars, start_step=0, path_callback=update_path, var_char=var_char)
    
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
        
        # Hàm bổ trợ lấy giá trị hiện tại của biến trong từ vựng
        def get_val(idx):
            return b_dict[idx] if idx in B else Fraction(0)

        # Định nghĩa hàm đặt tên biến nhất quán với biến trạng thái var_char
        def var_name(idx):
            if idx == 0: return "x0"
            if 1 <= idx <= n_vars: return f"x{idx}"
            return f"w{idx - n_vars}"

        # TRÍCH XUẤT NGHIỆM GỐC KHÔNG BỊ LỆCH CHỈ SỐ (Hỗ trợ cả 0-indexed và 1-indexed)
        current_sol_dict = {}
        for orig_idx, v_info in var_mapping.items():
            # Tự động chuẩn hóa chỉ số hiển thị của bài toán gốc sang 1, 2, 3...
            display_idx = orig_idx if (isinstance(orig_idx, int) and orig_idx > 0) else orig_idx + 1
            
            if v_info['type'] == '>=0':
                val = get_val(v_info['vars'][0])
            elif v_info['type'] == '<=0':
                val = -get_val(v_info['vars'][0])
            elif v_info['type'] == 'free':
                val = get_val(v_info['vars'][0]) - get_val(v_info['vars'][1])
            
            val_str = format_frac(val)
            # SỬA TẠI ĐÂY: Khóa 'x' cố định cho bài toán gốc, khóa 'y' cố định cho đồ thị Plotly
            current_sol_dict[f'x{display_idx}'] = val_str  
            current_sol_dict[f'y{display_idx}'] = val_str  

        print("\n=== KẾT LUẬN BÀI TOÁN GỐC ===")
        
        # PHÂN NHÁNH TRẠNG THÁI TỐI ƯU
        if zero_obj_vars:
            status = 'Tối ưu (Vô số nghiệm)'
            solution = current_sol_dict 
            
            print(f"Trạng thái: BÀI TOÁN CÓ VÔ SỐ NGHIỆM (ALTERNATIVE OPTIMA)")
            print(f" => Giá trị tối ưu Z = {z_display}")
            
            # SỬA TẠI ĐÂY: Ép buộc lọc theo 'x' để hiển thị bài toán gốc dạng x1, x2...
            for k, v_str in solution.items():
                if k.startswith('x'): 
                    print(f" - Một điểm cực biên tối ưu nền: {k} = {v_str}")
                
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
            print(f"    Điều kiện tham số: {', '.join([f'{name} >= 0' for name in zero_names])}")
            print("    (Tất cả các biến không cơ sở khác bị gán chặt bằng 0)")

        else:
            status = 'Tối ưu (Nghiệm duy nhất)'
            solution = current_sol_dict
            
            print(f"Trạng thái: Tối ưu (Nghiệm duy nhất)")
            # SỬA TẠI ĐÂY: Luôn luôn duyệt và in ra nhãn 'x' cho bài toán gốc
            for k, v_str in solution.items():
                if k.startswith('x'): 
                    print(f" - Điểm cực biên tối ưu: {k} = {v_str}")
            print(f" => Giá trị tối ưu Z = {z_display}")

    # Đoạn cuối cùng của hàm solve_two_phase trong file solve_two_phase.py
    result_dict = {
        'status': status,
        'z': z_display,
        'solution': solution,
        'path_vertices': path_vertices  # BẮT BUỘC: phải trả về mảng này để nuôi mũi tên xanh!
    }
    

    return result_dict
