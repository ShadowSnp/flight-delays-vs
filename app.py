# -*- coding: utf-8 -*-
"""
Flight Delay Analyzer – Visual Studio Edition
Clean light theme  |  Microsoft Fluent-inspired design
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinterdnd2 import TkinterDnD, DND_FILES

matplotlib.rcParams.update({
    "font.family":      "Segoe UI",
    "axes.spines.top":  False,
    "axes.spines.right":False,
})

# ── Palette  (light / Microsoft Fluent) ───────────────────────────────────────
C_BG        = "#f3f3f3"
C_SURFACE   = "#ffffff"
C_SURFACE2  = "#fafafa"
C_PRIMARY   = "#0078d4"   # Microsoft blue
C_PRIMARY2  = "#005a9e"
C_ACCENT    = "#00b4d8"
C_SUCCESS   = "#107c10"
C_WARNING   = "#d83b01"
C_TEXT      = "#201f1e"
C_SUBTEXT   = "#605e5c"
C_BORDER    = "#d2d0ce"
C_HOVER     = "#e1efff"
C_STRIPE    = "#f0f6ff"

BAR_PALETTE = ["#0078d4","#00b4d8","#107c10","#d83b01","#8764b8"]

DELAY_COLS  = ["carrier_delay","weather_delay","nas_delay",
               "security_delay","late_aircraft_delay"]
DELAY_LBLS  = ["Carrier","Weather","NAS","Security","Late Aircraft"]
MONTH_NAMES = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
               7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def load_file(path: str) -> pd.DataFrame:
    path = path.strip().strip("{}")
    ext  = os.path.splitext(path)[1].lower()
    return pd.read_excel(path) if ext in (".xlsx",".xls") else pd.read_csv(path)


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df[df["arr_cancelled"] == 0].copy()
    for c in DELAY_COLS + ["arr_delay"]:
        if c in df2.columns:
            df2[c] = df2[c].fillna(0)
    return df2


def _trend_series(df):
    """Return (x_labels, y_values, xlabel) for the trend line."""
    has_year = "year" in df.columns and df["year"].nunique() > 1
    if has_year:
        g = df.groupby("year")["arr_delay"].mean().reset_index()
        return g["year"].astype(str).tolist(), g["arr_delay"].tolist(), "Year"
    if df["month"].nunique() > 1:
        g = df.groupby("month")["arr_delay"].mean().reset_index()
        return ([MONTH_NAMES.get(int(m), str(m)) for m in g["month"]],
                g["arr_delay"].tolist(), "Month")
    g = (df.groupby("carrier_name")["arr_delay"]
           .mean().nlargest(10).reset_index())
    return g["carrier_name"].tolist(), g["arr_delay"].tolist(), "Carrier (top 10)"


# ═══════════════════════════════════════════════════════════════════════════════
# CHART FACTORIES
# ═══════════════════════════════════════════════════════════════════════════════

def _base_fig(w=7.2, h=4):
    fig, ax = plt.subplots(figsize=(w, h), facecolor=C_SURFACE)
    ax.set_facecolor(C_SURFACE2)
    ax.tick_params(colors=C_SUBTEXT, labelsize=8)
    for sp in ax.spines.values():
        sp.set_edgecolor(C_BORDER)
    return fig, ax


def chart_bar(df):
    totals = df[DELAY_COLS].sum()
    fig, ax = _base_fig()
    bars = ax.bar(DELAY_LBLS, totals/1e6, color=BAR_PALETTE,
                  edgecolor="white", linewidth=0.8, zorder=3)
    ax.yaxis.grid(True, color=C_BORDER, linewidth=0.6, zorder=0)
    for bar, v in zip(bars, totals):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.01,
                f"{v/1e6:.1f}M", ha="center", va="bottom",
                fontsize=8, color=C_SUBTEXT, fontweight="bold")
    ax.set_title("Total Delay by Cause", color=C_TEXT,
                 fontsize=13, fontweight="bold", pad=10)
    ax.set_ylabel("Minutes (millions)", color=C_SUBTEXT, fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.1f}M"))
    fig.tight_layout(pad=1.4)
    return fig


def chart_hist(df):
    arr = df["arr_delay"].dropna()
    fig, ax = _base_fig()
    n, bins, patches = ax.hist(arr, bins=40, color=C_PRIMARY,
                                edgecolor="white", linewidth=0.4, zorder=3)
    for p in patches:
        p.set_alpha(0.85)
    mean_v = arr.mean()
    ax.axvline(mean_v, color=C_WARNING, linestyle="--",
               linewidth=1.6, label=f"Mean  {mean_v:,.0f} min", zorder=4)
    ax.yaxis.grid(True, color=C_BORDER, linewidth=0.5, zorder=0)
    ax.set_title("ArrDelay Distribution", color=C_TEXT,
                 fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel("Total arrival delay (minutes)", color=C_SUBTEXT, fontsize=9)
    ax.set_ylabel("Number of groups", color=C_SUBTEXT, fontsize=9)
    ax.legend(fontsize=9, framealpha=0.6)
    fig.tight_layout(pad=1.4)
    return fig


def chart_scatter(df):
    s = df[["arr_flights","arr_delay"]].dropna()
    fig, ax = _base_fig()
    ax.scatter(s["arr_flights"], s["arr_delay"],
               alpha=0.40, s=16, color=C_ACCENT,
               edgecolors="none", zorder=3)
    ax.yaxis.grid(True, color=C_BORDER, linewidth=0.5, zorder=0)
    ax.xaxis.grid(True, color=C_BORDER, linewidth=0.5, zorder=0)
    ax.set_title("Flight Volume vs Arrival Delay", color=C_TEXT,
                 fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel("Number of flights (arr_flights)", color=C_SUBTEXT, fontsize=9)
    ax.set_ylabel("Total arrival delay (min)", color=C_SUBTEXT, fontsize=9)
    corr = s["arr_flights"].corr(s["arr_delay"])
    ax.text(0.97, 0.05, f"r = {corr:.3f}", transform=ax.transAxes,
            ha="right", color=C_SUBTEXT, fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", facecolor=C_STRIPE, alpha=0.8))
    fig.tight_layout(pad=1.4)
    return fig


def chart_line(df):
    xlbls, yvals, xlabel = _trend_series(df)
    fig, ax = _base_fig()
    xi = list(range(len(xlbls)))
    ax.plot(xi, yvals, color=C_PRIMARY, linewidth=2.4,
            marker="o", markersize=7, markerfacecolor="white",
            markeredgewidth=2, markeredgecolor=C_PRIMARY, zorder=4)
    ax.fill_between(xi, yvals, alpha=0.08, color=C_PRIMARY, zorder=2)
    ax.yaxis.grid(True, color=C_BORDER, linewidth=0.6, zorder=0)
    ax.set_xticks(xi)
    ax.set_xticklabels(xlbls, rotation=20, ha="right", fontsize=8)
    ax.set_title("Average Arrival Delay Trend", color=C_TEXT,
                 fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel(xlabel, color=C_SUBTEXT, fontsize=9)
    ax.set_ylabel("Average delay (min)", color=C_SUBTEXT, fontsize=9)
    fig.tight_layout(pad=1.4)
    return fig


def chart_summary(df):
    """4-panel summary figure saved to output/."""
    fig, axes = plt.subplots(2, 2, figsize=(13, 7.5), facecolor=C_SURFACE)
    fig.suptitle("Flight Delay Analysis — Summary",
                 color=C_TEXT, fontsize=15, fontweight="bold", y=1.01)

    totals = df[DELAY_COLS].sum()
    arr    = df["arr_delay"].dropna()
    s      = df[["arr_flights","arr_delay"]].dropna()
    xl, yv, xlabel = _trend_series(df)
    xi = list(range(len(xl)))

    for ax in axes.flat:
        ax.set_facecolor(C_SURFACE2)
        ax.tick_params(colors=C_SUBTEXT, labelsize=7)
        for sp in ax.spines.values():
            sp.set_edgecolor(C_BORDER)
        ax.yaxis.grid(True, color=C_BORDER, linewidth=0.5, zorder=0)

    # bar
    axes[0,0].bar(DELAY_LBLS, totals/1e6, color=BAR_PALETTE,
                  edgecolor="white", zorder=3)
    axes[0,0].set_title("Delay by Cause", color=C_TEXT,
                         fontsize=10, fontweight="bold")
    axes[0,0].set_ylabel("Millions min", color=C_SUBTEXT, fontsize=8)
    axes[0,0].tick_params(axis="x", labelsize=7)

    # histogram
    axes[0,1].hist(arr, bins=30, color=C_PRIMARY, edgecolor="white",
                   alpha=0.85, zorder=3)
    axes[0,1].axvline(arr.mean(), color=C_WARNING, linestyle="--", linewidth=1.4)
    axes[0,1].set_title("ArrDelay Distribution", color=C_TEXT,
                         fontsize=10, fontweight="bold")
    axes[0,1].set_xlabel("Minutes", color=C_SUBTEXT, fontsize=8)

    # line
    axes[1,0].plot(xi, yv, color=C_PRIMARY, linewidth=2, marker="o",
                   markersize=5, markerfacecolor="white",
                   markeredgewidth=1.5, markeredgecolor=C_PRIMARY, zorder=4)
    axes[1,0].fill_between(xi, yv, alpha=0.08, color=C_PRIMARY, zorder=2)
    axes[1,0].set_xticks(xi)
    axes[1,0].set_xticklabels(xl, rotation=20, ha="right", fontsize=6)
    axes[1,0].set_title("Delay Trend", color=C_TEXT,
                         fontsize=10, fontweight="bold")
    axes[1,0].set_ylabel("Avg delay (min)", color=C_SUBTEXT, fontsize=8)

    # scatter
    axes[1,1].scatter(s["arr_flights"], s["arr_delay"],
                      alpha=0.30, s=8, color=C_ACCENT, edgecolors="none", zorder=3)
    axes[1,1].xaxis.grid(True, color=C_BORDER, linewidth=0.5, zorder=0)
    axes[1,1].set_title("Flights vs Delay", color=C_TEXT,
                         fontsize=10, fontweight="bold")
    axes[1,1].set_xlabel("arr_flights", color=C_SUBTEXT, fontsize=8)
    axes[1,1].set_ylabel("ArrDelay (min)", color=C_SUBTEXT, fontsize=8)

    fig.tight_layout()
    return fig


def get_stats(df) -> str:
    cause_totals = df[DELAY_COLS].sum()
    top_idx      = cause_totals.values.argmax()
    top_lbl      = DELAY_LBLS[top_idx]
    xl, yv, _    = _trend_series(df)
    worst_lbl    = xl[yv.index(max(yv))]
    corr         = df["arr_flights"].corr(df["arr_delay"])

    lines = [
        f"Period with highest avg delay : {worst_lbl}  ({max(yv):.1f} min)",
        f"Top cause of delay            : {top_lbl}  ({cause_totals.iloc[top_idx]:,.0f} min total)",
        "",
        "Delay breakdown (total minutes):",
    ]
    for lbl, col in zip(DELAY_LBLS, DELAY_COLS):
        lines.append(f"  {lbl:<18}: {cause_totals[col]:>12,.0f} min")
    lines += [
        "",
        f"Pearson r (flights ↔ delay)   : {corr:.3f}",
        ("→ Busier routes tend to have more delays."
         if corr > 0.3 else "→ Weak link between flight volume and delay."),
    ]
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# GUI
# ═══════════════════════════════════════════════════════════════════════════════

class App(TkinterDnD.Tk):

    def __init__(self):
        super().__init__()
        self.title("Flight Delay Analyzer — VS Edition")
        self.configure(bg=C_BG)
        self.geometry("1200x780")
        self.minsize(960, 620)
        self.df = None
        self._canvas_ref = None
        self._active_btn = None
        self._build()

    # ── root layout ───────────────────────────────────────────────────────────
    def _build(self):
        self._build_titlebar()
        body = tk.Frame(self, bg=C_BG)
        body.pack(fill="both", expand=True)
        self._build_sidebar(body)
        self._build_main(body)

    # ── custom title bar strip ────────────────────────────────────────────────
    def _build_titlebar(self):
        bar = tk.Frame(self, bg=C_PRIMARY, height=46)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        icon = tk.Label(bar, text="✈", bg=C_PRIMARY, fg="white",
                        font=("Segoe UI", 18))
        icon.pack(side="left", padx=(14, 6))

        tk.Label(bar, text="Flight Delay Analyzer",
                 bg=C_PRIMARY, fg="white",
                 font=("Segoe UI", 13, "bold")).pack(side="left")

        tk.Label(bar, text="Visual Studio Edition",
                 bg=C_PRIMARY, fg="#cce4f6",
                 font=("Segoe UI", 9)).pack(side="left", padx=(8, 0))

    # ── left sidebar ──────────────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        side = tk.Frame(parent, bg=C_SURFACE, width=240,
                        relief="flat", bd=0,
                        highlightbackground=C_BORDER, highlightthickness=1)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        # section label
        tk.Label(side, text="DATA SOURCE", bg=C_SURFACE, fg=C_SUBTEXT,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=16, pady=(16,4))

        self._build_upload(side)

        tk.Label(side, text="ANALYSIS", bg=C_SURFACE, fg=C_SUBTEXT,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=16, pady=(20,4))

        tasks = [
            ("📊  Delay Causes",      self._t3),
            ("📈  ArrDelay Histogram", self._t4),
            ("🔵  Flights vs Delay",   self._t5),
            ("📉  Delay Trend",        self._t6),
            ("📋  Statistics",         self._t7),
            ("💾  Save Summary PNG",   self._t8),
        ]
        self._task_btns = []
        for label, cmd in tasks:
            b = tk.Button(side, text=label, anchor="w",
                          bg=C_SURFACE, fg=C_TEXT,
                          font=("Segoe UI", 9),
                          relief="flat", bd=0, padx=16, pady=8,
                          activebackground=C_HOVER, cursor="hand2",
                          command=lambda c=cmd, b_=None: self._run_task(c, b_))
            b.pack(fill="x")
            b.configure(command=lambda c=cmd, btn=b: self._run_task(c, btn))
            self._task_btns.append(b)

        # status strip at bottom of sidebar
        self.status_lbl = tk.Label(side, text="No file loaded",
                                   bg=C_SURFACE, fg=C_SUBTEXT,
                                   font=("Segoe UI", 8),
                                   wraplength=210, justify="left")
        self.status_lbl.pack(side="bottom", padx=14, pady=12, anchor="w")

    def _run_task(self, cmd, btn):
        # highlight active button
        for b in self._task_btns:
            b.configure(bg=C_SURFACE, fg=C_TEXT)
        if btn:
            btn.configure(bg=C_HOVER, fg=C_PRIMARY)
        cmd()

    # ── upload box ────────────────────────────────────────────────────────────
    def _build_upload(self, parent):
        outer = tk.Frame(parent, bg=C_PRIMARY, padx=1, pady=1)
        outer.pack(fill="x", padx=14)

        box = tk.Frame(outer, bg=C_SURFACE,
                       highlightbackground=C_PRIMARY, highlightthickness=2,
                       pady=14)
        box.pack(fill="both")

        self.upload_icon = tk.Label(box, text="⬆", bg=C_SURFACE,
                                    fg=C_PRIMARY, font=("Segoe UI", 26))
        self.upload_icon.pack()

        self.upload_title = tk.Label(box, text="Upload here",
                                     bg=C_SURFACE, fg=C_TEXT,
                                     font=("Segoe UI", 11, "bold"))
        self.upload_title.pack()

        tk.Label(box, text="CSV or Excel  ·  drag & drop",
                 bg=C_SURFACE, fg=C_SUBTEXT,
                 font=("Segoe UI", 8)).pack(pady=(2,6))

        browse_btn = tk.Button(box, text="Browse…",
                               bg=C_PRIMARY, fg="white",
                               font=("Segoe UI", 9, "bold"),
                               relief="flat", bd=0, padx=16, pady=5,
                               activebackground=C_PRIMARY2, cursor="hand2",
                               command=self._browse)
        browse_btn.pack()

        # bind DnD on every widget in the box
        for w in [box, self.upload_icon, self.upload_title, browse_btn]:
            w.drop_target_register(DND_FILES)
            w.dnd_bind("<<Drop>>", self._on_drop)

    # ── main right area ───────────────────────────────────────────────────────
    def _build_main(self, parent):
        main = tk.Frame(parent, bg=C_BG)
        main.pack(side="left", fill="both", expand=True)

        # ── top: table strip ──────────────────────────────────────────────────
        table_strip = tk.Frame(main, bg=C_SURFACE, height=200,
                               highlightbackground=C_BORDER, highlightthickness=1)
        table_strip.pack(fill="x", padx=14, pady=(14,0))
        table_strip.pack_propagate(False)

        hdr = tk.Frame(table_strip, bg=C_PRIMARY, height=28)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  First 10 rows", bg=C_PRIMARY, fg="white",
                 font=("Segoe UI", 9, "bold")).pack(side="left", pady=4)

        self._build_table(table_strip)

        # ── bottom: plot / stats ──────────────────────────────────────────────
        bottom = tk.Frame(main, bg=C_BG)
        bottom.pack(fill="both", expand=True, padx=14, pady=10)

        # chart area
        self.chart_frame = tk.Frame(bottom, bg=C_SURFACE,
                                    highlightbackground=C_BORDER,
                                    highlightthickness=1)
        self.chart_frame.pack(side="left", fill="both", expand=True)

        chart_hdr = tk.Frame(self.chart_frame, bg=C_PRIMARY, height=28)
        chart_hdr.pack(fill="x")
        chart_hdr.pack_propagate(False)
        self.chart_title = tk.Label(chart_hdr, text="  Chart",
                                    bg=C_PRIMARY, fg="white",
                                    font=("Segoe UI", 9, "bold"))
        self.chart_title.pack(side="left", pady=4)

        self.plot_area = tk.Frame(self.chart_frame, bg=C_SURFACE)
        self.plot_area.pack(fill="both", expand=True)

        # stats panel
        stats_frame = tk.Frame(bottom, bg=C_SURFACE, width=260,
                               highlightbackground=C_BORDER, highlightthickness=1)
        stats_frame.pack(side="left", fill="y", padx=(10,0))
        stats_frame.pack_propagate(False)

        stats_hdr = tk.Frame(stats_frame, bg=C_PRIMARY, height=28)
        stats_hdr.pack(fill="x")
        stats_hdr.pack_propagate(False)
        tk.Label(stats_hdr, text="  Statistics", bg=C_PRIMARY, fg="white",
                 font=("Segoe UI", 9, "bold")).pack(side="left", pady=4)

        self.stats_box = tk.Text(stats_frame, bg=C_SURFACE, fg=C_TEXT,
                                 font=("Consolas", 8), relief="flat",
                                 wrap="word", state="disabled",
                                 padx=10, pady=8,
                                 insertbackground=C_TEXT)
        sb = ttk.Scrollbar(stats_frame, command=self.stats_box.yview)
        self.stats_box.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.stats_box.pack(fill="both", expand=True)
        self._set_stats("Upload a file to begin.")

    def _build_table(self, parent):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("VS.Treeview",
                        background=C_SURFACE, foreground=C_TEXT,
                        fieldbackground=C_SURFACE, rowheight=22,
                        font=("Consolas", 8))
        style.configure("VS.Treeview.Heading",
                        background=C_BG, foreground=C_SUBTEXT,
                        font=("Segoe UI", 8, "bold"), relief="flat")
        style.map("VS.Treeview",
                  background=[("selected", C_HOVER)],
                  foreground=[("selected", C_PRIMARY)])

        frame = tk.Frame(parent, bg=C_SURFACE)
        frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(frame, style="VS.Treeview",
                                 show="headings", selectmode="browse")
        vsb = ttk.Scrollbar(frame, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

    # ── file loading ──────────────────────────────────────────────────────────
    def _browse(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV / Excel","*.csv *.xlsx *.xls"),("All files","*.*")])
        if path:
            self._load(path)

    def _on_drop(self, event):
        self._load(event.data)

    def _load(self, path):
        try:
            raw = load_file(path)
            self.df = clean_df(raw)
            fname = os.path.basename(path.strip().strip("{}"))
            self.upload_title.config(text=f"✓  {fname}", fg=C_SUCCESS)
            self.upload_icon.config(text="✓", fg=C_SUCCESS)
            self.status_lbl.config(
                text=f"{len(raw):,} rows loaded\n{len(self.df):,} after cleaning")
            self._fill_table(raw)
            self._set_stats(
                f"File  : {fname}\nRows  : {len(raw):,}"
                f"\nClean : {len(self.df):,}\n\nSelect an analysis →")
            self._clear_chart()
        except Exception as exc:
            messagebox.showerror("Load error", str(exc))

    def _fill_table(self, df: pd.DataFrame):
        self.tree.delete(*self.tree.get_children())
        cols = list(df.columns)
        self.tree["columns"] = cols
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=max(75, len(c)*8),
                             anchor="center", stretch=False)
        for i, (_, row) in enumerate(df.head(10).iterrows()):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", tags=(tag,),
                             values=[str(v) if pd.notna(v) else "" for v in row])
        self.tree.tag_configure("odd",  background=C_STRIPE)
        self.tree.tag_configure("even", background=C_SURFACE)

    # ── chart display ─────────────────────────────────────────────────────────
    def _show_chart(self, fig, title="Chart"):
        self._clear_chart()
        self.chart_title.config(text=f"  {title}")
        canvas = FigureCanvasTkAgg(fig, master=self.plot_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._canvas_ref = canvas
        plt.close(fig)

    def _clear_chart(self):
        if self._canvas_ref:
            self._canvas_ref.get_tk_widget().destroy()
            self._canvas_ref = None

    def _set_stats(self, text: str):
        self.stats_box.config(state="normal")
        self.stats_box.delete("1.0", "end")
        self.stats_box.insert("end", text)
        self.stats_box.config(state="disabled")

    def _need_data(self) -> bool:
        if self.df is None:
            messagebox.showwarning("No data", "Please upload a file first.")
            return True
        return False

    # ── task handlers ─────────────────────────────────────────────────────────
    def _t3(self):
        if self._need_data(): return
        self._show_chart(chart_bar(self.df), "Total Delay by Cause")

    def _t4(self):
        if self._need_data(): return
        self._show_chart(chart_hist(self.df), "ArrDelay Distribution")

    def _t5(self):
        if self._need_data(): return
        self._show_chart(chart_scatter(self.df), "Flight Volume vs Arrival Delay")

    def _t6(self):
        if self._need_data(): return
        self._show_chart(chart_line(self.df), "Average Delay Trend")

    def _t7(self):
        if self._need_data(): return
        self._set_stats(get_stats(self.df))
        self._set_stats(get_stats(self.df))

    def _t8(self):
        if self._need_data(): return
        os.makedirs("output", exist_ok=True)
        fig  = chart_summary(self.df)
        path = os.path.abspath(os.path.join("output","flight_delays_summary.png"))
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=C_SURFACE)
        plt.close(fig)
        self._set_stats(f"Saved to:\n{path}")
        messagebox.showinfo("Saved", f"Summary chart saved:\n{path}")


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = App()
    app.mainloop()
