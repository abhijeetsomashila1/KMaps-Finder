import tkinter as tk
from tkinter import messagebox
from itertools import product
from sympy import symbols, SOPform, POSform

THEME = {
    "bg": "#f0f8ff",
    "fg": "#003366",
    "entry_bg": "#ffffff",
    "entry_fg": "#003366",
    "canvas_bg": "#ffffff",
    "cell_fill": "#d0ecff",
    "text_fill": "#003366",
    "cell_on": "#66cc66",    
    "cell_dc": "#cce5ff",     
    "cell_off": "#d0ecff",    
    "outline": "#007acc",
    "button_bg": "#3399ff",
    "button_fg": "white"
}


def gray_code(n):
    if n == 0:
        return ['']
    prev = gray_code(n - 1)
    return ['0' + x for x in prev] + ['1' + x for x in reversed(prev)]


def parse_input_list(text):
    try:
        return [int(x.strip()) for x in text.split(',') if x.strip()]
    except:
        return None


def bool_expr_to_literal(expr, var_names):
    s = str(expr)
    for var in var_names:
        s = s.replace(f"~{var}", f"{var}'")
    return s.replace(" & ", ".").replace(" | ", " + ")


def get_groupings(grid, rows, cols):
    nrows, ncols = len(rows), len(cols)
    visited = [[False]*ncols for _ in range(nrows)]
    groups = []

    def dfs(r, c, group):
        if visited[r][c] or grid[r][c] == 0:
            return
        visited[r][c] = True
        group.append((r, c))
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = (r + dr) % nrows, (c + dc) % ncols
            if not visited[nr][nc] and grid[nr][nc] in (1, 'X'):
                dfs(nr, nc, group)

    for i in range(nrows):
        for j in range(ncols):
            if not visited[i][j] and grid[i][j] in (1, 'X'):
                group = []
                dfs(i, j, group)
                if any(grid[r][c] == 1 for r, c in group):
                    groups.append(group)
    return groups


class KMapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("K-Maps Simplifier Project")
        self.build_ui()

    def build_ui(self):
        self.widgets = {}
        self.root.configure(bg=THEME["bg"])
        font = ("Segoe UI", 11)

        row = 0
        self._label("Variables (2-4):", row)
        self.widgets["var_entry"] = self._entry("4", row)

        row += 1
        self._label("Minterms Σm:", row)
        self.widgets["min_entry"] = self._entry("0,2,5,7,8,10,13,15", row)

        row += 1
        self._label("Don't-cares Σd:", row)
        self.widgets["dc_entry"] = self._entry("1,3", row)

        row += 1
        self._label("Form:", row)
        self.widgets["form_var"] = tk.StringVar(value="SOP")
        self.widgets["form_menu"] = tk.OptionMenu(self.root, self.widgets["form_var"], "SOP", "POS")
        self.widgets["form_menu"].grid(row=row, column=1, sticky="w", padx=5, pady=5)

        row += 1
        self.widgets["run_btn"] = tk.Button(
            self.root, text="Simplify & Show K-Map", command=self.run_simplify,
            font=("Segoe UI", 12, "bold")
        )
        self.widgets["run_btn"].grid(row=row, column=0, columnspan=2, pady=10)

        row += 1
        self.widgets["canvas"] = tk.Canvas(self.root, width=600, height=400, highlightthickness=0)
        self.widgets["canvas"].grid(row=row, column=0, columnspan=2, padx=10, pady=10)

        row += 1
        self.widgets["output"] = tk.Text(self.root, height=3, width=60, font=font, relief=tk.FLAT)
        self.widgets["output"].grid(row=row, column=0, columnspan=2, pady=5)

        self.apply_theme()

    def _label(self, text, row):
        lbl = tk.Label(self.root, text=text, font=("Segoe UI", 11))
        lbl.grid(row=row, column=0, sticky="e", padx=5, pady=5)
        self.widgets[f"label_{row}"] = lbl

    def _entry(self, default, row):
        entry = tk.Entry(self.root, width=30)
        entry.insert(0, default)
        entry.grid(row=row, column=1)
        return entry

    def apply_theme(self):
        th = THEME
        self.root.configure(bg=th["bg"])
        for widget in self.widgets.values():
            if isinstance(widget, tk.Label):
                widget.config(bg=th["bg"], fg=th["fg"])
            elif isinstance(widget, tk.Entry):
                widget.config(bg=th["entry_bg"], fg=th["entry_fg"], insertbackground=th["entry_fg"])
            elif isinstance(widget, tk.OptionMenu):
                widget.config(bg=th["entry_bg"], fg=th["entry_fg"], highlightbackground=th["entry_fg"])
                widget["menu"].config(bg=th["entry_bg"], fg=th["entry_fg"])
            elif isinstance(widget, tk.Button):
                widget.config(bg=th["button_bg"], fg=th["button_fg"], activebackground=th["outline"])
            elif isinstance(widget, tk.Canvas):
                widget.config(bg=th["canvas_bg"])
            elif isinstance(widget, tk.Text):
                widget.config(bg=th["entry_bg"], fg=th["entry_fg"])

    def run_simplify(self):
        th = THEME
        canvas = self.widgets["canvas"]
        canvas.delete("all")
        self.widgets["output"].delete("1.0", tk.END)

        try:
            num_vars = int(self.widgets["var_entry"].get())
            if num_vars < 2 or num_vars > 4:
                raise ValueError
        except:
            messagebox.showerror("Error", "Number of variables must be between 2 and 4")
            return

        minterms = parse_input_list(self.widgets["min_entry"].get())
        dontcares = parse_input_list(self.widgets["dc_entry"].get())
        if minterms is None or dontcares is None:
            messagebox.showerror("Error", "Invalid minterm/don't care input.")
            return

        form = self.widgets["form_var"].get()
        variables = symbols(' '.join(['A', 'B', 'C', 'D'][:num_vars]))

        if form == "SOP":
            expr = SOPform(variables, minterms, dontcares)
        else:
            all_vals = set(range(2 ** num_vars))
            maxterms = sorted(list(all_vals - set(minterms) - set(dontcares)))
            expr = POSform(variables, maxterms, dontcares)

        simplified = bool_expr_to_literal(expr, [str(v) for v in variables])
        self.widgets["output"].insert(tk.END, f"Simplified {form} Expression:\n{simplified}")

        row_bits = num_vars // 2
        col_bits = num_vars - row_bits
        rows = gray_code(row_bits)
        cols = gray_code(col_bits)

        table = {}
        for i in range(2 ** num_vars):
            bits = tuple(int(b) for b in f"{i:0{num_vars}b}")
            if i in minterms:
                table[bits] = 1
            elif i in dontcares:
                table[bits] = 'X'
            else:
                table[bits] = 0

        grid = []
        for r in rows:
            row = []
            for c in cols:
                bits = tuple(int(b) for b in r + c)
                row.append(table.get(bits, 0))
            grid.append(row)

        groups = get_groupings(grid, rows, cols)
        cell_size = 50
        margin = 50
        canvas.config(width=margin + len(cols)*cell_size, height=margin + len(rows)*cell_size)

        for j, col in enumerate(cols):
            canvas.create_text(margin + j*cell_size + cell_size/2, margin/2,
                               text=col, fill=th["text_fill"], font=("Segoe UI", 12, "bold"))
        for i, row in enumerate(rows):
            canvas.create_text(margin/2, margin + i*cell_size + cell_size/2,
                               text=row, fill=th["text_fill"], font=("Segoe UI", 12, "bold"))

        index_map = {}
        for i, r in enumerate(rows):
            for j, c in enumerate(cols):
                bits = tuple(int(b) for b in r + c)
                index = int(''.join(map(str, bits)), 2)
                index_map[(i, j)] = index

        for i in range(len(rows)):
            for j in range(len(cols)):
                x0 = margin + j * cell_size
                y0 = margin + i * cell_size
                x1 = x0 + cell_size
                y1 = y0 + cell_size
                val = grid[i][j]
                fill = th["cell_on"] if val == 1 else th["cell_dc"] if val == 'X' else th["cell_off"]
                canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline=th["outline"], width=2)
                canvas.create_text((x0+x1)/2, (y0+y1)/2, text=str(val),
                                   fill=th["text_fill"], font=("Segoe UI", 12, "bold"))
                canvas.create_text(x0+6, y0+6, text=str(index_map[(i,j)]),
                                   anchor="nw", fill="#888888", font=("Segoe UI", 8, "normal"))

        for group in groups:
            if not group:
                continue
            xs = [margin + j * cell_size for i, j in group]
            ys = [margin + i * cell_size for i, j in group]
            if xs and ys:
                x0 = min(xs) + 5
                y0 = min(ys) + 5
                x1 = max(xs) + cell_size - 5
                y1 = max(ys) + cell_size - 5
                canvas.create_rectangle(x0, y0, x1, y1, outline=th["outline"], width=3)


if __name__ == "__main__":
    root = tk.Tk()
    app = KMapApp(root)
    root.mainloop()
