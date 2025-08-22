# Run everything with:
# 
# for thr in 0 0.1 1 10 100; do for proc in tt tta ttee ttev tth; do python3 plot_dim6top_tables.py ${proc} $thr; done; done
#
# ------------------ 

import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys

def parse_latex_scientific(s):
    if isinstance(s, str):
        # Match patterns like $-3.6 \times 10^{2}$ or $1.6 \times 10^{-2}$
        match = re.match(r"\$?(-?[\d\.]+)\s*\\times\s*10\^\{(-?\d+)\}\$?", s)
        if match:
            base = float(match.group(1))
            exponent = int(match.group(2))
            return base * 10**exponent
        else:
            return s

# --- Parse LaTeX into DataFrame ---
def parse_latex_table(filename):
    with open(filename, "r", encoding="utf-8") as f:
        latex = f.read()

    # Isolate tabular if present
    m = re.search(r'\\begin{tabular}.*?\\end{tabular}', latex, re.S)
    content = m.group(0) if m else latex

    # Strip begin/end lines
    content = re.sub(r'\\begin{tabular}{.*?}|\\end{tabular}', '', content)

    # Replace \ccc{tag}{name}{...} → $C_{name}^{tag}$
    ccc_pat = re.compile(r'\$?\s*\\ccc\{([^}]*)\}\{([^}]*)\}(?:\{([^}]*)\})?\s*\$?')
    def repl_ccc(m):
        tag = m.group(1).strip()
        name = m.group(2).strip()
        return rf"$C_{{{name}}}^{{{tag}}}$"
    content = ccc_pat.sub(repl_ccc, content)

    # Cleanup
    content = re.sub(r'\\hline', '', content)   # remove hline
    content = re.sub(r'%.*', '', content)       # remove comments

    # Split into rows and columns
    rows = [r.strip() for r in content.split('\\\\') if '&' in r]
    data = [[c.strip() for c in row.split('&')] for row in rows]

    # Build DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])

    # Convert numeric entries
    for col in df.columns[1:]:
        df[col] = df[col].apply(parse_latex_scientific)

        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(r'[^\d\.\-eE+]', '', regex=True),
            errors="coerce"
        ) 

    df = df.fillna( 0.0 )
    return df

def filter_df(df, param):

    name_block = df.iloc[:, 0]
    numeric_block = df.iloc[:, 1:]
    mask = numeric_block.abs() > param
    
    # keep only rows with at least one True
    rows = mask.any(axis=1)
    
    # keep only columns with at least one True
    cols = mask.any(axis=0)
    filtered_df = pd.concat( [ name_block[rows], numeric_block.loc[rows, cols] ], axis = 1 )
    
    return filtered_df


def plot_with_groups(df, proc, thr, title):
    """
    df: DataFrame with first col = operator labels, rest = numeric data
    threshold: cutoff for filtering numeric values
    groups: dict mapping group name -> list of operators (row labels)
    """

    values = df.apply(pd.to_numeric, errors="coerce")  # convert numeric part

    # Extract labels and numeric data
    labels_y = df.iloc[:, 0].tolist()
    labels_x = list(df.columns[1:])
    numeric = df.iloc[:, 1:].to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(12, 8))
    im = ax.imshow(numeric, cmap="viridis", aspect='auto')
    plt.colorbar(im, ax=ax, label="value", drawedges = True, norm = 'log')

    ax.set_xticks(np.arange(len(labels_x)))
    ax.set_xticklabels(labels_x, rotation=90)
    ax.set_yticks(np.arange(len(labels_y)))
    ax.set_yticklabels(labels_y)

    ax.set_title( title )
    plt.tight_layout()

    # Annotate bins with numbers
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            val = values.iloc[i, j]
            if not np.isnan(val) and val != 0:
                ax.text(j-1, i, f"{val:.2e}", ha="center", va="center", color="r", fontsize=8)


    import os
    os.makedirs( f"dim6top_tables/{proc}/", exist_ok = True )
    plt.savefig(f"dim6top_tables/{proc}/quad_dependence_thr{thr}.png")
    plt.savefig(f"dim6top_tables/{proc}/quad_dependence_thr{thr}.pdf")

# ===============================
# Example usage
# ===============================

proc = sys.argv[1]
thr = float(sys.argv[2])

df = parse_latex_table( f"dim6top_tables/arxiv/squared_{proc}.tex" )

# Apply a cutoff if desired
df_cut = filter_df(df, param=thr)

# Plot
plot_with_groups(df, proc, thr = "None", title=f"Quadratic dependence for {proc} from arXiv.1802.07237. No cut on table.")
plot_with_groups(df_cut, proc, thr = thr, title=f"Quadratic dependence for {proc} from arXiv.1802.07237. Threshold: {thr} (absolute value)")

