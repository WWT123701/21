"""海明码编解码与纠错演示器的 Tkinter 界面骨架。"""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# 窗口与字体配置
WINDOW_TITLE = "海明码编解码与纠错演示器"
WINDOW_GEOMETRY = "1000x650"
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 520
FONT_SIZE = 12
FONT_FAMILY_CANDIDATES = ("Microsoft YaHei UI", "Microsoft YaHei", "微软雅黑")

# 浅色主题配色
COLOR_BG = "#f3f6fa"
COLOR_CARD = "#ffffff"
COLOR_CANVAS = "#f8fafc"
COLOR_FOOTER = "#edf2f7"
COLOR_BORDER = "#d8e0ea"
COLOR_TITLE = "#1f2a37"
COLOR_TEXT = "#344054"
COLOR_MUTED = "#667085"
COLOR_ACCENT = "#2563eb"
COLOR_ACCENT_HOVER = "#1d4ed8"
COLOR_INPUT = "#fbfcfe"


class HammingApp:
    """封装演示器主窗口、主题样式和三栏界面布局。"""

    # 码字绘制尺寸与配色统一集中为类常量，避免颜色散落在绘制逻辑中。
    CELL_SIZE = 40
    CELL_GAP = 6
    HIGHLIGHT_BORDER_WIDTH = 3
    COLOR_PARITY_CELL = "#06b6d4"       # 校验位：青色
    COLOR_DATA_CELL = "#2563eb"         # 数据位：蓝色
    COLOR_CELL_TEXT = "#ffffff"         # 方块内文字：白色
    COLOR_HIGHLIGHT = "#dc2626"         # 高亮边框与指示三角：红色
    COLOR_POSITION_LABEL = "#475569"    # 上方位置号
    COLOR_ROLE_LABEL = "#64748b"        # 下方角色标签
    COLOR_EMPTY_TEXT = "#94a3b8"        # 空码字提示
    AUTO_STEP_MS = 700                  # 自动播放时每位之间的间隔
    CHANNEL_SIDE_MARGIN = 14            # 码字超出画布时两侧保留的滚动留白

    # 科技风主题配色：页头、霓虹强调色与终端日志区。
    COLOR_HEADER_BG = "#0b1526"
    COLOR_HEADER_CHIP = "#0f2742"
    COLOR_HEADER_LINE = "#1e3350"
    COLOR_HEADER_MUTED = "#8fa3bf"
    COLOR_NEON_CYAN = "#22d3ee"
    COLOR_NEON_GREEN = "#34d399"
    COLOR_CHANNEL_CYAN = "#0891b2"
    COLOR_VIOLET = "#7c3aed"
    COLOR_CONSOLE_BG = "#0b1220"
    COLOR_CONSOLE_BAR = "#111c2e"
    COLOR_CONSOLE_TEXT = "#dbeafe"
    COLOR_CONSOLE_MUTED = "#7f8ea3"
    COLOR_CONSOLE_SCROLL = "#334155"
    COLOR_CHANNEL_GRID = "#e9eff7"
    COLOR_CHANNEL_DECOR = "#b9c6d8"
    COLOR_DOT_RED = "#f87171"
    COLOR_DOT_AMBER = "#fbbf24"

    def __init__(self, master: tk.Tk | None = None) -> None:
        """初始化窗口、字体、ttk 样式以及全部界面组件。"""
        self.root = master if master is not None else tk.Tk()
        self.font_family = self._resolve_font_family()
        self._last_codeword: tuple[list[int], set[int], int | None] | None = None

        # 运行期状态：原始码字、校验位下标、单步位置与自动播放定时器。
        self._codeword: list[int] = []
        self._parity_idx: set[int] = set()
        self._step_index: int | None = None
        self._auto_job: str | None = None
        self._auto_playing = False

        self._configure_window()
        self._configure_fonts()
        self._configure_styles()
        self._build_layout()
        self.input_entry.focus_set()

    def _resolve_font_family(self) -> str:
        """从系统中选择可用的微软雅黑字体，避免不同环境下的字体回退。"""
        available_fonts = set(tkfont.families(self.root))
        for family in FONT_FAMILY_CANDIDATES:
            if family in available_fonts:
                return family
        return str(tkfont.nametofont("TkDefaultFont").actual("family"))

    def _configure_window(self) -> None:
        """设置窗口标题、初始尺寸、最小尺寸与根网格的伸缩规则。"""
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_GEOMETRY)
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.root.configure(background=COLOR_BG)

        # 页头与底栏固定高度，中间内容区占用剩余空间。
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)

    def _configure_fonts(self) -> None:
        """将 Tk 命名字体统一设置为微软雅黑 12 号。"""
        for font_name in (
            "TkDefaultFont",
            "TkTextFont",
            "TkMenuFont",
            "TkHeadingFont",
            "TkCaptionFont",
            "TkSmallCaptionFont",
            "TkIconFont",
            "TkTooltipFont",
        ):
            try:
                tkfont.nametofont(font_name).configure(
                    family=self.font_family,
                    size=FONT_SIZE,
                )
            except tk.TclError:
                # 某些 Tk 构建可能缺少个别命名字体，跳过即可。
                continue

        self.root.option_add("*Font", (self.font_family, FONT_SIZE))
        self.root.option_add("*TCombobox*Listbox.font", (self.font_family, FONT_SIZE))
        self.root.option_add("*TCombobox*Listbox.background", COLOR_CARD)
        self.root.option_add("*TCombobox*Listbox.foreground", COLOR_TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", COLOR_ACCENT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

    def _configure_styles(self) -> None:
        """初始化 ttk 主题，并配置统一的浅色控件样式。"""
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        ui_font = (self.font_family, FONT_SIZE)
        bold_font = (self.font_family, FONT_SIZE, "bold")

        style.configure(
            ".",
            font=ui_font,
            background=COLOR_BG,
            foreground=COLOR_TEXT,
        )

        # 页面、卡片与底栏使用不同层级的浅色背景。
        style.configure("App.TFrame", background=COLOR_BG)
        style.configure(
            "Card.TFrame",
            background=COLOR_CARD,
            bordercolor=COLOR_BORDER,
            lightcolor=COLOR_CARD,
            darkcolor=COLOR_BORDER,
            borderwidth=1,
            relief="solid",
        )
        style.configure("BottomBar.TFrame", background=COLOR_FOOTER)
        style.configure("Header.TFrame", background=self.COLOR_HEADER_BG)
        style.configure(
            "HeaderAccent.TFrame",
            background=self.COLOR_NEON_CYAN,
        )
        style.configure(
            "HeaderTitle.TLabel",
            background=self.COLOR_HEADER_BG,
            foreground="#f8fafc",
            font=(self.font_family, 18, "bold"),
        )
        style.configure(
            "HeaderSubtitle.TLabel",
            background=self.COLOR_HEADER_BG,
            foreground=self.COLOR_HEADER_MUTED,
            font=(self.font_family, 9),
        )
        style.configure("Console.TFrame", background=self.COLOR_CONSOLE_BG)
        style.configure(
            "ConsoleBar.TFrame",
            background=self.COLOR_CONSOLE_BAR,
        )
        style.configure(
            "ConsoleBarTitle.TLabel",
            background=self.COLOR_CONSOLE_BAR,
            foreground=self.COLOR_CONSOLE_MUTED,
            font=(self.font_family, 9, "bold"),
        )
        style.configure(
            "ConsoleLive.TLabel",
            background=self.COLOR_CONSOLE_BAR,
            foreground=self.COLOR_NEON_GREEN,
            font=(self.font_family, 9, "bold"),
        )
        style.configure(
            "Console.Vertical.TScrollbar",
            background=self.COLOR_CONSOLE_SCROLL,
            troughcolor=self.COLOR_CONSOLE_BG,
            bordercolor=self.COLOR_CONSOLE_BG,
            arrowcolor=self.COLOR_CONSOLE_MUTED,
            lightcolor=self.COLOR_CONSOLE_SCROLL,
            darkcolor=self.COLOR_CONSOLE_BG,
        )
        style.map(
            "Console.Vertical.TScrollbar",
            background=[("active", "#475569")],
        )
        style.configure(
            "Channel.Horizontal.TScrollbar",
            background=self.COLOR_CHANNEL_DECOR,
            troughcolor=COLOR_CANVAS,
            bordercolor=COLOR_CANVAS,
            arrowcolor=self.COLOR_CHANNEL_CYAN,
            lightcolor=self.COLOR_CHANNEL_DECOR,
            darkcolor=COLOR_CANVAS,
        )
        style.map(
            "Channel.Horizontal.TScrollbar",
            background=[("active", self.COLOR_CHANNEL_CYAN)],
        )

        style.configure(
            "Section.TLabel",
            background=COLOR_CARD,
            foreground=COLOR_TITLE,
            font=bold_font,
        )
        style.configure(
            "Body.TLabel",
            background=COLOR_CARD,
            foreground=COLOR_TEXT,
            font=ui_font,
        )
        style.configure(
            "Hint.TLabel",
            background=COLOR_CARD,
            foreground=COLOR_MUTED,
            font=ui_font,
        )
        style.configure(
            "Code.TLabel",
            background=COLOR_CARD,
            foreground=COLOR_MUTED,
            font=(self.font_family, 9, "bold"),
        )
        style.configure(
            "FooterMeta.TLabel",
            background=COLOR_FOOTER,
            foreground=COLOR_MUTED,
            font=(self.font_family, 9),
        )
        style.configure(
            "FooterReady.TLabel",
            background=COLOR_FOOTER,
            foreground="#059669",
            font=(self.font_family, 9, "bold"),
        )

        # 单行输入框和方案下拉框。
        style.configure(
            "Data.TEntry",
            font=ui_font,
            padding=6,
            fieldbackground=COLOR_INPUT,
            foreground=COLOR_TEXT,
            bordercolor=COLOR_BORDER,
            lightcolor=COLOR_BORDER,
            darkcolor=COLOR_BORDER,
        )
        style.map(
            "Data.TEntry",
            bordercolor=[("focus", COLOR_ACCENT)],
            lightcolor=[("focus", COLOR_ACCENT)],
            darkcolor=[("focus", COLOR_ACCENT)],
        )
        style.configure(
            "Scheme.TCombobox",
            font=ui_font,
            padding=5,
            fieldbackground=COLOR_INPUT,
            background=COLOR_CARD,
            foreground=COLOR_TEXT,
            arrowcolor=COLOR_MUTED,
            bordercolor=COLOR_BORDER,
            lightcolor=COLOR_BORDER,
            darkcolor=COLOR_BORDER,
        )
        style.map(
            "Scheme.TCombobox",
            fieldbackground=[("readonly", COLOR_INPUT)],
            selectbackground=[("readonly", COLOR_INPUT)],
            selectforeground=[("readonly", COLOR_TEXT)],
            bordercolor=[("focus", COLOR_ACCENT)],
        )

        # 主按钮与次按钮。
        style.configure(
            "Primary.TButton",
            font=ui_font,
            padding=(18, 8),
            background=COLOR_ACCENT,
            foreground="#ffffff",
            borderwidth=0,
            focuscolor=COLOR_ACCENT,
        )
        style.map(
            "Primary.TButton",
            background=[
                ("pressed", COLOR_ACCENT_HOVER),
                ("active", COLOR_ACCENT_HOVER),
                ("disabled", "#9bbcf5"),
            ],
            foreground=[("disabled", "#f2f6ff")],
        )
        style.configure(
            "Secondary.TButton",
            font=ui_font,
            padding=(18, 8),
            background=COLOR_CARD,
            foreground=COLOR_TEXT,
            bordercolor=COLOR_BORDER,
            lightcolor=COLOR_CARD,
            darkcolor=COLOR_BORDER,
        )
        style.map(
            "Secondary.TButton",
            background=[("pressed", "#e8eef6"), ("active", "#f1f5f9")],
            bordercolor=[("active", COLOR_ACCENT)],
            foreground=[("disabled", COLOR_MUTED)],
        )

    def _build_layout(self) -> None:
        """按 grid 网格搭建科技风页头、三栏主内容区与底部操作栏。"""
        self._build_header()

        content = ttk.Frame(
            self.root,
            style="App.TFrame",
            padding=(18, 14, 18, 12),
        )
        content.grid(row=1, column=0, sticky="nsew")

        # 三栏按 3:4:3 的比例随窗口缩放。
        content.columnconfigure(0, weight=3, uniform="main")
        content.columnconfigure(1, weight=4, uniform="main")
        content.columnconfigure(2, weight=3, uniform="main")
        content.rowconfigure(0, weight=1)

        encode_panel = self._build_encode_panel(content)
        channel_panel = self._build_channel_panel(content)
        check_panel = self._build_check_panel(content)

        encode_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        channel_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 12))
        check_panel.grid(row=0, column=2, sticky="nsew")

        self._build_bottom_bar()

    def _build_header(self) -> None:
        """创建深色科技风页头、芯片 Logo 与电路装饰。"""
        header = ttk.Frame(self.root, style="Header.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        inner = ttk.Frame(
            header,
            style="Header.TFrame",
            padding=(22, 9),
        )
        inner.grid(row=0, column=0, sticky="ew")
        inner.columnconfigure(1, weight=1)

        logo = tk.Canvas(
            inner,
            width=54,
            height=54,
            background=self.COLOR_HEADER_BG,
            highlightthickness=0,
        )
        logo.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 14))
        self._draw_logo(logo)

        title = ttk.Label(
            inner,
            text=WINDOW_TITLE,
            style="HeaderTitle.TLabel",
        )
        title.grid(row=0, column=1, sticky="sw")

        subtitle = ttk.Label(
            inner,
            text="HAMMING CODE LAB  /  ERROR CORRECTION SIMULATOR",
            style="HeaderSubtitle.TLabel",
        )
        subtitle.grid(row=1, column=1, sticky="nw", pady=(0, 2))

        art = tk.Canvas(
            inner,
            width=222,
            height=50,
            background=self.COLOR_HEADER_BG,
            highlightthickness=0,
        )
        art.grid(row=0, column=2, rowspan=2, sticky="e", padx=(18, 0))
        self._draw_header_art(art)
        self.header_art = art
        inner.bind("<Configure>", self._on_header_configure)

        # 页头底部使用一条霓虹色细线收尾。
        accent = ttk.Frame(header, style="HeaderAccent.TFrame", height=2)
        accent.grid(row=1, column=0, sticky="ew")

    def _on_header_configure(self, event: tk.Event) -> None:
        """窗口较窄时隐藏页头右侧装饰，避免挤压标题文字。"""
        if event.width < 900:
            self.header_art.grid_remove()
        else:
            self.header_art.grid()

    def _draw_logo(self, canvas: tk.Canvas) -> None:
        """绘制六边形芯片 Logo 与“01”数码符号。"""
        canvas.create_polygon(
            27, 3, 47, 15, 47, 39, 27, 51, 7, 39, 7, 15,
            fill=self.COLOR_HEADER_CHIP,
            outline=self.COLOR_NEON_CYAN,
            width=2,
        )
        canvas.create_polygon(
            27, 9, 42, 18, 42, 36, 27, 45, 12, 36, 12, 18,
            fill="",
            outline=self.COLOR_HEADER_LINE,
            width=1,
        )
        for y in (18, 27, 36):
            canvas.create_line(
                0, y, 7, y,
                fill=self.COLOR_NEON_CYAN,
                width=1,
            )
            canvas.create_line(
                47, y, 54, y,
                fill=self.COLOR_NEON_CYAN,
                width=1,
            )
        canvas.create_text(
            27,
            27,
            text="01",
            fill=self.COLOR_NEON_CYAN,
            font=(self.font_family, 10, "bold"),
        )

    def _draw_header_art(self, canvas: tk.Canvas) -> None:
        """绘制页头右侧的二进制代码、电路节点与在线状态。"""
        canvas.create_text(
            218,
            5,
            anchor="ne",
            text="0101 1011 0010 1101",
            fill=self.COLOR_HEADER_MUTED,
            font=(self.font_family, 8),
        )
        canvas.create_line(
            4, 33, 218, 33,
            fill=self.COLOR_HEADER_LINE,
            width=1,
        )
        canvas.create_line(
            4, 33, 42, 33, 42, 24, 84, 24, 84, 33, 126, 33,
            fill=self.COLOR_NEON_CYAN,
            width=1,
        )
        canvas.create_line(
            150, 33, 150, 42, 196, 42, 196, 33, 218, 33,
            fill=self.COLOR_NEON_GREEN,
            width=1,
        )
        for x, y, color in (
            (42, 24, self.COLOR_NEON_CYAN),
            (126, 33, self.COLOR_NEON_CYAN),
            (196, 42, self.COLOR_NEON_GREEN),
        ):
            canvas.create_oval(
                x - 3, y - 3, x + 3, y + 3,
                fill=color,
                outline="",
            )
        canvas.create_text(
            4,
            46,
            anchor="w",
            text="SYS.CHECK",
            fill=self.COLOR_HEADER_MUTED,
            font=(self.font_family, 8, "bold"),
        )
        canvas.create_text(
            218,
            46,
            anchor="e",
            text="● ONLINE",
            fill=self.COLOR_NEON_GREEN,
            font=(self.font_family, 8, "bold"),
        )

    def _build_panel_header(
        self,
        panel: ttk.Frame,
        title_text: str,
        icon_text: str,
        channel_code: str,
        accent_color: str,
    ) -> ttk.Frame:
        """创建带六边形数码徽标和通道编号的卡片标题栏。"""
        header = ttk.Frame(panel, style="Card.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        badge = tk.Canvas(
            header,
            width=32,
            height=32,
            background=COLOR_CARD,
            highlightthickness=0,
        )
        badge.grid(row=0, column=0, sticky="w", padx=(0, 10))
        badge.create_polygon(
            10, 1, 22, 1, 31, 10, 31, 22, 22, 31, 10, 31, 1, 22, 1, 10,
            fill=accent_color,
            outline="",
        )
        badge.create_text(
            16,
            16,
            text=icon_text,
            fill=self.COLOR_CELL_TEXT,
            font=(self.font_family, 9, "bold"),
        )

        title = ttk.Label(
            header,
            text=title_text,
            style="Section.TLabel",
        )
        title.grid(row=0, column=1, sticky="w")

        code = ttk.Label(
            header,
            text=channel_code,
            style="Code.TLabel",
        )
        code.grid(row=0, column=2, sticky="e")

        return header

    def _build_encode_panel(self, parent: ttk.Frame) -> ttk.Frame:
        """创建左侧编码区，包含输入框、编码方案下拉框和编码按钮。"""
        panel = ttk.Frame(parent, style="Card.TFrame", padding=(18, 14))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(2, weight=1)

        self._build_panel_header(
            panel,
            "编码区",
            "01",
            "CH.01",
            COLOR_ACCENT,
        )

        intro = ttk.Label(
            panel,
            text="输入数据并选择编码方案",
            style="Body.TLabel",
        )
        intro.grid(row=1, column=0, sticky="w", pady=(6, 14))

        # 表单区单独使用 Frame 分区，内部全部通过 grid 排列。
        form = ttk.Frame(panel, style="Card.TFrame")
        form.grid(row=2, column=0, sticky="new")
        form.columnconfigure(0, weight=1)

        data_label = ttk.Label(form, text="数据  ·  BINARY", style="Body.TLabel")
        data_label.grid(row=0, column=0, sticky="w")

        self.input_entry = ttk.Entry(form, style="Data.TEntry")
        self.input_entry.grid(row=1, column=0, sticky="ew", pady=(6, 14))
        self.input_entry.bind("<Return>", self._on_entry_return)

        scheme_label = ttk.Label(
            form,
            text="编码方案  ·  SCHEME",
            style="Body.TLabel",
        )
        scheme_label.grid(row=2, column=0, sticky="w")

        self.scheme_combobox = ttk.Combobox(
            form,
            values=["Hamming(7,4)", "Hamming(15,11)"],
            state="readonly",
            style="Scheme.TCombobox",
            width=15,
        )
        self.scheme_combobox.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        self.scheme_combobox.current(0)

        self.encode_button = ttk.Button(
            panel,
            text="编码",
            style="Primary.TButton",
            command=self.on_encode,
        )
        self.encode_button.grid(row=3, column=0, sticky="ew", pady=(16, 0))

        return panel

    def _build_channel_panel(self, parent: ttk.Frame) -> ttk.Frame:
        """创建中间信道区，包含可伸缩 Canvas 和注入错误提示标签。"""
        panel = ttk.Frame(parent, style="Card.TFrame", padding=(18, 14))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        self._build_panel_header(
            panel,
            "信道区",
            "TX",
            "CH.02",
            self.COLOR_CHANNEL_CYAN,
        )

        # Canvas 无法使用 ttk 版本，因此使用 tk.Canvas 并手动匹配浅色主题。
        canvas_frame = ttk.Frame(panel, style="Card.TFrame")
        canvas_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        self.channel_canvas = tk.Canvas(
            canvas_frame,
            width=200,
            background=COLOR_CANVAS,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_BORDER,
        )
        self.channel_canvas.grid(row=0, column=0, sticky="nsew")
        self.channel_canvas.bind("<Configure>", self._on_canvas_configure)

        self.channel_scrollbar = ttk.Scrollbar(
            canvas_frame,
            orient="horizontal",
            command=self.channel_canvas.xview,
            style="Channel.Horizontal.TScrollbar",
        )
        self.channel_scrollbar.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.channel_scrollbar.grid_remove()
        self.channel_canvas.configure(xscrollcommand=self.channel_scrollbar.set)

        self.channel_hint = ttk.Label(
            panel,
            text="提示：在此区域注入错误",
            style="Hint.TLabel",
        )
        self.channel_hint.grid(row=2, column=0, sticky="w", pady=(8, 0))

        return panel

    def _build_check_panel(self, parent: ttk.Frame) -> ttk.Frame:
        """创建右侧校验区，包含终端风格只读日志与垂直滚动条。"""
        panel = ttk.Frame(parent, style="Card.TFrame", padding=(18, 14))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        self._build_panel_header(
            panel,
            "校验区",
            "OK",
            "CH.03",
            self.COLOR_VIOLET,
        )

        log_frame = ttk.Frame(panel, style="Console.TFrame")
        log_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1)

        self._build_console_bar(log_frame)

        # Text 组件通过 disabled 状态实现只读展示。
        self.log_text = tk.Text(
            log_frame,
            wrap="word",
            state="disabled",
            font=(self.font_family, FONT_SIZE),
            background=self.COLOR_CONSOLE_BG,
            foreground=self.COLOR_CONSOLE_TEXT,
            insertbackground=self.COLOR_CONSOLE_TEXT,
            selectbackground=self.COLOR_CHANNEL_CYAN,
            selectforeground="#ffffff",
            borderwidth=0,
            relief="flat",
            highlightthickness=0,
            padx=12,
            pady=10,
            spacing1=2,
            spacing3=2,
            width=14,
            cursor="arrow",
        )
        self.log_text.grid(row=1, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            log_frame,
            orient="vertical",
            command=self.log_text.yview,
            style="Console.Vertical.TScrollbar",
        )
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        # 首屏提示写在切换到只读状态之前。
        self.log_text.configure(state="normal")
        self.log_text.insert(
            "1.0",
            "系统就绪。\n输入 4 位或 11 位二进制数据。\n点击“编码”开始演示。\n",
        )
        self.log_text.configure(state="disabled")

        return panel

    def _build_console_bar(self, parent: ttk.Frame) -> ttk.Frame:
        """创建带红黄绿状态灯的终端日志标题栏。"""
        bar = ttk.Frame(
            parent,
            style="ConsoleBar.TFrame",
            padding=(10, 0),
        )
        bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        bar.columnconfigure(1, weight=1)

        dots = tk.Canvas(
            bar,
            width=54,
            height=28,
            background=self.COLOR_CONSOLE_BAR,
            highlightthickness=0,
        )
        dots.grid(row=0, column=0, sticky="w", padx=(0, 8))
        for x, color in (
            (8, self.COLOR_DOT_RED),
            (20, self.COLOR_DOT_AMBER),
            (32, self.COLOR_NEON_GREEN),
        ):
            dots.create_oval(
                x - 3, 11, x + 3, 17,
                fill=color,
                outline="",
            )

        title = ttk.Label(
            bar,
            text="LOG",
            style="ConsoleBarTitle.TLabel",
        )
        title.grid(row=0, column=1, sticky="w")

        live = ttk.Label(
            bar,
            text="● LIVE",
            style="ConsoleLive.TLabel",
        )
        live.grid(row=0, column=2, sticky="e")

        return bar

    def _build_bottom_bar(self) -> None:
        """创建带状态装饰的底部操作栏和三个操作按钮。"""
        bottom_bar = ttk.Frame(
            self.root,
            style="BottomBar.TFrame",
            padding=(18, 10),
        )
        bottom_bar.grid(row=2, column=0, sticky="ew")
        bottom_bar.columnconfigure(0, weight=1)
        bottom_bar.columnconfigure(2, weight=1)

        meta = ttk.Label(
            bottom_bar,
            text="HAMMING LAB / SIGNAL LAB",
            style="FooterMeta.TLabel",
        )
        meta.grid(row=0, column=0, sticky="w")

        # 按钮组使用独立 Frame 居中，避免按钮随窗口无限拉伸。
        actions = ttk.Frame(bottom_bar, style="BottomBar.TFrame")
        actions.grid(row=0, column=1)

        self.step_button = ttk.Button(
            actions,
            text="单步执行",
            style="Secondary.TButton",
            command=self.on_step,
        )
        self.auto_button = ttk.Button(
            actions,
            text="自动播放",
            style="Primary.TButton",
            command=self.on_auto_play,
        )
        self.reset_button = ttk.Button(
            actions,
            text="重置",
            style="Secondary.TButton",
            command=self.on_reset,
        )

        buttons = (self.step_button, self.auto_button, self.reset_button)
        for column, button in enumerate(buttons):
            button.grid(
                row=0,
                column=column,
                padx=(0 if column == 0 else 10, 0),
            )

        ready = ttk.Label(
            bottom_bar,
            text="● READY",
            style="FooterReady.TLabel",
        )
        ready.grid(row=0, column=2, sticky="e")

    def append_log(self, message: str) -> None:
        """向校验区日志追加一条信息，并自动滚动到底部。"""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _on_entry_return(self, _event: tk.Event) -> None:
        """在数据输入框中按回车时执行编码。"""
        self.on_encode()

    def _get_scheme_parameters(self) -> tuple[int, int] | None:
        """返回当前方案的（总位数，数据位数），无法识别时返回 None。"""
        scheme = self.scheme_combobox.get()
        if scheme == "Hamming(7,4)":
            return 7, 4
        if scheme == "Hamming(15,11)":
            return 15, 11
        return None

    def _encode_hamming(
        self,
        data_bits: list[int],
        total_bits: int,
    ) -> tuple[list[int], set[int]]:
        """使用偶校验生成海明码，返回码字和校验位零基下标集合。"""
        # 1、2、4、8……位置为校验位，其余位置依次填入数据位。
        parity_positions: list[int] = []
        position = 1
        while position <= total_bits:
            parity_positions.append(position)
            position <<= 1
        parity_idx = {position - 1 for position in parity_positions}

        codeword = [0] * total_bits
        data_iter = iter(data_bits)
        for position in range(1, total_bits + 1):
            if position not in parity_positions:
                codeword[position - 1] = next(data_iter)

        # 每个校验位负责覆盖二进制位为 1 的所有位置，使对应分组保持偶数校验。
        for parity_position in parity_positions:
            parity = 0
            for position in range(1, total_bits + 1):
                if position & parity_position:
                    parity ^= codeword[position - 1]
            codeword[parity_position - 1] = parity

        return codeword, parity_idx

    def _role_for_index(self, index: int, parity_idx: set[int]) -> str:
        """返回零基下标对应的 p/d 角色名称。"""
        if index in parity_idx:
            return f"p{index + 1}"
        data_number = sum(
            1
            for position in range(index + 1)
            if position not in parity_idx
        )
        return f"d{data_number}"

    def _highlight_step(self, index: int, source: str) -> None:
        """高亮指定位并写入单步或自动播放日志。"""
        self._step_index = index
        self.draw_codeword(self._codeword, self._parity_idx, index)
        role = self._role_for_index(index, self._parity_idx)
        self.append_log(
            f"{source}：第 {index + 1} 位（{role}）= {self._codeword[index]}"
        )

    def _stop_auto_play(self) -> None:
        """停止自动播放计时器，并把按钮文字恢复为“自动播放”。"""
        if self._auto_job is not None:
            try:
                self.root.after_cancel(self._auto_job)
            except tk.TclError:
                pass
            self._auto_job = None
        self._auto_playing = False
        self.auto_button.configure(text="自动播放")

    def _auto_step(self) -> None:
        """自动播放定时回调：高亮下一位，到末尾后自动停止。"""
        self._auto_job = None
        if not self._auto_playing or not self._codeword:
            return

        next_index = 0 if self._step_index is None else self._step_index + 1
        if next_index >= len(self._codeword):
            self._stop_auto_play()
            self.append_log("自动播放结束。")
            return

        self._highlight_step(next_index, "自动")
        self._auto_job = self.root.after(self.AUTO_STEP_MS, self._auto_step)

    def _draw_channel_decorations(
        self,
        canvas: tk.Canvas,
        content_width: int | None = None,
    ) -> None:
        """绘制信道内的点状网格、四角定位框与二进制装饰。"""
        width = content_width if content_width is not None else canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        # 低对比度点状网格，营造信号示波器的底层质感。
        for x in range(24, width, 24):
            canvas.create_line(
                x, 0, x, height,
                fill=self.COLOR_CHANNEL_GRID,
                dash=(1, 6),
            )
        for y in range(24, height, 24):
            canvas.create_line(
                0, y, width, y,
                fill=self.COLOR_CHANNEL_GRID,
                dash=(1, 6),
            )

        # 四角霓虹定位框。
        margin = 11
        length = 14
        corners = (
            (margin, margin, 1, 1),
            (width - margin, margin, -1, 1),
            (margin, height - margin, 1, -1),
            (width - margin, height - margin, -1, -1),
        )
        for x, y, dx, dy in corners:
            canvas.create_line(
                x, y, x + length * dx, y,
                fill=self.COLOR_CHANNEL_CYAN,
                width=1,
            )
            canvas.create_line(
                x, y, x, y + length * dy,
                fill=self.COLOR_CHANNEL_CYAN,
                width=1,
            )

        # 顶部和底部的微型数码标记。
        canvas.create_text(
            18,
            15,
            anchor="nw",
            text="CHANNEL // 01",
            fill=self.COLOR_CHANNEL_DECOR,
            font=(self.font_family, 8, "bold"),
        )
        canvas.create_text(
            width - 18,
            15,
            anchor="ne",
            text="0x7F",
            fill=self.COLOR_CHANNEL_DECOR,
            font=(self.font_family, 8),
        )
        canvas.create_text(
            width - 18,
            height - 14,
            anchor="se",
            text="0101 0011 1010",
            fill=self.COLOR_CHANNEL_GRID,
            font=(self.font_family, 8),
        )

    def _draw_channel_placeholder(self) -> None:
        """绘制等待编码数据的六边形芯片图形和占位文案。"""
        canvas = self.channel_canvas
        canvas.delete("all")

        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        # 占位状态不需要横向滚动，恢复为完整画布宽度。
        self.channel_scrollbar.grid_remove()
        canvas.configure(scrollregion=(0, 0, width, height))
        canvas.xview_moveto(0)
        self.channel_hint.configure(text="提示：在此区域注入错误")
        self._draw_channel_decorations(canvas, width)

        center_x = width // 2
        center_y = height // 2 - 18
        radius = 25

        # 芯片左右两侧的引脚。
        for offset in (-12, 0, 12):
            canvas.create_line(
                center_x - radius - 12,
                center_y + offset,
                center_x - radius,
                center_y + offset,
                fill=self.COLOR_CHANNEL_CYAN,
                width=1,
            )
            canvas.create_line(
                center_x + radius,
                center_y + offset,
                center_x + radius + 12,
                center_y + offset,
                fill=self.COLOR_CHANNEL_CYAN,
                width=1,
            )

        # 六边形芯片轮廓与“01”核心。
        chip_points = []
        for angle in range(0, 360, 60):
            radians = math.radians(angle - 30)
            chip_points.extend(
                (
                    center_x + radius * math.cos(radians),
                    center_y + radius * math.sin(radians),
                )
            )
        canvas.create_polygon(
            *chip_points,
            fill="",
            outline=self.COLOR_CHANNEL_CYAN,
            width=2,
        )
        canvas.create_text(
            center_x,
            center_y,
            text="01",
            fill=self.COLOR_CHANNEL_CYAN,
            font=(self.font_family, 12, "bold"),
        )
        canvas.create_text(
            center_x,
            center_y + 50,
            text="等待编码数据",
            fill=self.COLOR_ROLE_LABEL,
            font=(self.font_family, FONT_SIZE),
        )
        canvas.create_text(
            center_x,
            center_y + 72,
            text="AWAITING BINARY INPUT",
            fill=self.COLOR_EMPTY_TEXT,
            font=(self.font_family, 8, "bold"),
        )

    def _on_canvas_configure(self, _event: tk.Event) -> None:
        """在 Canvas 尺寸变化后重新绘制占位图或当前码字。"""
        if self._last_codeword is None:
            self._draw_channel_placeholder()
            return
        bits, parity_idx, highlight_idx = self._last_codeword
        self.draw_codeword(bits, parity_idx, highlight_idx)

    def draw_codeword(
        self,
        bits: list[int],
        parity_idx: set[int],
        highlight_idx: int | None,
    ) -> None:
        """在信道 Canvas 上绘制一行码字方块。

        参数:
            bits: 按位序排列的码字列表，支持 7 位或 15 位等任意长度。
            parity_idx: 校验位在 bits 中的零基下标集合。
            highlight_idx: 需要突出显示的零基下标；None 表示不高亮。
        """
        canvas = self.channel_canvas

        # 保存最近一次绘制参数，便于窗口尺寸变化后重新居中绘制。
        self._last_codeword = (list(bits), set(parity_idx), highlight_idx)

        # 每次重绘前清空 Canvas，避免新旧码字重叠。
        canvas.delete("all")

        # 布局尚未完成时先返回，等待 Canvas 的 <Configure> 事件触发重绘。
        canvas_width = canvas.winfo_width()
        if canvas_width <= 1:
            return

        canvas_height = canvas.winfo_height()
        if canvas_height <= 1:
            canvas_height = int(canvas.cget("height"))

        # 没有码字时绘制空状态，并恢复为非滚动视图。
        if not bits:
            self.channel_scrollbar.grid_remove()
            self.channel_hint.configure(text="提示：在此区域注入错误")
            canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
            canvas.xview_moveto(0)
            self._draw_channel_decorations(canvas, canvas_width)
            canvas.create_text(
                canvas_width // 2,
                canvas_height // 2,
                text="暂无码字",
                fill=self.COLOR_EMPTY_TEXT,
                font=(self.font_family, FONT_SIZE),
            )
            return

        # 计算整行总宽度；超出画布时扩大虚拟内容区并启用横向滚动。
        total_width = (
            len(bits) * self.CELL_SIZE
            + max(0, len(bits) - 1) * self.CELL_GAP
        )
        content_width = canvas_width
        if total_width > canvas_width:
            content_width = total_width + 2 * self.CHANNEL_SIDE_MARGIN
        start_x = (content_width - total_width) // 2

        if content_width > canvas_width:
            self.channel_scrollbar.grid()
            self.channel_hint.configure(
                text="提示：注入错误 · 可横向滚动"
            )
        else:
            self.channel_scrollbar.grid_remove()
            self.channel_hint.configure(text="提示：在此区域注入错误")

        canvas.configure(
            scrollregion=(0, 0, content_width, canvas_height),
        )
        self._draw_channel_decorations(canvas, content_width)

        # 预留上方位置号、下方角色标签和指示三角的空间，并让整行垂直居中。
        top_label_space = 28
        role_space = 26
        triangle_space = 18
        block_height = (
            top_label_space
            + self.CELL_SIZE
            + role_space
            + triangle_space
        )
        cell_top = max(
            top_label_space,
            (canvas_height - block_height) // 2 + top_label_space,
        )

        for index, bit in enumerate(bits):
            # 计算当前格子的左上角、右下角和中心点坐标。
            x1 = start_x + index * (self.CELL_SIZE + self.CELL_GAP)
            y1 = cell_top
            x2 = x1 + self.CELL_SIZE
            y2 = y1 + self.CELL_SIZE
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # 校验位使用青色底，数据位使用蓝色底。
            fill_color = (
                self.COLOR_PARITY_CELL
                if index in parity_idx
                else self.COLOR_DATA_CELL
            )
            is_highlighted = highlight_idx == index

            # 绘制方块；高亮格额外使用红色粗边框。
            canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=fill_color,
                outline=(
                    self.COLOR_HIGHLIGHT
                    if is_highlighted
                    else fill_color
                ),
                width=(
                    self.HIGHLIGHT_BORDER_WIDTH
                    if is_highlighted
                    else 1
                ),
            )

            # 在方块中心绘制 0/1，统一使用白色粗体文字。
            canvas.create_text(
                center_x,
                center_y,
                text=str(bit),
                fill=self.COLOR_CELL_TEXT,
                font=(self.font_family, FONT_SIZE, "bold"),
            )

            # 在方块上方标注 1 起始的位置号。
            canvas.create_text(
                center_x,
                y1 - 8,
                text=str(index + 1),
                anchor="s",
                fill=self.COLOR_POSITION_LABEL,
                font=(self.font_family, FONT_SIZE),
            )

            # 在方块下方标注角色：p 开头为校验位，d 开头为数据位。
            role = self._role_for_index(index, parity_idx)
            canvas.create_text(
                center_x,
                y2 + 6,
                text=role,
                anchor="n",
                fill=self.COLOR_ROLE_LABEL,
                font=(self.font_family, FONT_SIZE),
            )

            # 高亮格下方绘制红色上指三角，尖端对准该格中心。
            if is_highlighted:
                triangle_apex_y = y2 + 28
                triangle_base_y = triangle_apex_y + 12
                canvas.create_polygon(
                    center_x,
                    triangle_apex_y,
                    center_x - 7,
                    triangle_base_y,
                    center_x + 7,
                    triangle_base_y,
                    fill=self.COLOR_HIGHLIGHT,
                    outline=self.COLOR_HIGHLIGHT,
                )

        # 无高亮时从最左端开始；单步/自动播放时把高亮位移入可视区域。
        if highlight_idx is None:
            canvas.xview_moveto(0)
        else:
            self._scroll_cell_into_view(
                highlight_idx,
                start_x,
                content_width,
                canvas_width,
            )

    def _scroll_cell_into_view(
        self,
        index: int,
        start_x: int,
        content_width: int,
        viewport_width: int,
    ) -> None:
        """在横向滚动模式下确保指定码位处于可视区域。"""
        if content_width <= viewport_width:
            self.channel_canvas.xview_moveto(0)
            return

        cell_left = start_x + index * (self.CELL_SIZE + self.CELL_GAP)
        cell_right = cell_left + self.CELL_SIZE
        view_left = self.channel_canvas.canvasx(0)
        view_right = view_left + viewport_width
        if view_left <= cell_left and cell_right <= view_right:
            return

        target_left = cell_left - (viewport_width - self.CELL_SIZE) // 2
        max_left = content_width - viewport_width
        target_left = max(0, min(target_left, max_left))
        self.channel_canvas.xview_moveto(target_left / content_width)

    def on_encode(self) -> None:
        """读取输入并按当前方案生成海明码，然后在信道区绘制。"""
        self._stop_auto_play()
        scheme = self.scheme_combobox.get()
        parameters = self._get_scheme_parameters()
        if parameters is None:
            self.append_log("无法识别当前编码方案，请重新选择。")
            return

        total_bits, data_length = parameters
        raw = self.input_entry.get().strip().replace(" ", "")

        # 校验输入是否为空、是否只含 0/1，以及长度是否符合方案要求。
        if not raw:
            self.append_log(f"请输入 {data_length} 位二进制数据。")
            self.input_entry.focus_set()
            return
        if any(character not in "01" for character in raw):
            self.append_log("输入格式错误：数据只能包含 0 和 1。")
            self.input_entry.focus_set()
            self.input_entry.selection_range(0, "end")
            return
        if len(raw) != data_length:
            self.append_log(
                f"“{scheme}”需要 {data_length} 位数据，当前输入 {len(raw)} 位。"
            )
            self.input_entry.focus_set()
            self.input_entry.selection_range(0, "end")
            return

        # 编码成功后更新运行状态，并清除之前的单步高亮。
        data_bits = [int(character) for character in raw]
        self._codeword, self._parity_idx = self._encode_hamming(
            data_bits,
            total_bits,
        )
        self._step_index = None
        self.draw_codeword(self._codeword, self._parity_idx, None)

        code_text = "".join(str(bit) for bit in self._codeword)
        parity_text = "、".join(
            self._role_for_index(index, self._parity_idx)
            for index in sorted(self._parity_idx)
        )
        self.append_log(f"{scheme} 编码完成：{raw} → {code_text}")
        self.append_log(
            f"校验位：{parity_text}；可点击“单步执行”或“自动播放”。"
        )

    def on_step(self) -> None:
        """逐位高亮当前码字，便于观察每个码位的角色和取值。"""
        if not self._codeword:
            self._stop_auto_play()
            self.append_log("请先输入数据并点击“编码”生成码字。")
            self.input_entry.focus_set()
            return

        was_playing = self._auto_playing
        self._stop_auto_play()
        if was_playing:
            self.append_log("自动播放已暂停。")

        # 第一次从第 1 位开始，之后顺序推进并在末尾回到开头。
        if self._step_index is None:
            next_index = 0
        else:
            next_index = (self._step_index + 1) % len(self._codeword)
        self._highlight_step(next_index, "单步")

    def on_auto_play(self) -> None:
        """开始或暂停自动逐位播放。"""
        if self._auto_playing:
            self._stop_auto_play()
            self.append_log("自动播放已暂停。")
            return

        if not self._codeword:
            self.append_log("请先输入数据并点击“编码”生成码字。")
            self.input_entry.focus_set()
            return

        # 未高亮或已到最后一位时从头开始，否则从当前位继续。
        self._auto_playing = True
        self.auto_button.configure(text="暂停播放")
        if self._step_index is None or self._step_index >= len(self._codeword) - 1:
            self._step_index = -1

        self.append_log("自动播放开始。")
        self._auto_job = self.root.after(0, self._auto_step)

    def on_reset(self) -> None:
        """停止播放、清空输入和码字，并恢复初始界面状态。"""
        self._stop_auto_play()
        self._codeword = []
        self._parity_idx = set()
        self._step_index = None
        self.input_entry.delete(0, "end")
        self.scheme_combobox.current(0)
        self._last_codeword = None
        self._draw_channel_placeholder()

        # 清空日志并写入重置提示。
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert(
            "1.0",
            "已重置。\n请输入数据并点击“编码”。\n",
        )
        self.log_text.configure(state="disabled")
        self.input_entry.focus_set()

    def run(self) -> None:
        """启动 Tkinter 主事件循环。"""
        self.root.mainloop()


if __name__ == "__main__":
    # 支持直接运行 ui/app.py 进行界面预览。
    HammingApp().run()
