import tkinter as tk
from tkinter import ttk, messagebox
import random
import collections
import heapq
import time
import threading

# --- CẤU HÌNH BÀI TOÁN 8-PUZZLE ---
GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)

class Node:
    _id_counter = 65  # Bắt đầu đặt tên node từ chữ 'A' (ASCII 65)
    
    def __init__(self, state, parent=None, action=None, cost=0, depth=0, h_cost=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.cost = cost      # g(n)
        self.depth = depth
        self.h_cost = h_cost  # h(n) - Misplaced tiles
        self.f_cost = cost + h_cost # f(n) dùng cho A*
        
        # Gán tên định danh Node (A, B, C,...) giống trong ảnh mẫu
        if parent is None:
            self.name = "A"
        else:
            self.name = chr(Node._id_counter)
            Node._id_counter += 1
            if Node._id_counter > 90: # Reset vòng lại nếu vượt quá chữ Z
                Node._id_counter = 65

    def __lt__(self, other):
        # Mặc định ưu tiên theo f_cost (hoặc cost tùy thuật toán)
        return self.f_cost < other.f_cost

def get_misplaced_tiles(state):
    """ Hàm Heuristic đếm số ô sai vị trí so với trạng thái GOAL """
    count = 0
    for i in range(9):
        if state[i] != 0 and state[i] != GOAL[i]:
            count += 1
    return count

def get_neighbors(state):
    neighbors = []
    idx = state.index(0)
    row, col = divmod(idx, 3)
    moves = [(-1, 0, 'Up'), (1, 0, 'Down'), (0, -1, 'Left'), (0, 1, 'Right')]
    
    for dr, dc, move in moves:
        r, c = row + dr, col + dc
        if 0 <= r < 3 and 0 <= c < 3:
            new_idx = r * 3 + c
            new_state = list(state)
            new_state[idx], new_state[new_idx] = new_state[new_idx], new_state[idx]
            neighbors.append((tuple(new_state), move))
    return neighbors

def format_state_matrix(state):
    """ Định dạng ma trận 3x3 để in vào bảng Log """
    matrix_str = ""
    for i in range(3):
        row = [str(x) if x != 0 else "_" for x in state[i*3:(i+1)*3]]
        matrix_str += " " + " ".join(row) + "\n"
    return matrix_str

# --- GIAO DIỆN CHÍNH ---
class EightPuzzleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("8-Puzzle Search Algorithms")
        self.root.geometry("1150x700")
        self.root.configure(bg="#f5f6f8")

        self.current_state = list(GOAL)
        self.path = []
        self.current_step_idx = 0
        self.is_running = False
        
        self.setup_ui()
        self.reset_puzzle()

    def setup_ui(self):
        # --- Top Control Bar (Góc phải trên cùng như ảnh) ---
        top_frame = tk.Frame(self.root, bg="#f5f6f8", height=50)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=20, pady=10)

        # Tiêu đề góc trái
        title_label = tk.Label(top_frame, text="8-Puzzle Search Algorithms", font=("Arial", 16, "bold"), bg="#f5f6f8", fg="#1e293b")
        title_label.pack(side=tk.LEFT)

        # Cụm điều khiển dồn sang bên phải
        right_controls = tk.Frame(top_frame, bg="#f5f6f8")
        right_controls.pack(side=tk.RIGHT)

        tk.Label(right_controls, text="Algorithm", bg="#f5f6f8").pack(side=tk.LEFT, padx=5)
        self.algo_var = tk.StringVar(value="UCS")
        self.algo_menu = ttk.Combobox(right_controls, textvariable=self.algo_var, values=["BFS", "DFS", "UCS", "IDS", "A* (Misplaced)"], width=15, state="readonly")
        self.algo_menu.pack(side=tk.LEFT, padx=5)

        tk.Label(right_controls, text="Max depth", bg="#f5f6f8").pack(side=tk.LEFT, padx=5)
        self.max_depth_entry = tk.Spinbox(right_controls, from_=1, to=200, width=5)
        self.max_depth_entry.delete(0, "end")
        self.max_depth_entry.insert(0, "35")
        self.max_depth_entry.pack(side=tk.LEFT, padx=5)

        self.btn_random = tk.Button(right_controls, text="Random", bg="#ffffff", bd=1, relief=tk.SOLID, command=self.shuffle_puzzle, padx=10)
        self.btn_random.pack(side=tk.LEFT, padx=5)

        self.btn_run = tk.Button(right_controls, text="Run", bg="#ffffff", bd=1, relief=tk.SOLID, command=self.start_solve, padx=15)
        self.btn_run.pack(side=tk.LEFT, padx=5)

        self.btn_reset = tk.Button(right_controls, text="Reset", bg="#ffffff", bd=1, relief=tk.SOLID, command=self.reset_puzzle, padx=10)
        self.btn_reset.pack(side=tk.LEFT, padx=5)

        # --- Main Layout Division ---
        main_frame = tk.Frame(self.root, bg="#f5f6f8")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # --- LEFT COLUMN: Puzzle Grid & Controls ---
        left_column = tk.Frame(main_frame, bg="#f5f6f8")
        left_column.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

        # Khung chứa lưới ô số 3x3
        self.grid_frame = tk.Frame(left_column, bg="#f5f6f8")
        self.grid_frame.pack(pady=10)
        self.cells = []
        for i in range(9):
            btn = tk.Button(self.grid_frame, text="", font=("Arial", 22, "bold"), width=4, height=2, bg="#2563eb", fg="white", bd=0, highlightthickness=0)
            btn.grid(row=i//3, column=i%3, padx=4, pady=4)
            self.cells.append(btn)

        # Nút điều hướng bước đi dưới Grid
        nav_frame = tk.Frame(left_column, bg="#f5f6f8")
        nav_frame.pack(fill=tk.X, pady=5)
        
        self.btn_prev = tk.Button(nav_frame, text="Prev Step", font=("Arial", 9), command=self.prev_step, bg="#ffffff", bd=1, relief=tk.SOLID)
        self.btn_prev.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        self.btn_next = tk.Button(nav_frame, text="Next Step", font=("Arial", 9), command=self.next_step, bg="#ffffff", bd=1, relief=tk.SOLID)
        self.btn_next.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        self.btn_auto = tk.Button(nav_frame, text="Auto Run", font=("Arial", 9), command=self.toggle_auto, bg="#ffffff", bd=1, relief=tk.SOLID)
        self.btn_auto.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Thanh chỉnh tốc độ Auto Speed
        speed_frame = tk.Frame(left_column, bg="#f5f6f8")
        speed_frame.pack(fill=tk.X, pady=5)
        tk.Label(speed_frame, text="Auto speed", bg="#f5f6f8", font=("Arial", 9)).pack(side=tk.LEFT)
        self.speed_scale = tk.Scale(speed_frame, from_=100, to=1000, orient=tk.HORIZONTAL, bg="#f5f6f8", bd=0, highlightthickness=0)
        self.speed_scale.set(300)
        self.speed_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

        # Khung hiển thị đích mẫu (Goal Box ở dưới cùng bên trái)
        goal_box = tk.LabelFrame(left_column, text="Goal", bg="#ffffff", font=("Arial", 9))
        goal_box.pack(fill=tk.BOTH, expand=True, pady=(15, 5))
        
        goal_matrix_lbl = tk.Label(goal_box, text="1  2  3\n4  5  6\n7  8  _", font=("Courier", 12, "bold"), bg="#ffffff", justify=tk.LEFT, pady=15)
        goal_matrix_lbl.pack()

        # --- RIGHT COLUMN: Info Panel (Top) & Log Notebook (Bottom) ---
        right_column = tk.Frame(main_frame, bg="#f5f6f8")
        right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 1. Info Panel thiết kế dạng hiển thị văn bản y hệt trong ảnh
        info_frame = tk.Frame(right_column, bg="#f5f6f8")
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.stats = {
            "Step": tk.StringVar(value="-"),
            "Algorithm": tk.StringVar(value="-"),
            "Expanded": tk.StringVar(value="-"),
            "Action": tk.StringVar(value="-"),
            "Path cost": tk.StringVar(value="-"),
            "Depth": tk.StringVar(value="-"),
            "IDS limit": tk.StringVar(value="-"),
            "Frontier": tk.StringVar(value="-"),
            "Explored": tk.StringVar(value="-"),
            "Status": tk.StringVar(value="Ready.")
        }

        # Sắp xếp lưới nhãn thông tin
        keys = list(self.stats.keys())
        for idx, key in enumerate(keys):
            row = idx if idx < 9 else 8  # Đẩy Status xuống dòng cuối kéo dài
            col = 0 if idx < 9 else 0
            
            f = tk.Frame(info_frame, bg="#f5f6f8")
            if key == "Status":
                f.grid(row=9, column=0, columnspan=2, sticky="w", pady=4)
                tk.Label(f, text=f"{key}:", font=("Arial", 10, "bold"), bg="#f5f6f8", width=12, anchor="w").pack(side=tk.LEFT)
                tk.Label(f, textvariable=self.stats[key], font=("Arial", 10, "italic"), bg="#f5f6f8", fg="#475569").pack(side=tk.LEFT)
            else:
                f.grid(row=idx, column=0, sticky="w", pady=2)
                tk.Label(f, text=f"{key}:", font=("Arial", 10), bg="#f5f6f8", width=15, anchor="w").pack(side=tk.LEFT)
                tk.Label(f, textvariable=self.stats[key], font=("Arial", 10, "bold"), bg="#f5f6f8").pack(side=tk.LEFT)

        # 2. Log Panel dạng Tabbed Notebook (Children, Frontier, Explored, Step Log)
        self.notebook = ttk.Notebook(right_column)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_children = tk.Text(self.notebook, font=("Courier", 10), bg="white", bd=0)
        self.tab_frontier = tk.Text(self.notebook, font=("Courier", 10), bg="white", bd=0)
        self.tab_explored = tk.Text(self.notebook, font=("Courier", 10), bg="white", bd=0)
        self.tab_steplog = tk.Text(self.notebook, font=("Courier", 10), bg="white", bd=0)

        self.notebook.add(self.tab_children, text="Children")
        self.notebook.add(self.tab_frontier, text="Frontier")
        self.notebook.add(self.tab_explored, text="Explored")
        self.notebook.add(self.tab_steplog, text="Step Log")

    # --- LOGIC XỬ LÝ THUẬT TOÁN ---
    def update_grid(self):
        for i, val in enumerate(self.current_state):
            if val == 0:
                self.cells[i].config(text="", bg="#e2e8f0") # Màu xám nhạt cho ô trống giống mẫu
            else:
                self.cells[i].config(text=str(val), bg="#2563eb")

    def reset_puzzle(self):
        self.current_state = list(GOAL)
        self.path = []
        self.current_step_idx = 0
        self.update_grid()
        
        # Xóa trắng dữ liệu ở tất cả các Tab
        self.tab_children.delete('1.0', tk.END)
        self.tab_frontier.delete('1.0', tk.END)
        self.tab_explored.delete('1.0', tk.END)
        self.tab_steplog.delete('1.0', tk.END)
        
        for key, var in self.stats.items(): 
            var.set("-" if key != "Status" else "Ready.")
        Node._id_counter = 65

    def shuffle_puzzle(self):
        self.reset_puzzle()
        state = list(GOAL)
        # Giới hạn xáo trộn vừa phải để các thuật toán mù tìm kiếm nhanh chóng
        for _ in range(14): 
            neighbors = get_neighbors(tuple(state))
            state = list(random.choice(neighbors)[0])
        self.current_state = state
        self.update_grid()

    def write_to_tab(self, tab, text):
        """ Hàm bổ trợ cập nhật văn bản vào tab chỉ định an toàn từ luồng phụ """
        self.root.after(0, lambda: self._safe_write(tab, text))

    def _safe_write(self, tab, text):
        tab.insert(tk.END, text + "\n")
        tab.see(tk.END)

    def update_stat(self, key, value):
        self.root.after(0, lambda: self.stats[key].set(str(value)))

    def start_solve(self):
        algo = self.algo_var.get()
        start_state = tuple(self.current_state)
        Node._id_counter = 65 # Reset bảng chữ cái định danh Node
        
        try:
            max_d = int(self.max_depth_entry.get())
        except ValueError:
            max_d = 35

        # Làm sạch các Tab trước khi chạy
        self.tab_children.delete('1.0', tk.END)
        self.tab_frontier.delete('1.0', tk.END)
        self.tab_explored.delete('1.0', tk.END)
        self.tab_steplog.delete('1.0', tk.END)
        
        self.btn_run.config(state=tk.DISABLED)
        
        # Đẩy tiến trình tính toán thuật toán ra luồng riêng biệt
        threading.Thread(target=self.solve, args=(algo, start_state, max_d), daemon=True).start()

    def solve(self, algo, start, max_d):
        start_time = time.time()
        result_node = None
        explored = set()
        
        # Khởi tạo Node gốc ban đầu
        root_node = Node(start, cost=0, depth=0, h_cost=get_misplaced_tiles(start))

        if algo == "BFS":
            self.update_stat("Status", "Queue structure: First In First Out (FIFO)")
            queue = collections.deque([root_node])
            explored.add(start)
            
            while queue:
                node = queue.popleft()
                self.update_stat("Expanded", node.name)
                
                if node.state == GOAL:
                    result_node = node
                    break
                
                for state, action in get_neighbors(node.state):
                    if state not in explored and node.depth < max_d:
                        explored.add(state)
                        child = Node(state, node, action, node.cost + 1, node.depth + 1)
                        queue.append(child)
                        
                        # Ghi nhật ký tiến trình vào tab Children
                        log_text = f"{child.name} | parent={node.name} | action={action} | path_cost={child.cost} | depth={child.depth}\n" + format_state_matrix(state)
                        self.write_to_tab(self.tab_children, log_text)
                
                self.update_stat("Frontier", f"{len(queue)} node(s)")
                self.update_stat("Explored", f"{len(explored)} state(s)")

        elif algo == "DFS":
            self.update_stat("Status", "Stack structure: Last In First Out (LIFO)")
            stack = [root_node]
            explored.add(start)
            
            while stack:
                node = stack.pop()
                self.update_stat("Expanded", node.name)
                
                if node.state == GOAL:
                    result_node = node
                    break
                
                if node.depth < max_d:
                    for state, action in get_neighbors(node.state):
                        if state not in explored:
                            explored.add(state)
                            child = Node(state, node, action, node.cost + 1, node.depth + 1)
                            stack.append(child)
                            
                            log_text = f"{child.name} | parent={node.name} | action={action} | path_cost={child.cost} | depth={child.depth}\n" + format_state_matrix(state)
                            self.write_to_tab(self.tab_children, log_text)
                
                self.update_stat("Frontier", f"{len(stack)} node(s)")
                self.update_stat("Explored", f"{len(explored)} state(s)")

        elif algo == "UCS":
            self.update_stat("Status", "Priority queue: choose node with the smallest cumulative path cost.")
            # Lưu trữ Priority Queue dạng: (cost, id_counter, node)
            pq = [(root_node.cost, id(root_node), root_node)]
            
            while pq:
                cost, _, node = heapq.heappop(pq)
                self.update_stat("Expanded", node.name)
                
                if node.state == GOAL:
                    result_node = node
                    break
                
                if node.state not in explored:
                    explored.add(node.state)
                    self.write_to_tab(self.tab_explored, f"Explored State {node.name}:\n" + format_state_matrix(node.state))
                    
                    if node.depth < max_d:
                        for state, action in get_neighbors(node.state):
                            if state not in explored:
                                child = Node(state, node, action, node.cost + 1, node.depth + 1)
                                heapq.heappush(pq, (child.cost, id(child), child))
                                
                                # Định dạng log chi tiết y hệt hình mẫu yêu cầu
                                log_text = f"{child.name} | parent={node.name} | action={action} | path_cost={child.cost} | depth={child.depth}\n" + format_state_matrix(state)
                                self.write_to_tab(self.tab_children, log_text)
                
                self.update_stat("Frontier", f"{len(pq)} node(s)")
                self.update_stat("Explored", f"{len(explored)} state(s)")

        elif algo == "IDS":
            self.update_stat("Status", "Iterative Deepening Search: increasing depth limit progressively.")
            
            def dls(node, limit, visited_path):
                self.update_stat("Expanded", node.name)
                if node.state == GOAL: return node
                if limit <= 0: return None
                
                for state, action in get_neighbors(node.state):
                    if state not in visited_path:
                        visited_path.add(state)
                        child = Node(state, node, action, node.cost + 1, node.depth + 1)
                        
                        log_text = f"{child.name} | parent={node.name} | action={action} | depth={child.depth}\n" + format_state_matrix(state)
                        self.write_to_tab(self.tab_children, log_text)
                        
                        res = dls(child, limit - 1, visited_path)
                        if res: return res
                        visited_path.remove(state)
                return None

            for d in range(max_d + 1):
                self.update_stat("IDS limit", d)
                path_set = {start}
                res = dls(root_node, d, path_set)
                self.update_stat("Explored", f"{len(path_set)} state(s)")
                if res:
                    result_node = res
                    break

        elif algo == "A* (Misplaced)":
            self.update_stat("Status", "A* Search: Minimizing total estimated cost f(n) = g(n) + h(n)")
            pq = [(root_node.f_cost, id(root_node), root_node)]
            
            while pq:
                _, _, node = heapq.heappop(pq)
                self.update_stat("Expanded", node.name)
                
                if node.state == GOAL:
                    result_node = node
                    break
                
                if node.state not in explored:
                    explored.add(node.state)
                    self.write_to_tab(self.tab_explored, f"Explored {node.name}:\n" + format_state_matrix(node.state))
                    
                    if node.depth < max_d:
                        for state, action in get_neighbors(node.state):
                            if state not in explored:
                                h_val = get_misplaced_tiles(state)
                                child = Node(state, node, action, node.cost + 1, node.depth + 1, h_val)
                                heapq.heappush(pq, (child.f_cost, id(child), child))
                                
                                log_text = f"{child.name} | parent={node.name} | action={action} | path_cost={child.cost} | misplaced_tile_cost={child.h_cost} | depth={child.depth}\n" + format_state_matrix(state)
                                self.write_to_tab(self.tab_children, log_text)
                
                self.update_stat("Frontier", f"{len(pq)} node(s)")
                self.update_stat("Explored", f"{len(explored)} state(s)")

        # --- HIỂN THỊ KẾT QUẢ TÌM ĐƯỜNG ĐI LÊN TAB STEP LOG ---
        if result_node:
            self.path = []
            curr = result_node
            while curr:
                self.path.append(curr)
                curr = curr.parent
            self.path.reverse()
            
            self.current_step_idx = 0
            
            # Đổ dữ liệu các bước giải vào tab "Step Log"
            self.write_to_tab(self.tab_steplog, "=========================================")
            self.write_to_tab(self.tab_steplog, f" SUCCESS! Found path with {len(self.path)-1} steps.")
            self.write_to_tab(self.tab_steplog, "=========================================\n")
            
            for idx, n in enumerate(self.path):
                step_title = f"Step {idx}/{len(self.path)-1} - Node {n.name}"
                if n.action: step_title += f" (Move: {n.action})"
                else: step_title += " (START STATE)"
                
                self.write_to_tab(self.tab_steplog, f"👉 {step_title}")
                self.write_to_tab(self.tab_steplog, format_state_matrix(n.state))
            
            self.update_stat("Algorithm", algo)
            self.update_stat("Status", f"Solution found in {time.time()-start_time:.3f}s! Click 'Next Step' or 'Auto Run' to see animation.")
            
            # Kích hoạt xem bước đầu tiên tự động trên giao diện lưới
            self.next_step()
        else:
            self.update_stat("Status", "Failure: No solution found within depth limit.")
            self.root.after(0, lambda: messagebox.showinfo("Result", "No solution found within depth limit."))
        
        self.root.after(0, lambda: self.btn_run.config(state=tk.NORMAL))

    def next_step(self):
        if not self.path or self.current_step_idx >= len(self.path):
            return
        
        node = self.path[self.current_step_idx]
        self.current_state = list(node.state)
        self.update_grid()
        
        self.stats["Step"].set(f"{self.current_step_idx}/{len(self.path)-1}")
        self.stats["Action"].set(str(node.action) if node.action else "START")
        self.stats["Path cost"].set(str(node.cost))
        self.stats["Depth"].set(str(node.depth))
        
        self.current_step_idx += 1

    def prev_step(self):
        if not self.path or self.current_step_idx <= 1:
            return
        
        self.current_step_idx -= 2
        node = self.path[self.current_step_idx]
        self.current_state = list(node.state)
        self.update_grid()
        
        self.stats["Step"].set(f"{self.current_step_idx}/{len(self.path)-1}")
        self.stats["Action"].set(str(node.action) if node.action else "START")
        self.stats["Path cost"].set(str(node.cost))
        self.stats["Depth"].set(str(node.depth))
        
        self.current_step_idx += 1

    def toggle_auto(self):
        if self.is_running:
            self.is_running = False
            self.btn_auto.config(text="Auto Run")
        else:
            if not self.path:
                messagebox.showwarning("Warning", "Please run an algorithm to solve first!")
                return
            self.is_running = True
            self.btn_auto.config(text="Stop Auto")
            self.auto_run_loop()

    def auto_run_loop(self):
        if self.is_running and self.current_step_idx < len(self.path):
            self.next_step()
            delay = self.speed_scale.get()
            self.root.after(delay, self.auto_run_loop)
        else:
            self.is_running = False
            self.btn_auto.config(text="Auto Run")

if __name__ == "__main__":
    root = tk.Tk()
    # Thiết lập giao diện nút bấm phẳng & hiện đại theo phong cách mới
    style = ttk.Style()
    style.configure("TNotebook", background="#f5f6f8")
    style.configure("TNotebook.Tab", padding=[12, 4], font=("Arial", 9))
    
    app = EightPuzzleGUI(root)
    root.mainloop()