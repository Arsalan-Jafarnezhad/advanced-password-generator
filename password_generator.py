from tkinter import font, messagebox
from secrets import choice, randbelow
from string import ascii_uppercase, ascii_lowercase, digits, punctuation
from webbrowser import open_new_tab
import sys
from tkinter import (
    IntVar,
    StringVar,
    BooleanVar,
    PhotoImage,
    Frame,
    Label,
    Entry,
    Button,
    Canvas,
    END,
    Checkbutton,
    Tk,
    Scale,
    Scrollbar,
)
from pathlib import Path
import sys

def resource_path(relative_path):
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = Path(__file__).parent

    return base_path / relative_path

try:
    from PIL import Image, ImageTk

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class PasswordGeneratorApp:
    MIN_LENGTH = 4
    MAX_LENGTH = 128
    ICON_SIZE = 20  # <- single place to control social icon size (px)
    SCROLL_SPEED = 40  # <- pixels scrolled per wheel notch; raise/lower to tune feel

    def __init__(self, master):
        self.master = master
        self.master.title("Advanced Password Generator")
        self.master.geometry("920x540+100+100")
        self.master.resizable(False, False)
        self.master.minsize(820, 500)
        self.master.configure(bg="#101418")
        self.master.iconbitmap(resource_path("icon.ico"))
        # ===============================
        # Social Media
        # ===============================
        self.github_url = (
            "https://github.com/arsalan-jafarnezhad/advanced-password-generator/"
        )
        self.telegram_url = "https://t.me/axiomlite/"
        self.linkedin_url = "https://linkedin.com/in/arsalan-jafarnezhad/"

        # Icons are loaded lazily/safely. Missing files no longer crash the app -
        # a text fallback button is rendered instead.
        self.github_icon = self.load_icon(resource_path("github.png"), self.ICON_SIZE)
        self.telegram_icon = self.load_icon(resource_path("telegram.png"), self.ICON_SIZE)
        self.linkedin_icon = self.load_icon(resource_path("linkedin.png"), self.ICON_SIZE)

        self.colors = {
            "bg": "#101418",
            "panel": "#171c22",
            "panel_alt": "#1d242c",
            "text": "#e6edf3",
            "muted": "#8b949e",
            "accent": "#2ea043",
            "accent_hover": "#3fb950",
            "danger": "#f85149",
            "danger_hover": "#ff6b6b",
            "entry_bg": "#0d1117",
            "entry_border": "#30363d",
            "warn": "#d29922",
        }

        self.title_font = font.Font(family="Segoe UI", size=22, weight="bold")
        self.label_font = font.Font(family="Segoe UI", size=12)
        self.label_bold_font = font.Font(family="Segoe UI", size=12, weight="bold")
        self.password_font = font.Font(family="Consolas", size=16, weight="bold")
        self.small_font = font.Font(family="Segoe UI", size=10)
        self.icon_fallback_font = font.Font(family="Segoe UI", size=9, weight="bold")

        # Scale uses an IntVar (required by Scale).
        self.length_var = IntVar(value=16)
        # Entry uses its own StringVar so invalid/partial typing can never
        # raise a TclError (the original bug: clearing the box crashed the trace).
        self.length_str_var = StringVar(value="16")

        self.password_var = StringVar(value="")
        self.status_var = StringVar(
            value="Select character groups and generate a password."
        )
        self.status_color = self.colors["muted"]
        self.strength_var = StringVar(value="Strength: -")

        self.uppercase_var = BooleanVar(value=True)
        self.lowercase_var = BooleanVar(value=True)
        self.numbers_var = BooleanVar(value=True)
        self.special_var = BooleanVar(value=False)
        self.exclude_ambiguous_var = BooleanVar(value=False)
        self.require_each_selected_var = BooleanVar(value=True)
        self.exclude_custom_var = StringVar(value="")

        self._copy_reset_job = None

        self.create_widgets()

        # Keep the slider and the text entry in sync without fighting the user.
        self.length_var.trace_add("write", self._sync_entry_from_scale)
        self.length_str_var.trace_add("write", self._sync_scale_from_entry)
        self.exclude_custom_var.trace_add(
            "write", lambda *_: self.on_settings_changed()
        )

        self.update_generate_button()
        self.update_strength_display()

        # Generate one immediately so the UI never opens with an empty field.
        self.generate_password()

    # ------------------------------------------------------------------
    # Icon helpers
    # ------------------------------------------------------------------
    def load_icon(self, path, size):
        """Load and resize an icon safely. Returns None if unavailable so
        callers can fall back to a text button instead of crashing."""
        try:
            if PIL_AVAILABLE:
                img = Image.open(path).convert("RGBA")
                img = img.resize((size, size), Image.LANCZOS)
                return ImageTk.PhotoImage(img)

            # No PIL available: PhotoImage only supports integer zoom/subsample,
            # so we approximate the requested size.
            img = PhotoImage(file=path)
            current_w = img.width() or size
            if current_w > size:
                factor = max(1, round(current_w / size))
                img = img.subsample(factor, factor)
            elif current_w < size:
                factor = max(1, round(size / current_w))
                img = img.zoom(factor, factor)
            return img
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Scrolling helpers
    # ------------------------------------------------------------------
    def _smooth_scroll_windows(self, event):
        """Handles <MouseWheel> on Windows and macOS.

        Windows reports event.delta in multiples of 120 per notch; macOS
        reports small per-pixel-ish deltas. Either way we convert it into a
        fine-grained pixel scroll (canvas yscrollincrement is set to 1px)
        so the motion feels continuous instead of jumping row-by-row.
        """
        notches = event.delta / 120 if abs(event.delta) >= 120 else event.delta
        self.options_canvas.yview_scroll(int(-notches * self.SCROLL_SPEED), "units")
        return "break"

    def _smooth_scroll_linux_up(self, event):
        self.options_canvas.yview_scroll(-self.SCROLL_SPEED, "units")
        return "break"

    def _smooth_scroll_linux_down(self, event):
        self.options_canvas.yview_scroll(self.SCROLL_SPEED, "units")
        return "break"

    def setup_smooth_scrolling(self, root_widget, canvas):
        """Make the mouse wheel scroll `canvas` no matter which widget under
        `root_widget` the cursor happens to be hovering over - labels,
        checkboxes, entries, buttons, all of it - the way scrolling works
        on a normal web page. Call this once, after every child widget under
        root_widget has already been created.
        """
        # 1px increments turn each wheel notch into a smooth pixel-scroll
        # instead of a chunky "jump to next widget" scroll.
        canvas.configure(yscrollincrement=1)

        def bind_recursive(widget):
            widget.bind("<MouseWheel>", self._smooth_scroll_windows, add="+")
            widget.bind("<Button-4>", self._smooth_scroll_linux_up, add="+")
            widget.bind("<Button-5>", self._smooth_scroll_linux_down, add="+")
            for child in widget.winfo_children():
                bind_recursive(child)

        bind_recursive(root_widget)

    def resize_scroll_frame(self, event):
        """Keep the inner frame the same width as the canvas."""
        self.options_canvas.itemconfigure(self.canvas_window, width=event.width)

    def update_scroll_region(self, event=None):
        self.options_canvas.configure(scrollregion=self.options_canvas.bbox("all"))

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def create_widgets(self):
        outer = Frame(self.master, bg=self.colors["bg"])
        outer.pack(fill="both", expand=True, padx=20, pady=20)

        # ---------- Header: title/subtitle on the left, social on the right ----------
        header = Frame(outer, bg=self.colors["bg"])
        header.pack(fill="x", pady=(0, 16))
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)

        header_left = Frame(header, bg=self.colors["bg"])
        header_left.grid(row=0, column=0, sticky="w")

        title_label = Label(
            header_left,
            text="Advanced Password Generator",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=self.title_font,
        )
        title_label.pack(anchor="w")

        subtitle_label = Label(
            header_left,
            text="Secure generation, validation, strength feedback, and clipboard support",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=self.small_font,
        )
        subtitle_label.pack(anchor="w", pady=(4, 0))

        header_right = Frame(header, bg=self.colors["bg"])
        header_right.grid(row=0, column=1, sticky="ne")
        self.build_social_icons(header_right)

        # ---------- Main content ----------
        content = Frame(outer, bg=self.colors["bg"])
        content.pack(fill="both", expand=True)

        left_panel = Frame(
            content,
            bg=self.colors["panel"],
            bd=0,
            highlightthickness=1,
            highlightbackground=self.colors["entry_border"],
        )
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_panel = Frame(
            content,
            bg=self.colors["panel_alt"],
            width=280,
            bd=0,
            highlightthickness=1,
            highlightbackground=self.colors["entry_border"],
        )
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        self.build_left_panel(left_panel)
        self.build_right_panel(right_panel)

        # Bind this last, once every widget in the left panel exists, so the
        # wheel scrolls the character-set list no matter where the cursor is
        # hovering inside the panel - over text, checkboxes, entries, etc.
        self.setup_smooth_scrolling(left_panel, self.options_canvas)

    def build_social_icons(self, parent):
        Label(
            parent,
            text="Follow",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=self.small_font,
        ).pack(side="left", padx=(0, 8))

        icons = Frame(parent, bg=self.colors["bg"])
        icons.pack(side="left")

        self.make_social_button(icons, self.github_icon, "GH", self.github_url)
        self.make_social_button(icons, self.telegram_icon, "TG", self.telegram_url)
        self.make_social_button(icons, self.linkedin_icon, "in", self.linkedin_url)

    def make_social_button(self, parent, icon, fallback_text, url):
        common_kwargs = dict(
            command=lambda: self.open_link(url),
            bg=self.colors["bg"],
            activebackground=self.colors["panel"],
            bd=0,
            relief="flat",
            cursor="hand2",
            highlightthickness=0,
        )

        if icon is not None:
            btn = Button(parent, image=icon, **common_kwargs)
            btn.image = icon  # keep a reference so it isn't garbage collected
        else:
            btn = Button(
                parent,
                text=fallback_text,
                fg=self.colors["text"],
                font=self.icon_fallback_font,
                width=3,
                **common_kwargs,
            )

        btn.pack(side="left", padx=3)
        btn.bind("<Enter>", lambda e: btn.config(bg=self.colors["panel"]))
        btn.bind("<Leave>", lambda e: btn.config(bg=self.colors["bg"]))
        return btn

    def build_left_panel(self, parent):
        section = Frame(parent, bg=self.colors["panel"])
        section.pack(fill="both", expand=True, padx=20, pady=20)

        # ==========================
        # Password
        # ==========================
        Label(
            section,
            text="Generated Password",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=self.label_bold_font,
        ).pack(anchor="w")

        password_row = Frame(section, bg=self.colors["panel"])
        password_row.pack(fill="x", pady=(8, 10))

        self.password_entry = Entry(
            password_row,
            textvariable=self.password_var,
            bg=self.colors["entry_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            readonlybackground=self.colors["entry_bg"],
            relief="flat",
            bd=8,
            font=self.password_font,
        )
        self.password_entry.pack(side="left", fill="x", expand=True)
        self.password_entry.configure(state="readonly")

        self.strength_label = Label(
            section,
            textvariable=self.strength_var,
            bg=self.colors["panel"],
            fg=self.colors["muted"],
            font=self.label_font,
        )
        self.strength_label.pack(anchor="w")

        self.strength_bar_canvas = Canvas(
            section,
            height=6,
            bg=self.colors["entry_bg"],
            highlightthickness=0,
            bd=0,
        )
        self.strength_bar_canvas.pack(fill="x", pady=(6, 15))

        # ==========================
        # Length
        # ==========================
        length_row = Frame(section, bg=self.colors["panel"])
        length_row.pack(fill="x")

        Label(
            length_row,
            text="Password Length",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=self.label_bold_font,
        ).pack(side="left")

        vcmd = (self.master.register(self._validate_length_input), "%P")
        self.length_entry = Entry(
            length_row,
            textvariable=self.length_str_var,
            width=8,
            justify="center",
            bg=self.colors["entry_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            bd=6,
            font=self.label_font,
            validate="key",
            validatecommand=vcmd,
        )
        self.length_entry.pack(side="right")
        self.length_entry.bind("<FocusOut>", lambda e: self._clamp_length_entry())
        self.length_entry.bind("<Return>", lambda e: self._clamp_length_entry())

        self.length_scale = Scale(
            section,
            from_=self.MIN_LENGTH,
            to=self.MAX_LENGTH,
            orient="horizontal",
            variable=self.length_var,
            showvalue=False,
            highlightthickness=0,
            relief="flat",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            troughcolor=self.colors["entry_bg"],
            activebackground=self.colors["accent"],
            command=lambda e: self.on_settings_changed(),
        )
        self.length_scale.pack(fill="x", pady=(8, 18))

        # ===========================================================
        # Scrollable Character Options
        # ===========================================================
        Label(
            section,
            text="Character Sets",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=self.label_bold_font,
        ).pack(anchor="w")

        container = Frame(section, bg=self.colors["panel"])
        container.pack(fill="both", expand=True, pady=(8, 12))

        self.options_canvas = Canvas(
            container, bg=self.colors["panel"], highlightthickness=0, bd=0
        )
        scrollbar = Scrollbar(
            container, orient="vertical", command=self.options_canvas.yview
        )
        self.options_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.options_canvas.pack(side="left", fill="both", expand=True)

        self.options_frame = Frame(self.options_canvas, bg=self.colors["panel"])
        self.canvas_window = self.options_canvas.create_window(
            (0, 0), window=self.options_frame, anchor="nw"
        )

        self.options_frame.bind("<Configure>", self.update_scroll_region)
        self.options_canvas.bind("<Configure>", self.resize_scroll_frame)

        self.make_checkbutton(
            self.options_frame, "Include Uppercase (A-Z)", self.uppercase_var
        ).pack(anchor="w", pady=4)
        self.make_checkbutton(
            self.options_frame, "Include Lowercase (a-z)", self.lowercase_var
        ).pack(anchor="w", pady=4)
        self.make_checkbutton(
            self.options_frame, "Include Numbers (0-9)", self.numbers_var
        ).pack(anchor="w", pady=4)
        self.make_checkbutton(
            self.options_frame,
            "Include Special Characters (!@#$...)",
            self.special_var,
        ).pack(anchor="w", pady=4)
        self.make_checkbutton(
            self.options_frame,
            "Exclude Ambiguous (O 0 l I 1)",
            self.exclude_ambiguous_var,
        ).pack(anchor="w", pady=4)
        self.make_checkbutton(
            self.options_frame,
            "Require One Character From Every Selected Group",
            self.require_each_selected_var,
        ).pack(anchor="w", pady=4)

        exclude_row = Frame(self.options_frame, bg=self.colors["panel"])
        exclude_row.pack(anchor="w", pady=(8, 4), fill="x")
        Label(
            exclude_row,
            text="Exclude specific characters:",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=self.label_font,
        ).pack(anchor="w")
        Entry(
            exclude_row,
            textvariable=self.exclude_custom_var,
            bg=self.colors["entry_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            bd=6,
            font=self.label_font,
        ).pack(fill="x", pady=(4, 0))

        # ===========================================================
        # Bottom Buttons
        # ===========================================================
        bottom = Frame(section, bg=self.colors["panel"])
        bottom.pack(fill="x")

        left_buttons = Frame(bottom, bg=self.colors["panel"])
        left_buttons.pack(side="left")

        self.generate_button = self.make_button(
            left_buttons,
            "Generate Password",
            self.generate_password,
            self.colors["accent"],
            self.colors["accent_hover"],
        )
        self.generate_button.pack()

        right_buttons = Frame(bottom, bg=self.colors["panel"])
        right_buttons.pack(side="right")

        self.copy_button = self.make_button(
            right_buttons,
            "Copy",
            self.copy_to_clipboard,
            self.colors["entry_bg"],
            self.colors["panel_alt"],
            small=True,
        )
        self.copy_button.pack(fill="x")

        self.clear_button = self.make_button(
            right_buttons,
            "Clear",
            self.clear_password,
            self.colors["danger"],
            self.colors["danger_hover"],
            small=True,
        )
        self.clear_button.pack(fill="x", pady=(8, 0))

        self.status_label = Label(
            section,
            textvariable=self.status_var,
            bg=self.colors["panel"],
            fg=self.colors["muted"],
            justify="left",
            wraplength=560,
            font=self.small_font,
        )
        self.status_label.pack(anchor="w", pady=(18, 0))

    def make_button(self, parent, text, command, bg, hover_bg, small=False):
        btn = Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg="white" if bg != self.colors["entry_bg"] else self.colors["text"],
            activebackground=hover_bg,
            activeforeground=(
                "white" if bg != self.colors["entry_bg"] else self.colors["text"]
            ),
            relief="flat",
            bd=0,
            padx=18 if not small else 20,
            pady=10 if not small else 8,
            cursor="hand2",
            font=self.label_bold_font,
            disabledforeground=self.colors["muted"],
        )
        btn.bind(
            "<Enter>",
            lambda e: (
                btn.config(bg=hover_bg) if str(btn["state"]) != "disabled" else None
            ),
        )
        btn.bind(
            "<Leave>",
            lambda e: btn.config(bg=bg) if str(btn["state"]) != "disabled" else None,
        )
        return btn

    def build_right_panel(self, parent):
        section = Frame(parent, bg=self.colors["panel_alt"])
        section.pack(fill="both", expand=True, padx=18, pady=20)

        info_title = Label(
            section,
            text="Quality Guide",
            bg=self.colors["panel_alt"],
            fg=self.colors["text"],
            font=self.label_bold_font,
        )
        info_title.pack(anchor="w", pady=(0, 10))

        tips = [
            "Use at least 12-16 characters.",
            "Mix uppercase, lowercase, numbers, and symbols.",
            "Avoid reusing passwords across accounts.",
            "Exclude ambiguous characters when readability matters.",
            "Use a password manager for storage.",
        ]
        for tip in tips:
            Label(
                section,
                text=f"• {tip}",
                bg=self.colors["panel_alt"],
                fg=self.colors["muted"],
                font=self.small_font,
                wraplength=230,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=4)

        shortcut_title = Label(
            section,
            text="Shortcuts",
            bg=self.colors["panel_alt"],
            fg=self.colors["text"],
            font=self.label_bold_font,
        )
        shortcut_title.pack(anchor="w", pady=(16, 10))

        shortcuts = [
            "Enter: Generate password",
            "Ctrl+C: Copy generated password",
        ]
        for item in shortcuts:
            Label(
                section,
                text=f"• {item}",
                bg=self.colors["panel_alt"],
                fg=self.colors["muted"],
                font=self.small_font,
                wraplength=230,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=4)

        self.master.bind("<Return>", lambda _event: self.generate_password())
        self.master.bind("<Control-c>", lambda _event: self.copy_to_clipboard())

    def open_link(self, url):
        try:
            open_new_tab(url)
        except Exception:
            messagebox.showerror("Could Not Open Link", f"Unable to open:\n{url}")

    def make_checkbutton(self, parent, text, variable):
        return Checkbutton(
            parent,
            text=text,
            variable=variable,
            bg=self.colors["panel"],
            fg=self.colors["text"],
            activebackground=self.colors["panel"],
            activeforeground=self.colors["text"],
            selectcolor=self.colors["entry_bg"],
            font=self.label_font,
            command=self.on_settings_changed,
            anchor="w",
            justify="left",
        )

    # ------------------------------------------------------------------
    # Length entry <-> scale sync (bug fix: no more TclError on bad input)
    # ------------------------------------------------------------------
    def _validate_length_input(self, proposed):
        if proposed == "":
            return True
        if not proposed.isdigit():
            return False
        return len(proposed) <= len(str(self.MAX_LENGTH))

    def _sync_scale_from_entry(self, *_args):
        text = self.length_str_var.get()
        if text.isdigit():
            value = int(text)
            if (
                self.MIN_LENGTH <= value <= self.MAX_LENGTH
                and value != self.length_var.get()
            ):
                self.length_var.set(value)
        self.on_settings_changed()

    def _sync_entry_from_scale(self, *_args):
        value = self.length_var.get()
        if self.length_str_var.get() != str(value):
            self.length_str_var.set(str(value))

    def _clamp_length_entry(self):
        text = self.length_str_var.get()
        if not text.isdigit():
            value = self.MIN_LENGTH
        else:
            value = max(self.MIN_LENGTH, min(self.MAX_LENGTH, int(text)))
        self.length_str_var.set(str(value))
        self.length_var.set(value)

    # ------------------------------------------------------------------
    # Settings / validation
    # ------------------------------------------------------------------
    def on_settings_changed(self):
        self.update_generate_button()
        self.update_strength_display()

    def get_current_length(self):
        text = self.length_str_var.get()
        if not text.isdigit():
            return None
        return int(text)

    def update_generate_button(self):
        selected_count = sum(
            [
                self.uppercase_var.get(),
                self.lowercase_var.get(),
                self.numbers_var.get(),
                self.special_var.get(),
            ]
        )

        if selected_count < 1:
            self.generate_button.config(state="disabled")
            self.set_status("Select at least one character group.", self.colors["warn"])
            return

        length = self.get_current_length()
        if length is None:
            self.generate_button.config(state="disabled")
            self.set_status(
                f"Length must be a number between {self.MIN_LENGTH} and {self.MAX_LENGTH}.",
                self.colors["warn"],
            )
            return

        if length < self.MIN_LENGTH or length > self.MAX_LENGTH:
            self.generate_button.config(state="disabled")
            self.set_status(
                f"Length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH}.",
                self.colors["warn"],
            )
            return

        if self.require_each_selected_var.get() and length < selected_count:
            self.generate_button.config(state="disabled")
            self.set_status(
                "Length is too short to include each selected character group.",
                self.colors["warn"],
            )
            return

        # Warn (but don't block) if the exclude list wipes out a selected group entirely.
        groups = self.get_character_groups()
        if not groups or all(len(g) == 0 for g in groups):
            self.generate_button.config(state="disabled")
            self.set_status(
                "Your excluded characters removed every available character.",
                self.colors["danger"],
            )
            return

        self.generate_button.config(state="normal")
        self.set_status("Ready to generate a secure password.", self.colors["muted"])

    def set_status(self, text, color):
        self.status_var.set(text)
        if hasattr(self, "status_label"):
            self.status_label.config(fg=color)

    def get_character_groups(self):
        uppercase_chars = ascii_uppercase
        lowercase_chars = ascii_lowercase
        number_chars = digits
        special_chars = punctuation

        if self.exclude_ambiguous_var.get():
            ambiguous = {"O", "0", "I", "l", "1"}
            uppercase_chars = "".join(
                ch for ch in uppercase_chars if ch not in ambiguous
            )
            lowercase_chars = "".join(
                ch for ch in lowercase_chars if ch not in ambiguous
            )
            number_chars = "".join(ch for ch in number_chars if ch not in ambiguous)
            special_chars = "".join(ch for ch in special_chars if ch not in ambiguous)

        custom_exclude = set(self.exclude_custom_var.get())
        if custom_exclude:
            uppercase_chars = "".join(
                ch for ch in uppercase_chars if ch not in custom_exclude
            )
            lowercase_chars = "".join(
                ch for ch in lowercase_chars if ch not in custom_exclude
            )
            number_chars = "".join(
                ch for ch in number_chars if ch not in custom_exclude
            )
            special_chars = "".join(
                ch for ch in special_chars if ch not in custom_exclude
            )

        groups = []
        if self.uppercase_var.get():
            groups.append(uppercase_chars)
        if self.lowercase_var.get():
            groups.append(lowercase_chars)
        if self.numbers_var.get():
            groups.append(number_chars)
        if self.special_var.get():
            groups.append(special_chars)

        # Drop any group that ended up empty after exclusions so it can't be
        # picked from (and won't break the "require each group" guarantee).
        return [g for g in groups if g]

    # ------------------------------------------------------------------
    # Core actions
    # ------------------------------------------------------------------
    def generate_password(self):
        self.update_generate_button()
        if str(self.generate_button["state"]) == "disabled":
            return

        groups = self.get_character_groups()
        if not groups:
            messagebox.showerror(
                "Invalid Selection", "Please select at least one character group."
            )
            return

        length = self.get_current_length()
        if length is None:
            messagebox.showerror(
                "Invalid Length", "Password length must be a valid number."
            )
            return

        all_characters = "".join(groups)
        if not all_characters:
            messagebox.showerror(
                "Invalid Character Pool",
                "No characters are available for password generation.",
            )
            return

        password_chars = []
        if self.require_each_selected_var.get():
            for group in groups:
                password_chars.append(choice(group))

        remaining_length = max(0, length - len(password_chars))
        password_chars.extend(choice(all_characters) for _ in range(remaining_length))

        # If "require each group" pushed us over the requested length
        # (shouldn't happen given the validation above, but guard anyway).
        if len(password_chars) > length:
            password_chars = password_chars[:length]

        self.shuffle_list(password_chars)

        password = "".join(password_chars)
        self.password_var.set(password)
        self.password_entry.configure(state="normal")
        self.password_entry.selection_range(0, END)
        self.password_entry.configure(state="readonly")

        self.update_strength_display(password)
        self.set_status("Password generated successfully.", self.colors["accent"])

    def shuffle_list(self, items):
        for index in range(len(items) - 1, 0, -1):
            swap_index = randbelow(index + 1)
            items[index], items[swap_index] = items[swap_index], items[index]

    def evaluate_strength(self, password):
        if not password:
            return "Strength: -", self.colors["muted"], 0

        score = 0
        length = len(password)

        if length >= 8:
            score += 1
        if length >= 12:
            score += 1
        if length >= 16:
            score += 1
        if length >= 24:
            score += 1
        if any(ch in ascii_uppercase for ch in password):
            score += 1
        if any(ch in ascii_lowercase for ch in password):
            score += 1
        if any(ch in digits for ch in password):
            score += 1
        if any(ch in punctuation for ch in password):
            score += 1

        max_score = 8
        if score <= 3:
            label, color = "Strength: Weak", self.colors["danger"]
        elif score <= 5:
            label, color = "Strength: Medium", self.colors["warn"]
        elif score <= 6:
            label, color = "Strength: Strong", self.colors["accent"]
        else:
            label, color = "Strength: Very Strong", self.colors["accent"]

        return label, color, score / max_score

    def update_strength_display(self, password=None):
        if password is None:
            password = self.password_var.get()

        text, color, ratio = self.evaluate_strength(password)
        self.strength_var.set(text)
        self.strength_label.config(fg=color)
        self.draw_strength_bar(ratio, color)

    def draw_strength_bar(self, ratio, color):
        canvas = self.strength_bar_canvas
        canvas.delete("all")
        width = canvas.winfo_width() or 600
        height = int(canvas["height"])
        canvas.create_rectangle(
            0, 0, width, height, fill=self.colors["entry_bg"], width=0
        )
        fill_width = int(width * max(0.0, min(1.0, ratio)))
        if fill_width > 0:
            canvas.create_rectangle(0, 0, fill_width, height, fill=color, width=0)

    def copy_to_clipboard(self):
        password = self.password_var.get()
        if not password:
            messagebox.showwarning("Nothing to Copy", "Generate a password first.")
            return

        self.master.clipboard_clear()
        self.master.clipboard_append(password)
        self.master.update()
        self.set_status("Password copied to clipboard.", self.colors["accent"])

        original_text = "Copy"
        self.copy_button.config(text="Copied!")
        if self._copy_reset_job is not None:
            self.master.after_cancel(self._copy_reset_job)
        self._copy_reset_job = self.master.after(
            1500, lambda: self.copy_button.config(text=original_text)
        )

    def clear_password(self):
        self.password_var.set("")
        self.update_strength_display("")
        self.set_status("Password cleared.", self.colors["muted"])


if __name__ == "__main__":
    root = Tk()
    app = PasswordGeneratorApp(root)
    root.mainloop()
