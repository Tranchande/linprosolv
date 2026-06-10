import sys
import io
import os
import math
from flask import Flask, render_template, request, jsonify
from fractions import Fraction

# Import cả hai solver
from solve_two_phase import solve_two_phase
from duality import solve_duality
from plot_graph import plot_2d_lp

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/solve', methods=['POST'])
def solve_lp():
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout
    
    try:
        # ========== LẤY DỮ LIỆU CƠ BẢN ==========
        try:
            num_vars = int(request.form.get('num_vars', 2))
            num_constraints = int(request.form.get('num_constraints', 2))
            
            if num_vars < 1 or num_vars > 20:
                raise ValueError("Số biến phải từ 1 đến 20")
            if num_constraints < 1 or num_constraints > 50:
                raise ValueError("Số ràng buộc phải từ 1 đến 50")
        except ValueError as e:
            return jsonify({"success": False, "error": f"Dữ liệu đầu vào không hợp lệ: {str(e)}"})
        
        objective_type = request.form.get('objective_type', 'max')
        if objective_type not in ['max', 'min']:
            return jsonify({"success": False, "error": "Loại mục tiêu phải là 'max' hoặc 'min'"})
        
        solution_method = request.form.get('solution_method', 'two_phase')
        if solution_method not in ['two_phase', 'duality']:
            return jsonify({"success": False, "error": "Phương pháp giải không hợp lệ"})
        
        # ========== VALIDATION HÀM MỤC TIÊU ==========
        c = []
        for j in range(num_vars):
            try:
                val_str = request.form.get(f'c{j}', '0').strip()
                if not val_str:
                    val_str = '0'
                # Hỗ trợ phân số như "1/2"
                if '/' in val_str:
                    from fractions import Fraction
                    val = float(Fraction(val_str))
                else:
                    val = float(val_str)
                
                if math.isnan(val) or math.isinf(val):
                    raise ValueError(f"Giá trị không hợp lệ: {val_str}")
                
                c.append(val)
            except Exception as e:
                return jsonify({
                    "success": False, 
                    "error": f"Hệ số c{j+1} không hợp lệ: '{request.form.get(f'c{j}', '0')}'. Lỗi: {str(e)}"
                })
        
        # ========== VALIDATION DẤU BIẾN ==========
        variable_types = []
        for j in range(num_vars):
            var_type = request.form.get(f'var_type{j}', 'không âm').strip().lower()
            if var_type not in ['không âm', 'không dương', 'tự do']:
                return jsonify({
                    "success": False,
                    "error": f"Dấu của biến x{j+1} không hợp lệ. Chỉ chấp nhận: 'không âm', 'không dương', 'tự do'"
                })
            variable_types.append(var_type)
        
        # ========== VALIDATION RÀNG BUỘC ==========
        A = []
        b = []
        constraint_types = []
        
        for i in range(num_constraints):
            # Validate từng hệ số trong ràng buộc
            row = []
            for j in range(num_vars):
                try:
                    val_str = request.form.get(f'A{i}_{j}', '0').strip()
                    if not val_str:
                        val_str = '0'
                    
                    if '/' in val_str:
                        from fractions import Fraction
                        val = float(Fraction(val_str))
                    else:
                        val = float(val_str)
                    
                    if math.isnan(val) or math.isinf(val):
                        raise ValueError
                    
                    row.append(val)
                except:
                    return jsonify({
                        "success": False,
                        "error": f"Hệ số a{i+1}{j+1} (ràng buộc {i+1}, biến {j+1}) không hợp lệ: '{request.form.get(f'A{i}_{j}', '0')}'"
                    })
            A.append(row)
            
            # Validate vế phải b
            try:
                b_str = request.form.get(f'b{i}', '0').strip()
                if not b_str:
                    b_str = '0'
                
                if '/' in b_str:
                    from fractions import Fraction
                    b_val = float(Fraction(b_str))
                else:
                    b_val = float(b_str)
                
                if math.isnan(b_val) or math.isinf(b_val):
                    raise ValueError
                
                b.append(b_val)
            except:
                return jsonify({
                    "success": False,
                    "error": f"Giá trị b{i+1} (vế phải ràng buộc {i+1}) không hợp lệ: '{request.form.get(f'b{i}', '0')}'"
                })
            
            # Validate loại ràng buộc
            const_type = request.form.get(f'constraint_type{i}', '<=').strip()
            if const_type not in ['<=', '>=', '=']:
                return jsonify({
                    "success": False,
                    "error": f"Loại ràng buộc {i+1} không hợp lệ. Chỉ chấp nhận: '<=', '>=', '='"
                })
            constraint_types.append(const_type)
        
        # ========== KIỂM TRA THÊM ==========
        # Kiểm tra nếu tất cả hệ số mục tiêu đều bằng 0
        if all(abs(x) < 1e-12 for x in c):
            print("⚠️ Cảnh báo: Tất cả hệ số mục tiêu đều bằng 0")
        
        # Kiểm tra ràng buộc trùng lặp (cơ bản)
        for i in range(len(b)):
            if abs(b[i]) > 1e12:
                print(f"⚠️ Cảnh báo: Giá trị b[{i+1}] = {b[i]} rất lớn, có thể gây tràn số")
        
        # ========== TIẾP TỤC CHẠY SOLVER ==========
        # Chọn solver dựa trên phương pháp
        if solution_method == 'duality':
            print("=== SỬ DỤNG PHƯƠNG PHÁP ĐỐI NGẪU ===")
            algo_result = solve_duality(
                c=c, A=A, b=b, 
                constraint_types=constraint_types, 
                method=objective_type, 
                var_signs=variable_types
            )
        else:
            print("=== SỬ DỤNG PHƯƠNG PHÁP ĐƠN HÌNH 2 PHA ===")
            algo_result = solve_two_phase(
                c=c, A=A, b=b, 
                constraint_types=constraint_types, 
                method=objective_type, 
                var_signs=variable_types
            )


        sys.stdout = old_stdout
        raw_logs = new_stdout.getvalue()

        # Hiển thị nghiệm theo đúng phương pháp, không làm tròn
        solution_display = {}
        if algo_result and isinstance(algo_result.get('solution'), dict):
            print("DEBUG: solution_method =", solution_method)
            print("DEBUG: solution keys =", list(algo_result['solution'].keys()))
            print("DEBUG: solution =", algo_result['solution'])
            
            if solution_method == 'duality':
                # Phương pháp đối ngẫu: hiển thị cả nghiệm đối ngẫu (y) và nghiệm gốc (x)
                for k, v in algo_result['solution'].items():
                    if k.startswith('y') or k.startswith('x'):
                        solution_display[k] = str(v)
                # Nếu không tìm thấy y hoặc x, hiển thị tất cả
                if not solution_display:
                    solution_display = {k: str(v) for k, v in algo_result['solution'].items()}
            else:
                # Phương pháp đơn hình: hiển thị nghiệm x (gốc)
                for k, v in algo_result['solution'].items():
                    if k.startswith('x'):
                        solution_display[k] = str(v)
                # Nếu không tìm thấy x, hiển thị tất cả
                if not solution_display:
                    solution_display = {k: str(v) for k, v in algo_result['solution'].items()}

        # Vẽ đồ thị
                # Vẽ đồ thị - ưu tiên dùng plot_html từ solver
        plot_html = ""
        if solution_method == 'duality' and algo_result.get('plot_html'):
            plot_html = algo_result['plot_html']
        elif num_vars == 2:
            try:
                plot_html = plot_2d_lp(
                    c=c, A=A, b=b, 
                    constraint_types=constraint_types, 
                    method=objective_type, 
                    var_signs=variable_types,
                    result=algo_result,
                    path_vertices=algo_result.get('path_vertices', None)
                )
            except Exception as graph_err:
                print(f"Lỗi khi dựng đồ thị: {graph_err}")

        # Xử lý hiển thị Z (giữ nguyên phân số)
        z_value = algo_result.get('z', 'N/A')

        return jsonify({
            "success": True,
            "result": {
                "status": algo_result.get('status', 'Tối ưu'),
                "z": str(z_value),
                "solution": solution_display,
                "plot_html": plot_html,
                "steps": [],
                "raw_logs": raw_logs if raw_logs else "Tính toán thành công!"
            }
        })

    except Exception as e:
        if 'old_stdout' in locals():
            sys.stdout = old_stdout
        import traceback
        return jsonify({
            "success": False, 
            "error": f"Lỗi xử lý Backend: {str(e)}",
            "detail": traceback.format_exc()
        })

if __name__ == '__main__':
    app.run(debug=True, port=2026)