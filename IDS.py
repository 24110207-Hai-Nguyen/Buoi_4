import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
import random

# Định nghĩa trạng thái Đích (Goal State)
GOAL_STATE = (
    (1, 2, 3),
    (4, 5, 6),
    (7, 8, 0) # 0 là ô trống
)

class EightPuzzleIDS:
    def __init__(self, root):
        self.root = root
        self.root.title("8-Puzzle IDS Solver Pro")
        self.root.geometry("850x700")  # Mở rộng chiều rộng để chứa Log Panel
        self.root.configure(bg="#2c3e50")
        self.root.resizable(False, False)

        # Trạng thái hiện tại
        self.current_state = GOAL_STATE
        self.tiles = {}
        self.is_running = False

        # --- BỐ CỤC GIAO DIỆN (UI LAYOUT) ---
        
        # 1. TIÊU ĐỀ CHÍNH
        self.title_label = tk.Label(root, text="8-PUZZLE SOLVER (IDS)", font=("Arial", 20, "bold"), fg="#ecf0f1", bg="#2c3e50")
        self.title_label.pack(pady=10)

        # Khung chứa toàn bộ nội dung (Chia làm Bên trái và Bên phải)
        main_container = tk.Frame(root, bg="#2c3e50")
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        # --- PHÍA BÊN TRÁI: ĐIỀU KHIỂN & MA TRẬN & ĐƯỜNG ĐI ---
        left_frame = tk.Frame(main_container, bg="#2c3e50")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.status_label = tk.Label(left_frame, text="Trạng thái: Sẵn sàng", font=("Arial", 11), fg="#f1c40f", bg="#2c3e50")
        self.status_label.pack(pady=2)

        self.depth_label = tk.Label(left_frame, text="Độ sâu tìm kiếm (Depth): 0", font=("Arial", 12, "bold"), fg="#3498db", bg="#2c3e50")
        self.depth_label.pack(pady=2)

        self.steps_label = tk.Label(left_frame, text="Số bước dịch chuyển: 0", font=("Arial", 12, "bold"), fg="#2ecc71", bg="#2c3e50")
        self.steps_label.pack(pady=2)

        # Khung chứa ma trận 3x3
        self.grid_frame = tk.Frame(left_frame, bg="#34495e")
        self.grid_frame.pack(pady=10)
        self.create_grid()

        # Nút bấm điều khiển
        btn_frame = tk.Frame(left_frame, bg="#2c3e50")
        btn_frame.pack(pady=5)

        self.btn_shuffle = tk.Button(btn_frame, text="Trộn Khó (16 Bước)", font=("Arial", 11, "bold"), bg="#e67e22", fg="white", width=18, command=self.shuffle_board)
        self.btn_shuffle.pack(side=tk.LEFT, padx=5)

        self.btn_solve = tk.Button(btn_frame, text="Giải Bằng IDS", font=("Arial", 11, "bold"), bg="#2ecc71", fg="white", width=15, command=self.start_solve)
        self.btn_solve.pack(side=tk.LEFT, padx=5)

        # Ô xuất đường đi kết quả (Mới thêm)
        path_title = tk.Label(left_frame, text="ĐƯỜNG ĐI ĐẾN ĐÍCH CHI TIẾT:", font=("Arial", 11, "bold"), fg="#ecf0f1", bg="#2c3e50")
        path_title.pack(anchor=tk.W, pady=(10, 2), padx=10)
        
        self.path_output = scrolledtext.ScrolledText(left_frame, width=50, height=8, font=("Courier New", 10), bg="#1a252f", fg="#1abc9c", wrap=tk.WORD)
        self.path_output.pack(padx=10, fill=tk.X)
        self.path_output.insert(tk.END, "Chưa có lời giải. Vui lòng bấm 'Trộn Khó' rồi chọn 'Giải Bằng IDS'...")
        self.path_output.config(state=tk.DISABLED)

        # --- PHÍA BÊN PHẢI: LOG PANEL NHẬT KÝ CHẠY THỜI GIAN THỰC (Mới thêm) ---
        right_frame = tk.Frame(main_container, bg="#2c3e50")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(15, 0))

        log_title = tk.Label(right_frame, text="NHẬT KÝ HOẠT ĐỘNG (LOG PANEL)", font=("Arial", 11, "bold"), fg="#ecf0f1", bg="#2c3e50")
        log_title.pack(anchor=tk.W, pady=(0, 5))

        self.log_panel = scrolledtext.ScrolledText(right_frame, width=42, height=33, font=("Courier New", 9), bg="#000000", fg="#daffde")
        self.log_panel.pack(fill=tk.BOTH, expand=True)
        self.log_append("Hệ thống khởi tạo thành công.\nSẵn sàng nhận lệnh.")

    # --- CÁC HÀM XỬ LÝ GIAO DIỆN ---
    
    def create_grid(self):
        """Tạo lưới 3x3 ô số trên giao diện"""
        for r in range(3):
            for c in range(3):
                val = self.current_state[r][c]
                text = str(val) if val != 0 else ""
                bg_color = "#e74c3c" if val != 0 else "#34495e"
                fg_color = "white" if val != 0 else "#34495e"
                
                label = tk.Label(self.grid_frame, text=text, font=("Arial", 22, "bold"), bg=bg_color, fg=fg_color, width=5, height=2, bd=2, relief="groove")
                label.grid(row=r, column=c, padx=4, pady=4)
                self.tiles[(r, c)] = label

    def update_ui(self, state):
        """Cập nhật lại giá trị và màu sắc ma trận trên giao diện"""
        for r in range(3):
            for c in range(3):
                val = state[r][c]
                text = str(val) if val != 0 else ""
                bg_color = "#e74c3c" if val != 0 else "#34495e"
                fg_color = "white" if val != 0 else "#34495e"
                
                self.tiles[(r, c)].config(text=text, bg=bg_color, fg=fg_color)
        self.root.update()

    def log_append(self, msg):
        """Hàm helper để đẩy thêm dòng thông báo vào Log Panel"""
        self.log_panel.config(state=tk.NORMAL)
        self.log_panel.insert(tk.END, msg + "\n")
        self.log_panel.see(tk.END)  # Tự động cuộn xuống dưới cùng
        self.log_panel.config(state=tk.DISABLED)

    def print_state_flat(self, state):
        """Chuyển ma trận 3x3 thành chuỗi 1 dòng gọn đẹp để ghi log"""
        return " ".join("".join(str(cell) for cell in row) for row in state)

    def find_blank(self, state):
        """Tìm tọa độ của ô trống (số 0)"""
        for r in range(3):
            for c in range(3):
                if state[r][c] == 0:
                    return r, c

    def get_successors(self, state):
        """Sinh ra các trạng thái con hợp lệ bằng cách trượt ô trống"""
        successors = []
        r, c = self.find_blank(state)
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)] # Lên, Xuống, Trái, Phải

        for dr, dc in moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 3 and 0 <= nc < 3:
                new_state = [list(row) for row in state]
                new_state[r][c], new_state[nr][nc] = new_state[nr][nc], new_state[r][c]
                successors.append(tuple(tuple(row) for row in new_state))
        return successors

    # --- THUẬT TOÁN IDS TỐI ƯU CÓ GHI LOG THỜI GIAN THỰC ---

    def depth_limited_search(self, state, limit, current_depth, path, visited_global):
        """Hàm DLS duyệt trạng thái kèm theo ghi Log chi tiết từng node"""
        if state == GOAL_STATE:
            return path + [state]

        if current_depth >= limit:
            return "cutoff"

        if state in visited_global and visited_global[state] <= current_depth:
            return None
        
        visited_global[state] = current_depth
        cutoff_occurred = False
        
        for child in self.get_successors(state):
            if child not in path: 
                result = self.depth_limited_search(child, limit, current_depth + 1, path + [state], visited_global)
                if result == "cutoff":
                    cutoff_occurred = True
                elif result is not None:
                    return result

        return "cutoff" if cutoff_occurred else None

    def iterative_deepening_search(self, start_state):
        """Hàm lặp tăng dần tầng độ sâu (IDS)"""
        depth = 0
        while True:
            self.depth_label.config(text=f"Đang quét ở độ sâu Depth = {depth}...")
            self.log_append(f"[KÍCH HOẠT] Khởi chạy lượt tìm kiếm mới ở Tầng Depth = {depth}")
            self.root.update()
            
            visited_global = {} 
            result = self.depth_limited_search(start_state, depth, 0, [], visited_global)
            
            # Ghi nhận số lượng node đã quét qua ở tầng hiện tại vào log panel
            self.log_append(f" -> Tầng {depth} đã duyệt xong {len(visited_global)} trạng thái.")
            
            if result != "cutoff":
                return result, depth
            
            depth += 1
            if depth > 22:
                return None, depth

    # --- HÀM ĐIỀU KHIỂN SỰ KIỆN NÚT BẤM ---

    def shuffle_board(self):
        """Trộn bảng ngẫu nhiên 16 bước khó"""
        if self.is_running: return
        
        state = GOAL_STATE
        last_state = None
        
        self.log_append("\n[HÀM TRỘN] Đang thực hiện trượt ngẫu nhiên 16 bước từ đích...")
        for i in range(16): 
            successors = self.get_successors(state)
            choices = [s for s in successors if s != last_state]
            if not choices: choices = successors
            
            last_state = state
            state = random.choice(choices)
            self.log_append(f"  Bước trộn {i+1}: {self.print_state_flat(state)}")
            
        self.current_state = state
        self.update_ui(self.current_state)
        
        # Reset các ô hiển thị thông số thông tin
        self.status_label.config(text="Đã trộn mức ĐỘ KHÓ CAO!")
        self.depth_label.config(text="Độ sâu tìm kiếm (Depth): 0")
        self.steps_label.config(text="Số bước dịch chuyển: 0")
        
        self.path_output.config(state=tk.NORMAL)
        self.path_output.delete("1.0", tk.END)
        self.path_output.insert(tk.END, "Bảng đã trộn xong. Hệ thống đã sẵn sàng giải!")
        self.path_output.config(state=tk.DISABLED)

    def start_solve(self):
        """Kích hoạt giải thuật, in lịch trình ra Log Panel và kết xuất đường đi chi tiết"""
        if self.is_running: return
        if self.current_state == GOAL_STATE:
            messagebox.showinfo("Thông báo", "Bảng đã ở trạng thái đích sẵn rồi!")
            return

        self.is_running = True
        self.btn_shuffle.config(state=tk.DISABLED)
        self.btn_solve.config(state=tk.DISABLED)
        self.status_label.config(text="Đang tính toán...")
        
        self.log_append(f"\n[BẮT ĐẦU GIẢI] Trạng thái xuất phát: {self.print_state_flat(self.current_state)}")
        self.root.update()

        # Thực hiện thuật toán IDS
        path_solution, final_depth = self.iterative_deepening_search(self.current_state)

        if path_solution:
            # 1. Cập nhật ma trận UI về Đích tức thì
            self.current_state = GOAL_STATE
            self.update_ui(self.current_state)
            
            total_steps = len(path_solution) - 1
            
            # 2. Cập nhật nhãn thông tin
            self.depth_label.config(text=f"Độ sâu tìm thấy (Depth): {final_depth}")
            self.steps_label.config(text=f"Số bước dịch chuyển: {total_steps}")
            self.status_label.config(text="Trạng thái: Đã tìm thấy đích!")
            
            # 3. Ghi Log thành công vào Log Panel bên phải
            self.log_append(f"[THÀNH CÔNG] Tìm thấy lời giải tại tầng sâu {final_depth}!")
            self.log_append(f" -> Tổng số bước dịch chuyển thực tế: {total_steps} bước.\n")
            
            # 4. KẾT XUẤT ĐƯỜNG ĐI CHI TIẾT (Mới thêm) ra Khung Output bên trái
            self.path_output.config(state=tk.NORMAL)
            self.path_output.delete("1.0", tk.END)
            
            path_str_list = []
            for idx, step in enumerate(path_solution):
                step_name = f"Bắt đầu" if idx == 0 else f"Bước {idx}"
                if idx == len(path_solution) - 1:
                    step_name = "ĐÍCH"
                
                # Định dạng ma trận 3x3 sang dạng chuỗi dễ xem trong bảng text
                matrix_str = f"[{step[0][0]},{step[0][1]},{step[0][2]} | {step[1][0]},{step[1][1]},{step[1][2]} | {step[2][0]},{step[2][1]},{step[2][2]}]"
                path_str_list.append(f"-> {step_name}: {matrix_str}")
                
            # Đẩy chuỗi đường đi lên khung giao diện
            self.path_output.insert(tk.END, "\n".join(path_str_list))
            self.path_output.config(state=tk.DISABLED)
            
            messagebox.showinfo("Thành công", f"Tìm thấy đích ở độ sâu (Depth): {final_depth}\nĐã xuất toàn bộ {total_steps} bước đi ra khung hiển thị!")
        else:
            self.log_append(f"[THẤT BẠI] Quét tới giới hạn tầng {final_depth} nhưng không tìm ra đường đi.")
            self.depth_label.config(text=f"Cắt tại giới hạn Depth: {final_depth}")
            self.status_label.config(text="Không tìm thấy lời giải.")
            messagebox.showwarning("Thất bại", "Không tìm thấy lời giải trong giới hạn tầng sâu!")

        self.btn_shuffle.config(state=tk.NORMAL)
        self.btn_solve.config(state=tk.NORMAL)
        self.is_running = False

if __name__ == "__main__":
    root = tk.Tk()
    app = EightPuzzleIDS(root)
    root.mainloop()