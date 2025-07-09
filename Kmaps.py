import tkinter as tk
from tkinter import messagebox
from itertools import product
from sympy import symbols, SOPform, POSform


def gray_code(n):
    if n == 0:
        return ['']
    first = gray_code(n - 1)
    second = first[::-1]
    return ['0' + code for code in first] + ['1' + code for code in second]


def parse_input_list(entry_text):
    try:
        return [int(x.strip()) for x in entry_text.split(',') if x.strip() != '']
    except ValueError:
        return None


def get_adjacent_positions(i, j, num_rows, num_cols):
    return [
        ((i - 1) % num_rows, j),
        ((i + 1) % num_rows, j),
        (i, (j - 1) % num_cols),
        (i, (j + 1) % num_cols),
    ]


def get_groupings(grid, rows, cols):
    num_rows = len(rows)
    num_cols = len(cols)
    visited = [[False] * num_cols for _ in range(num_rows)]
    groups = []

    def dfs(r, c, group):
        if visited[r][c] or grid[r][c] == 0:
            return
        visited[r][c] = True
        group.append((r, c))
        for nr, nc in get_adjacent_positions(r, c, num_rows, num_cols):
            if not visited[nr][nc] and grid[nr][nc] in (1, 'X'):
                dfs(nr, nc, group)

    for i in range(num_rows):
        for j in range(num_cols):
            if not visited[i][j] and grid[i][j] in (1, 'X'):
                group = []
                dfs(i, j, group)
                if any(grid[r][c] == 1 for r, c in group):
                    groups.append(group)
    return groups


def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=8, **kwargs):
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def bool_expr_to_literal(expr, var_names):
    expr_str = str(expr)
    for var in var_names:
        expr_str = expr_str.replace(f"~{var}", f"{var}'")
    expr_str = expr_str.replace(" & ", ".").replace(" | ", " + ")
    return expr_str


def generate_kmap_with_expr_output(min_entry, dc_entry, var_entry, form_var, canvas, expr_text):
    canvas.delete("all")
    expr_text.delete("1.0", tk.END)

    minterms = parse_input_list(min_entry.get())
    dontcares = parse_input_list(dc_entry.get())

    if minterms is None or dontcares is None:
        messagebox.showerror("Error", "Please enter valid comma-separated numbers.")
        return

    try:
        num_vars = int(var_entry.get())
    except ValueError:
        messagebox.showerror("Error", "Number of variables must be an integer.")
        return

    if not (2 <= num_vars <= 4):
        messagebox.showerror("Error", "Only 2 to 4 variables supported.")
        return

    max_index = 2 ** num_vars - 1
    if any(x > max_index for x in minterms + dontcares):
        messagebox.showerror("Error", f"Indices must be ≤ {max_index} for {num_vars} variables.")
        return

    if not minterms:
        messagebox.showerror("Error", "At least one minterm is required.")
        return

    # Variables
    var_symbols = symbols(' '.join(['A', 'B', 'C', 'D'][:num_vars]))
    form_choice = form_var.get()

    if form_choice == "SOP":
        simplified_expr = SOPform(var_symbols, minterms, dontcares)
    else:
        # POS form needs maxterms, which are NOT the minterms or don't-cares
        all_terms = set(range(2**num_vars))
        maxterms = sorted(list(all_terms - set(minterms) - set(dontcares)))
        simplified_expr = POSform(var_symbols, maxterms, dontcares)

    simplified_str = bool_expr_to_literal(simplified_expr, [str(v) for v in var_symbols])
    expr_text.insert(tk.END, f"Simplified {form_choice} Expression:\n{simplified_str}\n")

    # K-Map layout
    row_bits = num_vars // 2
    col_bits = num_vars - row_bits
    rows = gray_code(row_bits)
    cols = gray_code(col_bits)

    total = 2 ** num_vars
    truth_table = {}
    for i in range(total):
        bits = tuple(int(b) for b in f"{i:0{num_vars}b}")
        if i in minterms:
            truth_table[bits] = 1
        elif i in dontcares:
            truth_table[bits] = 'X'
        else:
            truth_table[bits] = 0

    grid = []
    for r in rows:
        row = []
        for c in cols:
            bits = tuple(int(b) for b in r + c)
            row.append(truth_table.get(bits, 0))
        grid.append(row)

    groups = get_groupings(grid, rows, cols)

    # Draw K-Map
    cell_size = 50
    margin = 50
    canvas_width = margin + len(cols) * cell_size + 10
    canvas_height = margin + len(rows) * cell_size + 10
    canvas.config(width=canvas_width, height=canvas_height)

    # Headers
    for j, col in enumerate(cols):
        x = margin + j * cell_size + cell_size / 2
        canvas.create_text(x, margin / 2, text=col, font=("Courier", 12, "bold"))
    for i, row in enumerate(rows):
        y = margin + i * cell_size + cell_size / 2
        canvas.create_text(margin / 2, y, text=row, font=("Courier", 12, "bold"))

    # Cells
    for i, row in enumerate(rows):
        for j, col in enumerate(cols):
            val = grid[i][j]
            x0 = margin + j * cell_size
            y0 = margin + i * cell_size
            x1 = x0 + cell_size
            y1 = y0 + cell_size
            fill_color = "white"
            if val == 1:
                fill_color = "lightgreen"
            elif val == 'X':
                fill_color = "yellow"
            canvas.create_rectangle(x0, y0, x1, y1, fill=fill_color, outline="black")
            canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=str(val), font=("Courier", 14))

    # Groupings
    colors = ['red', 'blue', 'green', 'purple', 'orange']
    for idx, group in enumerate(groups):
        color = colors[idx % len(colors)]
        xs, ys = [], []
        for r, c in group:
            x0 = margin + c * cell_size
            y0 = margin + r * cell_size
            x1 = x0 + cell_size
            y1 = y0 + cell_size
            xs.extend([x0, x1])
            ys.extend([y0, y1])
        if xs and ys:
            x0 = min(xs) + 5
            y0 = min(ys) + 5
            x1 = max(xs) - 5
            y1 = max(ys) - 5
            create_rounded_rectangle(canvas, x0, y0, x1, y1, radius=6, outline=color, width=2, fill='')


def run_gui():
    root = tk.Tk()
    root.title("K-Map Simplifier")

    tk.Label(root, text="Number of Variables (2–4):").grid(row=0, column=0, sticky='e')
    var_entry = tk.Entry(root, width=5)
    var_entry.insert(0, "4")
    var_entry.grid(row=0, column=1, sticky='w')

    tk.Label(root, text="Minterms (Σm):").grid(row=1, column=0, sticky='e')
    min_entry = tk.Entry(root, width=40)
    min_entry.insert(0, "0,2,5,7,8,10,13,15")
    min_entry.grid(row=1, column=1)

    tk.Label(root, text="Don't-cares (Σd):").grid(row=2, column=0, sticky='e')
    dc_entry = tk.Entry(root, width=40)
    dc_entry.insert(0, "1,3")
    dc_entry.grid(row=2, column=1)

    tk.Label(root, text="Simplification Form:").grid(row=3, column=0, sticky='e')
    form_var = tk.StringVar(value="SOP")
    form_menu = tk.OptionMenu(root, form_var, "SOP", "POS")
    form_menu.grid(row=3, column=1, sticky='w')

    canvas = tk.Canvas(root, bg='white', width=500, height=400)
    canvas.grid(row=5, column=0, columnspan=2, pady=10)

    expr_text = tk.Text(root, height=4, width=60)
    expr_text.grid(row=6, column=0, columnspan=2)

    run_button = tk.Button(
        root, text="Simplify & Show K-Map",
        command=lambda: generate_kmap_with_expr_output(min_entry, dc_entry, var_entry, form_var, canvas, expr_text),
        bg="lightblue", font=("Arial", 12, "bold")
    )
    run_button.grid(row=4, column=0, columnspan=2, pady=10)

    root.mainloop()


if __name__ == "__main__":
    run_gui()
