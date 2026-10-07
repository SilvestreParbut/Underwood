import copy
import curses
import gettext
import os
import re
import select
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata


# ============================================================
# INTERNACIONALIZACIÓN (i18n)
# ============================================================

def get_locale_dir():
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "locale")


def current_language():
    config_path = os.path.expanduser("~/.config/underwood/language")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            pref = f.read().strip().lower()
            if pref in ("es", "en"):
                return pref
    except Exception:
        pass

    forced = os.environ.get("UNDERWOOD_LANG", "").strip().lower()
    if forced in ("es", "en"):
        return forced

    lang = os.environ.get("LANG", "").strip().lower()
    if lang.startswith("en"):
        return "en"

    return "es"


def save_language_preference(code):
    config_dir = os.path.expanduser("~/.config/underwood")
    config_path = os.path.join(config_dir, "language")
    try:
        os.makedirs(config_dir, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(code)
        return True
    except Exception:
        return False


def load_text_doc(name):
    lang = current_language()
    base = get_locale_dir()
    for candidate_lang in (lang, "es"):
        path = os.path.join(base, f"{name}.{candidate_lang}.txt")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            continue
        except Exception:
            continue
    return "(texto no disponible)"


def setup_i18n():
    lang = current_language()
    os.environ["LANGUAGE"] = lang
    try:
        os.environ.setdefault("LANG", f"{lang}_{lang.upper()}.UTF-8")
    except Exception:
        pass

    local_path = get_locale_dir()
    candidates = [
        local_path,
        os.path.expanduser("~/.local/share/locale"),
        "/usr/local/share/locale",
        "/usr/share/locale",
    ]
    chosen = "/usr/share/locale"
    for path in candidates:
        found = False
        for lc in ("en", "es"):
            mo = os.path.join(path, lc, "LC_MESSAGES", "underwood.mo")
            if os.path.isfile(mo):
                chosen = path
                found = True
                break
        if found:
            break

    try:
        gettext.bindtextdomain("underwood", chosen)
        gettext.textdomain("underwood")
        return gettext.gettext
    except Exception:
        return lambda s: s


_EN_FALLBACK = {
    "Archivo": "File",
    "Edición": "Edit",
    "Formato": "Format",
    "Alineación": "Alignment",
    "Capítulos": "Add chapters",
    "Ayuda": "Help",
    "Idioma": "Language",
    "Salir": "Quit",
    "Nuevo documento": "New document",
    "Abrir documento…": "Open document…",
    "Guardar": "Save",
    "Guardar como…": "Save as…",
    "Guardar como .docx…": "Save as .docx…",
    "Guardar como .md…": "Save as .md…",
    "Nombre para .md (se guarda en ~/underwood/):":
        "Name for .md (saved in ~/underwood/):",
    "Guardando .md… %s": "Saving .md… %s",
    "Exportar a PDF": "Export to PDF",
    "Seleccionar todo": "Select all",
    "Deshacer": "Undo",
    "Copiar": "Copy",
    "Cortar": "Cut",
    "Pegar": "Paste",
    "Buscar": "Find",
    "Reemplazar": "Replace",
    "Corrector ortográfico": "Spell checker",
    "Negrita": "Bold",
    "Cursiva": "Italic",
    "Subrayado": "Underline",
    "Izquierda": "Left",
    "Centrada": "Center",
    "Derecha": "Right",
    "Justificada": "Justify",
    "Salto de página": "Page break",
    "Crear capítulo": "Add chapter",
    "Crear sección": "Add section",
    "Crear subsección": "Add subsection",
    "Quitar nivel de título": "Remove heading level",
    "Mapa de capítulos": "Chapter map",
    "Nivel %d aplicado": "Level %d applied",
    "Nivel quitado": "Level removed",
    "Nuevo capítulo": "New chapter",
    "Saltado a: %s": "Jumped to: %s",
    "(sin capítulos — usa Capítulos → Insertar capítulo)":
        "(no chapters — use Add chapter → Chapter)",
    " ↑↓ mover · Enter ir · n: nuevo · Esc cerrar ":
        " ↑↓ move · Enter go · n: new · Esc close ",
    " Mapa de capítulos ": " Chapter map ",
    "Manual": "Manual",
    "Acerca de": "About",
    "Nombre (se guarda en ~/underwood/):":
        "Name (saved in ~/underwood/):",
    "Nombre para .docx (se guarda en ~/underwood/):":
        "Name for .docx (saved in ~/underwood/):",
    "Guardar como:": "Save as:",
    "Buscar:": "Find:",
    "Reemplazar con:": "Replace with:",
    "Abierto: %s": "Opened: %s",
    "Guardado: %s": "Saved: %s",
    "Error al guardar": "Error saving",
    "No se puede crear carpeta": "Cannot create folder",
    "Deshecho": "Undone",
    "Nada que deshacer": "Nothing to undo",
    "Copiado": "Copied",
    "Cortado": "Cut",
    "Pegado": "Pasted",
    "No encontrado": "Not found",
    "1 reemplazo": "1 replacement",
    "%d reemplazos": "%d replacements",
    "PDF: %s": "PDF: %s",
    "Exportando a PDF… %s": "Exporting to PDF… %s",
    "Guardando .docx… %s": "Saving .docx… %s",
    "Ya hay una exportación en curso": "An export is already running",
    "Ya hay un guardado en curso": "A save is already running",
    "LibreOffice no instalado": "LibreOffice not installed",
    "hunspell no instalado": "hunspell not installed",
    "Ortografía activada": "Spell check on",
    "Ortografía desactivada": "Spell check off",
    "Ortografía: ": "Spelling: ",
    "Ortografía ✓": "Spell ✓",
    "Ya estás en ese idioma": "Already in that language",
    "Seleccionado todo: %d líneas · %d palabras":
        "Selected all: %d lines · %d words",
    "Palabras: %d": "Words: %d",
    "Manual de Underwood": "Underwood Manual",
    "↑↓ desplazar  ·  Esc para volver":
        "↑↓ scroll  ·  Esc to go back",
    "Error: ": "Error: ",
    "Error al copiar: ": "Copy error: ",
    "Error al generar PDF": "Error generating PDF",
    "Error al guardar .docx": "Error saving .docx",
    " Enter: abrir  ·  Retroceso: subir  ·  Esc: cancelar ":
        " Enter: open  ·  Backspace: up  ·  Esc: cancel ",
    " Abrir documento ": " Open document ",
    "Herramientas: F9": "Tools: F9",
    "Selección: Shift→": "Selection: Shift→",
    "Selección: Ctrl+Space": "Selection: Ctrl+Space",
    "Selección iniciada": "Selection started",
    "Selección terminada": "Selection ended",
}

_gettext_fn = setup_i18n()


def tr(s):
    try:
        result = _gettext_fn(s)
    except Exception:
        result = s
    if result == s and s in _EN_FALLBACK:
        try:
            if current_language() == "en":
                return _EN_FALLBACK[s]
        except Exception:
            pass
    return result


STATUS_DURATION = 1.6
TEXT_WIDTH = 80
MAX_UNDO = 300

BOLD = 1
ITALIC = 2
UNDERLINE = 4

# Niveles de título (capítulos) — bits libres de `attrs`
H1 = 8
H2 = 16
H3 = 32
HEADING_MASK = H1 | H2 | H3

ALIGN_LEFT = 0
ALIGN_CENTER = 1
ALIGN_RIGHT = 2
ALIGN_JUSTIFY = 3

PAGE_BREAK = "\x0c"

MENU_SEPARATOR = " │ "

TITLE_ROW = 0
SEP_TITLE_ROW = 1
MENU_ROW = 2
SEP_TOP_ROW = 3
DROPDOWN_ROW = 3
TEXT_TOP = 4

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

internal_clipboard = ""
internal_rich_clipboard = []

_COLORS_READY = False
_USE_256 = False
_TTY_MODE = False


MENUS = [
    (tr("Archivo"), [
        (tr("Nuevo documento"),  "Ctrl+N", "NEW"),
        (tr("Abrir documento…"), "Ctrl+O", "OPEN"),
        None,
        (tr("Guardar"),          "Ctrl+S", "SAVE"),
        (tr("Guardar como…"),    "Ctrl+W", "SAVE_AS"),
        (tr("Guardar como .docx…"), "",    "SAVE_AS_DOCX"),
        (tr("Guardar como .md…"),   "",    "SAVE_AS_MD"),
        (tr("Exportar a PDF"),   "Ctrl+P", "PDF"),
        None,
        (tr("Salir"),            "Ctrl+Q", "QUIT"),
    ]),
    (tr("Edición"), [
        (tr("Seleccionar todo"), "Ctrl+A", "SELECT_ALL"),
        None,
        (tr("Deshacer"),   "Ctrl+Z", "UNDO"),
        None,
        (tr("Copiar"),     "Ctrl+C", "COPY"),
        (tr("Cortar"),     "Ctrl+X", "CUT"),
        (tr("Pegar"),      "Ctrl+V", "PASTE"),
        None,
        (tr("Buscar"),     "Ctrl+F", "FIND"),
        (tr("Reemplazar"), "Ctrl+R", "REPLACE"),
        None,
        (tr("Corrector ortográfico"), "F7", "SPELL"),
    ]),
    (tr("Formato"), [
        (tr("Negrita"),   "Ctrl+B", "BOLD"),
        (tr("Cursiva"),   "Ctrl+I", "ITALIC"),
        (tr("Subrayado"), "Ctrl+U", "UNDERLINE"),
    ]),
    (tr("Alineación"), [
        (tr("Izquierda"),   "Ctrl+L", "ALIGN_LEFT"),
        (tr("Centrada"),    "Ctrl+E", "ALIGN_CENTER"),
        (tr("Derecha"),     "Ctrl+D", "ALIGN_RIGHT"),
        (tr("Justificada"), "Ctrl+J", "ALIGN_JUSTIFY"),
    ]),
    (tr("Capítulos"), [
        (tr("Crear capítulo"),   "F2", "H1"),
        (tr("Crear sección"),    "F3", "H2"),
        (tr("Crear subsección"), "F4", "H3"),
        (tr("Quitar nivel de título"), "F6", "H0"),
        None,
        (tr("Mapa de capítulos"),    "Ctrl+T", "CHAPTERS"),
        None,
        (tr("Salto de página"),      "Ctrl+K", "PAGEBREAK"),
    ]),
    (tr("Ayuda"), [
        (tr("Manual"),    "Ctrl+G", "HELP"),
        (tr("Acerca de"), "Ctrl+H", "ABOUT"),
    ]),
    (tr("Idioma"), [
        ("Español", "", "LANG_ES"),
        ("English", "", "LANG_EN"),
    ]),
    (tr("Salir"), None),
]


MANUAL_TEXT = load_text_doc("manual")
ABOUT_TEXT = load_text_doc("about")


def _base_attr():
    if _COLORS_READY:
        try:
            return curses.color_pair(2)
        except Exception:
            return 0
    return 0


def curses_attr_for(attrs):
    a = _base_attr()
    if attrs & BOLD:
        a |= curses.A_BOLD
    if attrs & ITALIC:
        a |= getattr(curses, "A_ITALIC", 0)
    if attrs & UNDERLINE:
        a |= curses.A_UNDERLINE
    return a


def display_width(s):
    w = 0
    for ch in s:
        ea = unicodedata.east_asian_width(ch)
        if ea in ("W", "F"):
            w += 2
        else:
            w += 1
    return w


def truncate_display(s, max_width):
    result = ""
    w = 0
    for ch in s:
        cw = display_width(ch)
        if w + cw > max_width:
            break
        result += ch
        w += cw
    return result


def truncate_left(s, max_width):
    if max_width <= 0:
        return ""
    if display_width(s) <= max_width:
        return s
    result = ""
    w = 0
    for ch in reversed(s):
        cw = display_width(ch)
        if w + cw > max_width - 1:
            break
        result = ch + result
        w += cw
    return "…" + result


def count_words(document):
    text = document_to_string(document).replace(PAGE_BREAK, " ")
    return len(text.split())


# ============================================================
# CAPÍTULOS / MAPA DE CAPÍTULOS
# ============================================================

def get_line_heading_level(formatting, line_index):
    if line_index < 0 or line_index >= len(formatting):
        return 0
    fmt = formatting[line_index]
    if not fmt:
        return 0
    first = fmt[0]
    if first & H1:
        return 1
    if first & H2:
        return 2
    if first & H3:
        return 3
    return 0


def set_line_heading(formatting, line_index, level):
    if line_index < 0 or line_index >= len(formatting):
        return formatting
    fmt = formatting[line_index]
    new_fmt = []
    for attrs in fmt:
        attrs = attrs & ~HEADING_MASK
        if level == 1:
            attrs |= H1
        elif level == 2:
            attrs |= H2
        elif level == 3:
            attrs |= H3
        new_fmt.append(attrs)
    formatting[line_index] = new_fmt
    return formatting


def collect_headings(document, formatting):
    """Devuelve lista de (line_index, level, text)."""
    result = []
    for i, line in enumerate(document):
        level = get_line_heading_level(formatting, i)
        if level > 0 and line.strip():
            result.append((i, level, line.strip()))
    return result


def chapter_panel_geometry(width, height):
    box_w = min(72, max(40, width - 4))
    box_h = min(22, max(10, height - 4))
    box_x = max(0, (width - box_w) // 2)
    box_y = max(0, (height - box_h) // 2)
    list_start = box_y + 1
    list_height = box_h - 3
    return box_x, box_y, box_w, box_h, list_start, list_height


def draw_chapter_panel(stdscr, headings, index, scroll, width, height):
    box_x, box_y, box_w, box_h, list_start, list_height = (
        chapter_panel_geometry(width, height)
    )
    base = _base_attr()

    title = tr(" Mapa de capítulos ")
    top_bar_left = "┌─" + title
    top_bar_right = "─" * max(0, box_w - len(top_bar_left) - 1) + "┐"
    top_bar = (top_bar_left + top_bar_right)[:box_w]

    try:
        stdscr.addstr(box_y, box_x, top_bar, base | curses.A_BOLD)
    except curses.error:
        pass

    inner_w = box_w - 2
    spaces = " " * inner_w
    for i in range(1, box_h - 1):
        try:
            stdscr.addstr(box_y + i, box_x, "│", base)
            stdscr.addstr(box_y + i, box_x + 1, spaces, base)
            stdscr.addstr(box_y + i, box_x + box_w - 1, "│", base)
        except curses.error:
            pass

    list_x = box_x + 2
    list_w = box_w - 4

    if not headings:
        msg = truncate_display(
            tr("(sin capítulos — usa Capítulos → Crear capítulo)"), list_w
        )
        try:
            stdscr.addstr(list_start, list_x, msg, base)
        except curses.error:
            pass
    else:
        for i in range(list_height):
            entry_i = scroll + i
            if entry_i >= len(headings):
                break
            _line_index, level, text = headings[entry_i]
            indent = "    " * (level - 1)
            bullet = "▸ " if level == 1 else "· "
            display = indent + bullet + text
            display = truncate_display(display, list_w).ljust(list_w)

            attr = base
            if level == 1:
                attr |= curses.A_BOLD
            if entry_i == index:
                attr |= curses.A_REVERSE

            try:
                stdscr.addstr(list_start + i, list_x, display, attr)
            except curses.error:
                pass

    try:
        stdscr.addstr(box_y + box_h - 2, box_x + 1,
                      "─" * (box_w - 2), base)
    except curses.error:
        pass

    try:
        stdscr.addstr(box_y + box_h - 1, box_x, "│", base)
        stdscr.addstr(box_y + box_h - 1, box_x + 1, spaces, base)
        stdscr.addstr(box_y + box_h - 1, box_x + box_w - 1, "│", base)
    except curses.error:
        pass

    hints = tr(" ↑↓ mover · Enter ir · n: nuevo · Esc cerrar ")
    hints = truncate_display(hints, box_w - 4)
    hint_x = box_x + max(1, (box_w - len(hints)) // 2)
    try:
        stdscr.addstr(box_y + box_h - 1, hint_x, hints, base)
    except curses.error:
        pass


# ============================================================
# CORRECTOR ORTOGRÁFICO
# ============================================================

def _spell_tool():
    if shutil.which("hunspell"):
        return "hunspell"
    if shutil.which("aspell"):
        return "aspell"
    return None


def _dicts_for(lang):
    if lang == "es":
        return ["es_ES", "es_MX", "es", "es-ES"]
    return ["en_US", "en_GB", "en", "en-US"]


_WORD_PATTERN = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", re.UNICODE)


def run_spell_check(text, lang):
    tool = _spell_tool()
    if not tool:
        return None

    misspelled = set()
    ok = False
    for dict_name in _dicts_for(lang):
        try:
            if tool == "hunspell":
                cmd = ["hunspell", "-l", "-d", dict_name]
            else:
                cmd = ["aspell", "list", "--lang=" + dict_name]
            result = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=15
            )
            if result.returncode == 0:
                for line in result.stdout.decode(
                        "utf-8", errors="replace").splitlines():
                    w = line.strip()
                    if w:
                        misspelled.add(w.lower())
                ok = True
                break
        except Exception:
            continue

    if not ok:
        return None

    positions = []
    for m in _WORD_PATTERN.finditer(text):
        if m.group().lower() in misspelled:
            positions.append((m.start(), m.end()))
    return positions


def get_suggestions(word, lang):
    tool = _spell_tool()
    if not tool:
        return []
    for dict_name in _dicts_for(lang):
        try:
            if tool == "hunspell":
                cmd = ["hunspell", "-a", "-d", dict_name]
            else:
                cmd = ["aspell", "-a", "--lang=" + dict_name]
            result = subprocess.run(
                cmd,
                input=(word + "\n").encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=5
            )
            if result.returncode == 0:
                output = result.stdout.decode("utf-8", errors="replace")
                for line in output.splitlines():
                    if line.startswith("&"):
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            sugs = [s.strip()
                                    for s in parts[1].split(",")]
                            return [s for s in sugs if s][:5]
                    if line.startswith("#"):
                        return []
                return []
        except Exception:
            continue
    return []


# ============================================================
# EXPLORADOR DE ARCHIVOS
# ============================================================

BROWSE_EXTENSIONS = (".rtf", ".txt", ".docx", ".doc", ".md", ".markdown")


def list_directory(path):
    entries = []
    try:
        parent = os.path.dirname(os.path.abspath(path))
        if parent and parent != os.path.abspath(path):
            entries.append(("..", parent, True))

        dirs = []
        files = []
        for name in sorted(os.listdir(path)):
            if name.startswith("."):
                continue
            full = os.path.join(path, name)
            try:
                if os.path.isdir(full):
                    dirs.append((name, full, True))
                elif name.lower().endswith(BROWSE_EXTENSIONS):
                    files.append((name, full, False))
            except Exception:
                continue

        entries.extend(dirs)
        entries.extend(files)
    except Exception:
        pass
    return entries


def browser_box_geometry(width, height):
    box_w = min(72, max(40, width - 4))
    box_h = min(22, max(10, height - 4))
    box_x = max(0, (width - box_w) // 2)
    box_y = max(0, (height - box_h) // 2)
    return box_x, box_y, box_w, box_h


def draw_browser(stdscr, browse_dir, entries, index, scroll, width, height):
    box_x, box_y, box_w, box_h = browser_box_geometry(width, height)
    base = _base_attr()

    title = tr(" Abrir documento ")
    top_bar_left = "┌─" + title
    top_bar_right = "─" * max(0, box_w - len(top_bar_left) - 1) + "┐"
    top_bar = (top_bar_left + top_bar_right)[:box_w]

    try:
        stdscr.addstr(box_y, box_x, top_bar, base | curses.A_BOLD)
    except curses.error:
        pass

    inner_w = box_w - 2
    spaces = " " * inner_w
    for i in range(1, box_h - 1):
        try:
            stdscr.addstr(box_y + i, box_x, "│", base)
            stdscr.addstr(box_y + i, box_x + 1, spaces, base)
            stdscr.addstr(box_y + i, box_x + box_w - 1, "│", base)
        except curses.error:
            pass

    path_display = truncate_left(browse_dir, box_w - 4)
    try:
        stdscr.addstr(box_y + 1, box_x + 2, path_display, base)
    except curses.error:
        pass

    try:
        stdscr.addstr(box_y + 2, box_x + 1, "─" * (box_w - 2), base)
    except curses.error:
        pass

    list_start = box_y + 3
    list_height = box_h - 5
    list_x = box_x + 2
    list_w = box_w - 4

    for i in range(list_height):
        entry_i = scroll + i
        if entry_i >= len(entries):
            break
        name, full, is_dir = entries[entry_i]
        row_y = list_start + i
        selected = (entry_i == index)

        if is_dir:
            display = name + "/" if name != ".." else ".."
        else:
            display = name

        display = truncate_display(display, list_w).ljust(list_w)
        attr = base
        if is_dir:
            attr |= curses.A_BOLD
        if selected:
            attr |= curses.A_REVERSE

        try:
            stdscr.addstr(row_y, list_x, display, attr)
        except curses.error:
            pass

    try:
        stdscr.addstr(box_y + box_h - 2, box_x + 1,
                      "─" * (box_w - 2), base)
    except curses.error:
        pass

    hints = tr(" Enter: abrir  ·  Retroceso: subir  ·  Esc: cancelar ")
    hints = truncate_display(hints, box_w - 4)
    hint_x = box_x + max(1, (box_w - len(hints)) // 2)
    try:
        stdscr.addstr(box_y + box_h - 1, hint_x, hints, base)
    except curses.error:
        pass


# ============================================================
# ALINEACIÓN
# ============================================================

def get_line_align(alignments, line_index):
    if 0 <= line_index < len(alignments):
        return alignments[line_index]
    return ALIGN_LEFT


def compute_line_layout(text, text_width, align, is_last_subline):
    n = len(text)

    if align == ALIGN_CENTER:
        return text, max(0, (text_width - n) // 2), None

    if align == ALIGN_RIGHT:
        return text, max(0, text_width - n), None

    if align == ALIGN_JUSTIFY and not is_last_subline:
        words = [w for w in text.split(" ") if w]
        if len(words) >= 2:
            total_chars = sum(len(w) for w in words)
            gaps = len(words) - 1
            extra = text_width - total_chars - gaps

            if extra > 0:
                extra_per_gap = extra // gaps
                remainder = extra % gaps

                word_positions = []
                pos = 0
                for w in words:
                    idx = text.find(w, pos)
                    word_positions.append(idx)
                    pos = idx + len(w)

                result = []
                mapping = []
                for wi, w in enumerate(words):
                    wp = word_positions[wi]
                    for k, c in enumerate(w):
                        result.append(c)
                        mapping.append(wp + k)
                    if wi < len(words) - 1:
                        space_col = wp + len(w)
                        num = 1 + extra_per_gap
                        if wi < remainder:
                            num += 1
                        for _pad in range(num):
                            result.append(" ")
                            mapping.append(space_col)

                return "".join(result), 0, mapping

    return text, 0, None


def apply_alignment(document, alignments, cursor_line,
                    selection_start, selection_end, new_align):
    new_alignments = list(alignments)
    while len(new_alignments) < len(document):
        new_alignments.append(ALIGN_LEFT)
    while len(new_alignments) > len(document):
        new_alignments.pop()

    if selection_start is not None and selection_end is not None:
        selected = selection_range(document, selection_start, selection_end)
        if selected is not None:
            a, b = selected
            text = document_to_string(document)
            start_line, _unused = absolute_to_position(text, a)
            end_line, _unused = absolute_to_position(text, b)
            if b > a:
                before = text[:b]
                last_nl = before.rfind("\n")
                if last_nl == len(before) - 1 and end_line > start_line:
                    end_line -= 1
            for i in range(start_line, end_line + 1):
                if 0 <= i < len(new_alignments):
                    new_alignments[i] = new_align
    else:
        if 0 <= cursor_line < len(new_alignments):
            new_alignments[cursor_line] = new_align

    return new_alignments


# ============================================================
# BARRA DE MENÚS
# ============================================================

def menu_bar_total_width(menus):
    total = 0
    sep = MENU_SEPARATOR
    for i, (name, _items) in enumerate(menus):
        total += len(name)
        if i < len(menus) - 1:
            total += len(sep)
    return total


def menu_bar_layout(menus, width):
    total = menu_bar_total_width(menus)
    start_x = max(2, (width - total) // 2)
    layout = []
    x = start_x
    sep = MENU_SEPARATOR
    for i, (name, _items) in enumerate(menus):
        end = x + len(name)
        layout.append((name, x, end))
        x = end
        if i < len(menus) - 1:
            x += len(sep)
    return layout


def menu_index_at(menus, x, width):
    for i, (_name, start, end) in enumerate(menu_bar_layout(menus, width)):
        if start <= x < end:
            return i
    return -1


def dropdown_size(menu):
    max_label = 0
    max_shortcut = 0
    for item in menu:
        if item is None:
            continue
        label, shortcut, _action = item
        max_label = max(max_label, len(label))
        max_shortcut = max(max_shortcut, len(shortcut))
    return 1 + 1 + max_label + 2 + max_shortcut + 1 + 1


def dropdown_x(menu, menu_label_x, width):
    w = dropdown_size(menu)
    x = menu_label_x
    if x + w > width:
        x = max(0, width - w)
    return x


def dropdown_item_at(menu, mx, my, dx, dy):
    w = dropdown_size(menu)
    if mx < dx or mx >= dx + w:
        return -1
    if my <= dy or my >= dy + len(menu) + 2:
        return -1
    idx = my - dy - 1
    if idx < 0 or idx >= len(menu):
        return -1
    if menu[idx] is None:
        return -1
    return idx


def push_undo(undo_stack, document, formatting, alignments):
    undo_stack.append(
        (copy.deepcopy(document), copy.deepcopy(formatting),
         copy.deepcopy(alignments))
    )
    while len(undo_stack) > MAX_UNDO:
        undo_stack.pop(0)


# ============================================================
# LÍNEAS VISUALES
# ============================================================

def visual_lines(document, width):
    result = []
    for line_index, line in enumerate(document):
        if line == "":
            result.append((line_index, 0, ""))
            continue
        start = 0
        while start < len(line):
            remaining = line[start:]
            if len(remaining) <= width:
                result.append((line_index, start, remaining))
                break
            cut = remaining.rfind(" ", 0, width + 1)
            if cut <= 0:
                cut = width
            piece = remaining[:cut]
            result.append((line_index, start, piece))
            start += cut
            while start < len(line) and line[start] == " ":
                start += 1
    if not result:
        result.append((0, 0, ""))
    return result


def cursor_visual_position(document, cursor_line, cursor_col, width):
    lines = visual_lines(document, width)
    for row, (line_index, start, text) in enumerate(lines):
        if line_index != cursor_line:
            continue
        end = start + len(text)
        if start <= cursor_col <= end:
            return row, cursor_col - start
    last_row, (line_index, start, text) = len(lines) - 1, lines[-1]
    if line_index == cursor_line:
        return last_row, max(0, cursor_col - start)
    return 0, 0


def adjust_scroll(document, cursor_line, cursor_col, width,
                  visible_rows, scroll_row):
    cursor_row, _unused = cursor_visual_position(
        document, cursor_line, cursor_col, width)
    if cursor_row < scroll_row:
        scroll_row = cursor_row
    elif cursor_row >= scroll_row + visible_rows:
        scroll_row = cursor_row - visible_rows + 1
    return max(0, scroll_row)


def line_offsets(document):
    offsets = [0]
    total = 0
    for line in document:
        total += len(line) + 1
        offsets.append(total)
    return offsets


def position_to_absolute(document, line, col):
    absolute = 0
    for i in range(line):
        absolute += len(document[i]) + 1
    absolute += col
    return absolute


def absolute_to_position(text, absolute):
    before = text[:absolute]
    line = before.count("\n")
    last_newline = before.rfind("\n")
    if last_newline == -1:
        col = len(before)
    else:
        col = len(before) - last_newline - 1
    return line, col


def selection_range(document, start, end):
    if start is None or end is None:
        return None
    a = position_to_absolute(document, start[0], start[1])
    b = position_to_absolute(document, end[0], end[1])
    if a <= b:
        return a, b
    return b, a


def is_selected(document, line, col, selection_start, selection_end):
    selected = selection_range(document, selection_start, selection_end)
    if selected is None:
        return False
    current = position_to_absolute(document, line, col)
    return selected[0] <= current < selected[1]


def document_to_string(document):
    return "\n".join(document)


def string_to_document(text):
    return text.split("\n")


# ============================================================
# CELDAS
# ============================================================

def document_to_cells(document, formatting):
    cells = []
    for i, line in enumerate(document):
        if i < len(formatting):
            fmt_line = formatting[i]
        else:
            fmt_line = [0] * len(line)
        for j, ch in enumerate(line):
            attrs = fmt_line[j] if j < len(fmt_line) else 0
            cells.append((ch, attrs))
        if i < len(document) - 1:
            cells.append(("\n", 0))
    return cells


def cells_to_document(cells):
    document = []
    formatting = []
    line_chars = []
    line_fmt = []
    for ch, attrs in cells:
        if ch == "\n":
            document.append("".join(line_chars))
            formatting.append(line_fmt)
            line_chars = []
            line_fmt = []
        else:
            line_chars.append(ch)
            line_fmt.append(attrs)
    document.append("".join(line_chars))
    formatting.append(line_fmt)
    return document, formatting


def text_to_cells(text, attrs=0):
    cells = []
    for ch in text:
        if ch == "\n":
            cells.append(("\n", 0))
        else:
            cells.append((ch, attrs))
    return cells


def cells_to_text(cells):
    return "".join(ch for ch, _attrs in cells)


def selected_cells(document, formatting, start, end):
    selected = selection_range(document, start, end)
    if selected is None:
        return []
    a, b = selected
    cells = document_to_cells(document, formatting)
    return cells[a:b]


def delete_selection_rich(document, formatting, alignments, start, end):
    selected = selection_range(document, start, end)
    if selected is None:
        return document, formatting, alignments, 0, 0

    a, b = selected
    text = document_to_string(document)
    start_line, _unused = absolute_to_position(text, a)

    cells = document_to_cells(document, formatting)
    del cells[a:b]

    new_doc, new_fmt = cells_to_document(cells)
    n_removed = len(document) - len(new_doc)

    before = cells_to_text(cells[:a])
    new_line = before.count("\n")
    last_newline = before.rfind("\n")
    if last_newline == -1:
        new_col = len(before)
    else:
        new_col = len(before) - last_newline - 1

    new_align = list(alignments)
    while len(new_align) < len(document):
        new_align.append(ALIGN_LEFT)

    keep_align = get_line_align(alignments, start_line)
    head = new_align[:start_line]
    tail = new_align[start_line + n_removed + 1:]
    new_align = head + [keep_align] + tail

    while len(new_align) < len(new_doc):
        new_align.append(ALIGN_LEFT)
    new_align = new_align[:len(new_doc)]

    return new_doc, new_fmt, new_align, new_line, new_col


def insert_cells_at_cursor(document, formatting, alignments, line, col, cells):
    absolute = position_to_absolute(document, line, col)
    all_cells = document_to_cells(document, formatting)
    all_cells[absolute:absolute] = cells

    new_doc, new_fmt = cells_to_document(all_cells)
    n_added = len(new_doc) - len(document)

    new_align = list(alignments)
    while len(new_align) < len(document):
        new_align.append(ALIGN_LEFT)
    for _i in range(n_added):
        new_align.insert(line + 1, ALIGN_LEFT)
    while len(new_align) < len(new_doc):
        new_align.append(ALIGN_LEFT)
    new_align = new_align[:len(new_doc)]

    after = cells_to_text(all_cells[:absolute + len(cells)])
    new_line = after.count("\n")
    last_newline = after.rfind("\n")
    if last_newline == -1:
        new_col = len(after)
    else:
        new_col = len(after) - last_newline - 1

    return new_doc, new_fmt, new_align, new_line, new_col


def apply_attr_to_selection(document, formatting, start, end, attr):
    selected = selection_range(document, start, end)
    if selected is None:
        return formatting
    a, b = selected
    cells = document_to_cells(document, formatting)

    all_set = True
    any_char = False
    for idx in range(a, b):
        ch, attrs = cells[idx]
        if ch != "\n":
            any_char = True
            if not (attrs & attr):
                all_set = False
                break
    if not any_char:
        return formatting

    for idx in range(a, b):
        ch, attrs = cells[idx]
        if ch != "\n":
            if all_set:
                cells[idx] = (ch, attrs & ~attr)
            else:
                cells[idx] = (ch, attrs | attr)

    _doc_ignore, formatting = cells_to_document(cells)
    return formatting


# ============================================================
# EDICIÓN
# ============================================================

def insert_character_rich(document, formatting, line, col, char, attrs):
    document[line] = document[line][:col] + char + document[line][col:]
    if line >= len(formatting):
        formatting.append([])
    for offset, _c in enumerate(char):
        formatting[line].insert(col + offset, attrs)
    col += len(char)
    return document, formatting, line, col


def delete_before_cursor_rich(document, formatting, alignments, line, col):
    if col > 0:
        document[line] = document[line][:col - 1] + document[line][col:]
        if line < len(formatting) and col - 1 < len(formatting[line]):
            del formatting[line][col - 1]
        col -= 1
    elif line > 0:
        previous_length = len(document[line - 1])
        document[line - 1] += document[line]
        if line < len(formatting):
            formatting[line - 1] += formatting[line]
            del formatting[line]
        del document[line]
        if line < len(alignments):
            del alignments[line]
        line -= 1
        col = previous_length
    return document, formatting, alignments, line, col


def delete_at_cursor_rich(document, formatting, alignments, line, col):
    line_text = document[line]
    if col < len(line_text):
        document[line] = line_text[:col] + line_text[col + 1:]
        if line < len(formatting) and col < len(formatting[line]):
            del formatting[line][col]
    elif line < len(document) - 1:
        document[line] += document[line + 1]
        if line + 1 < len(formatting):
            formatting[line] += formatting[line + 1]
            del formatting[line + 1]
        del document[line + 1]
        if line + 1 < len(alignments):
            del alignments[line + 1]
    return document, formatting, alignments, line, col


def enter_rich(document, formatting, alignments, line, col):
    left = document[line][:col]
    right = document[line][col:]
    if line < len(formatting):
        fmt_line = formatting[line]
        left_fmt = fmt_line[:col]
        right_fmt = fmt_line[col:]
    else:
        left_fmt = [0] * len(left)
        right_fmt = [0] * len(right)

    document[line] = left
    formatting[line] = left_fmt
    document.insert(line + 1, right)
    formatting.insert(line + 1, right_fmt)

    current_align = get_line_align(alignments, line)
    alignments.insert(line + 1, current_align)
    return document, formatting, alignments, line + 1, 0


def insert_page_break_rich(document, formatting, alignments, line, col):
    left = document[line][:col]
    right = document[line][col:]
    if line < len(formatting):
        fmt_line = formatting[line]
        left_fmt = fmt_line[:col]
        right_fmt = fmt_line[col:]
    else:
        left_fmt = [0] * len(left)
        right_fmt = [0] * len(right)

    document[line] = left
    formatting[line] = left_fmt
    document.insert(line + 1, PAGE_BREAK)
    formatting.insert(line + 1, [0])
    document.insert(line + 2, right)
    formatting.insert(line + 2, right_fmt)

    current_align = get_line_align(alignments, line)
    alignments.insert(line + 1, current_align)
    alignments.insert(line + 2, current_align)
    return document, formatting, alignments, line + 2, 0


# ============================================================
# BUSCAR Y REEMPLAZAR
# ============================================================

def find_all(document, term):
    if not term:
        return []
    text = document_to_string(document)
    lower_text = text.lower()
    lower_term = term.lower()
    positions = []
    start = 0
    step = max(1, len(lower_term))
    while True:
        idx = lower_text.find(lower_term, start)
        if idx == -1:
            break
        positions.append(absolute_to_position(text, idx))
        start = idx + step
    return positions


def replace_all(document, formatting, term, replacement):
    if not term:
        return document, formatting, 0
    replacement = replacement.replace("\\n", "\n")
    cells = document_to_cells(document, formatting)
    plain = "".join(ch for ch, _attrs in cells)
    term_lower = term.lower()
    plain_lower = plain.lower()
    result = []
    count = 0
    i = 0
    n = len(plain)
    tlen = len(term)
    while i < n:
        if i + tlen <= n and plain_lower[i:i + tlen] == term_lower:
            attrs = cells[i][1]
            for ch in replacement:
                if ch == "\n":
                    result.append(("\n", 0))
                else:
                    result.append((ch, attrs))
            i += tlen
            count += 1
        else:
            result.append(cells[i])
            i += 1
    doc, fmt = cells_to_document(result)
    return doc, fmt, count


# ============================================================
# PORTAPAPELES
# ============================================================

def set_system_clipboard(text):
    global internal_clipboard
    internal_clipboard = text
    try:
        if shutil.which("xclip"):
            process = subprocess.Popen(
                ["xclip", "-selection", "clipboard"],
                stdin=subprocess.PIPE
            )
            process.communicate(text.encode("utf-8"))
            return
        if shutil.which("xsel"):
            process = subprocess.Popen(
                ["xsel", "--clipboard", "--input"],
                stdin=subprocess.PIPE
            )
            process.communicate(text.encode("utf-8"))
            return
    except Exception:
        pass


def get_system_clipboard():
    global internal_clipboard
    try:
        if shutil.which("xclip"):
            result = subprocess.run(
                ["xclip", "-selection", "clipboard", "-o"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            if result.returncode == 0:
                return result.stdout.decode("utf-8", errors="replace")
        if shutil.which("xsel"):
            result = subprocess.run(
                ["xsel", "--clipboard", "--output"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            if result.returncode == 0:
                return result.stdout.decode("utf-8", errors="replace")
    except Exception:
        pass
    return internal_clipboard


# ============================================================
# RTF
# ============================================================

RTF_ALIGN = {
    ALIGN_LEFT:    r"\ql ",
    ALIGN_CENTER:  r"\qc ",
    ALIGN_RIGHT:   r"\qr ",
    ALIGN_JUSTIFY: r"\qj ",
}


def rtf_escape_char(ch):
    if ch == "\\":
        return "\\\\"
    if ch == "{":
        return "\\{"
    if ch == "}":
        return "\\}"
    code = ord(ch)
    if code < 128:
        return ch
    if code > 0xFFFF:
        code -= 0x10000
        high = 0xD800 + (code >> 10)
        low = 0xDC00 + (code & 0x3FF)
        if high > 32767:
            high -= 65536
        if low > 32767:
            low -= 65536
        return "\\u%d?\\u%d?" % (high, low)
    if code > 32767:
        code -= 65536
    return "\\u%d?" % code


def save_rtf(document, formatting, alignments, path):
    parts = []
    parts.append(r"{\rtf1\ansi\ansicpg1252\deff0")
    parts.append(r"{\fonttbl{\f0\froman Times New Roman;}}")
    parts.append(r"\viewkind4\uc1\f0\fs24 ")

    cur_b = False
    cur_i = False
    cur_u = False

    def close_styles():
        nonlocal cur_b, cur_i, cur_u
        if cur_b:
            parts.append(r"\b0 ")
            cur_b = False
        if cur_i:
            parts.append(r"\i0 ")
            cur_i = False
        if cur_u:
            parts.append(r"\ul0 ")
            cur_u = False

    for i, line in enumerate(document):
        if i < len(formatting):
            fmt_line = formatting[i]
        else:
            fmt_line = [0] * len(line)

        align = get_line_align(alignments, i)
        parts.append(r"\pard" + RTF_ALIGN[align])

        if line == PAGE_BREAK:
            close_styles()
            parts.append(r"\page ")
            continue

        heading_level = 0
        if fmt_line:
            first_attrs = fmt_line[0]
            if first_attrs & H1:
                heading_level = 1
            elif first_attrs & H2:
                heading_level = 2
            elif first_attrs & H3:
                heading_level = 3

        if heading_level > 0:
            parts.append("\\outlinelevel%d " % (heading_level - 1))

        for j, ch in enumerate(line):
            if ch == PAGE_BREAK:
                close_styles()
                parts.append(r"\page ")
                continue

            attrs = fmt_line[j] if j < len(fmt_line) else 0
            b = bool(attrs & BOLD) or (heading_level > 0)
            it = bool(attrs & ITALIC) or (heading_level == 3)
            u = bool(attrs & UNDERLINE) or (heading_level == 1)

            if b != cur_b:
                parts.append(r"\b " if b else r"\b0 ")
                cur_b = b
            if it != cur_i:
                parts.append(r"\i " if it else r"\i0 ")
                cur_i = it
            if u != cur_u:
                parts.append(r"\ul " if u else r"\ul0 ")
                cur_u = u

            parts.append(rtf_escape_char(ch))

        parts.append("\\par\n")

    if cur_b:
        parts.append(r"\b0 ")
    if cur_i:
        parts.append(r"\i0 ")
    if cur_u:
        parts.append(r"\ul0 ")

    parts.append("}")
    with open(path, "w", encoding="ascii", errors="ignore") as f:
        f.write("".join(parts))


def parse_rtf(text):
    document = [""]
    formatting = [[]]
    alignments = []
    style = [False, False, False]
    style_stack = []
    cur_align = ALIGN_LEFT
    cur_outline = 0
    uc = 1
    group_skip = []

    def current_attrs():
        a = 0
        if style[0]:
            a |= BOLD
        if style[1]:
            a |= ITALIC
        if style[2]:
            a |= UNDERLINE
        if cur_outline == 1:
            a |= H1
        elif cur_outline == 2:
            a |= H2
        elif cur_outline == 3:
            a |= H3
        return a

    def add_char(ch):
        document[-1] += ch
        formatting[-1].append(current_attrs())

    def add_newline():
        nonlocal cur_outline
        alignments.append(cur_align)
        document.append("")
        formatting.append([])
        cur_outline = 0

    i = 0
    n = len(text)
    skip_words = (
        "fonttbl", "colortbl", "stylesheet",
        "info", "pict", "header", "footer",
        "footnote", "filetbl", "listtable",
        "listoverridetable", "rsidtbl",
        "generator", "xmlnstbl"
    )

    while i < n:
        c = text[i]

        if c == "{":
            style_stack.append(tuple(style))
            j = i + 1
            will_skip = False
            if j < n and text[j] == "\\":
                if j + 1 < n and text[j + 1] == "*":
                    will_skip = True
                else:
                    k = j + 1
                    word = ""
                    while k < n and text[k].isalpha():
                        word += text[k]
                        k += 1
                    if word in skip_words:
                        will_skip = True
            group_skip.append(will_skip)
            i += 1

        elif c == "}":
            if style_stack:
                saved = style_stack.pop()
                style[0], style[1], style[2] = saved
            if group_skip:
                group_skip.pop()
            i += 1

        elif any(group_skip):
            i += 1

        elif c == "\\":
            i += 1
            if i >= n:
                break
            nc = text[i]

            if nc in ("\\", "{", "}"):
                add_char(nc)
                i += 1

            elif nc == "'":
                if i + 2 < n:
                    hex_str = text[i + 1:i + 3]
                    try:
                        code = int(hex_str, 16)
                        try:
                            ch = bytes([code]).decode("cp1252")
                        except Exception:
                            ch = chr(code)
                        add_char(ch)
                    except ValueError:
                        pass
                    i += 3
                else:
                    i += 1

            elif nc.isalpha():
                word = ""
                while i < n and text[i].isalpha():
                    word += text[i]
                    i += 1

                sign = 1
                if i < n and text[i] == "-":
                    sign = -1
                    i += 1

                num = ""
                while i < n and text[i].isdigit():
                    num += text[i]
                    i += 1

                has_param = bool(num)
                param = sign * int(num) if has_param else None

                if i < n and text[i] == " ":
                    i += 1

                if word == "u":
                    if has_param:
                        code = param
                        if code < 0:
                            code += 65536
                        try:
                            add_char(chr(code))
                        except (ValueError, OverflowError):
                            pass
                    skipped = 0
                    while skipped < uc and i < n:
                        c2 = text[i]
                        if c2 in ("{", "}"):
                            break
                        if c2 == "\\" and i + 1 < n and text[i + 1] == "'":
                            i += 4
                            skipped += 1
                        elif c2 == "\\" and i + 1 < n and text[i + 1].isalpha():
                            i += 2
                            while i < n and text[i].isalpha():
                                i += 1
                            if i < n and text[i] == "-":
                                i += 1
                            while i < n and text[i].isdigit():
                                i += 1
                            if i < n and text[i] == " ":
                                i += 1
                            skipped += 1
                        else:
                            i += 1
                            skipped += 1

                elif word in ("par", "line"):
                    add_newline()
                elif word == "page":
                    if document[-1] != "":
                        add_newline()
                    add_char(PAGE_BREAK)
                    add_newline()
                elif word == "pard":
                    cur_align = ALIGN_LEFT
                    cur_outline = 0
                elif word == "plain":
                    style[0] = False
                    style[1] = False
                    style[2] = False
                elif word == "ql":
                    cur_align = ALIGN_LEFT
                elif word == "qc":
                    cur_align = ALIGN_CENTER
                elif word == "qr":
                    cur_align = ALIGN_RIGHT
                elif word == "qj":
                    cur_align = ALIGN_JUSTIFY
                elif word == "outlinelevel":
                    if has_param and 0 <= param <= 2:
                        cur_outline = param + 1
                elif word == "b":
                    style[0] = True if param is None else (param != 0)
                elif word == "i":
                    style[1] = True if param is None else (param != 0)
                elif word == "ul":
                    style[2] = True if param is None else (param != 0)
                elif word == "ulnone":
                    style[2] = False
                elif word == "uc":
                    if has_param:
                        uc = max(0, param)
            else:
                i += 1

        elif c in ("\r", "\n"):
            i += 1

        else:
            add_char(c)
            i += 1

    alignments.append(cur_align)
    if len(document) > 1 and document[-1] == "" and not formatting[-1]:
        document.pop()
        formatting.pop()
        alignments.pop()

    while len(alignments) < len(document):
        alignments.append(ALIGN_LEFT)
    alignments = alignments[:len(document)]
    return document, formatting, alignments

# ============================================================
# MARKDOWN
# ============================================================

def save_markdown(document, formatting, alignments, path):
    lines = []
    for i, line in enumerate(document):
        if line == PAGE_BREAK:
            lines.append("")
            lines.append("---")
            lines.append("")
            continue

        if i < len(formatting):
            fmt_line = formatting[i]
        else:
            fmt_line = [0] * len(line)

        out = []
        cur_bold = False
        cur_italic = False
        cur_under = False

        for j, ch in enumerate(line):
            attrs = fmt_line[j] if j < len(fmt_line) else 0
            b = bool(attrs & BOLD)
            it = bool(attrs & ITALIC)
            u = bool(attrs & UNDERLINE)

            if cur_under and not u:
                out.append("</u>")
                cur_under = False
            if cur_italic and not it:
                out.append("*")
                cur_italic = False
            if cur_bold and not b:
                out.append("**")
                cur_bold = False

            if b and not cur_bold:
                out.append("**")
                cur_bold = True
            if it and not cur_italic:
                out.append("*")
                cur_italic = True
            if u and not cur_under:
                out.append("<u>")
                cur_under = True

            if ch in ("\\", "*", "_", "<", ">"):
                out.append("\\")
            out.append(ch)

        if cur_under:
            out.append("</u>")
        if cur_italic:
            out.append("*")
        if cur_bold:
            out.append("**")

        content = "".join(out)

        level = get_line_heading_level(formatting, i)
        if level == 1:
            lines.append("# " + content)
        elif level == 2:
            lines.append("## " + content)
        elif level == 3:
            lines.append("### " + content)
        else:
            lines.append(content)

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        if lines:
            f.write("\n")


def parse_markdown(text):
    document = []
    formatting = []
    alignments = []

    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]

    for line in lines:
        if line.strip() == "---":
            document.append(PAGE_BREAK)
            formatting.append([0])
            alignments.append(ALIGN_LEFT)
            continue

        level = 0
        content = line
        if line.startswith("### "):
            level = 3
            content = line[4:]
        elif line.startswith("## "):
            level = 2
            content = line[3:]
        elif line.startswith("# "):
            level = 1
            content = line[2:]

        chars = []
        attrs_list = []
        i = 0
        bold = False
        italic = False
        underline = False

        while i < len(content):
            if content.startswith("***", i):
                bold = not bold
                italic = not italic
                i += 3
            elif content.startswith("**", i):
                bold = not bold
                i += 2
            elif content.startswith("<u>", i):
                underline = True
                i += 3
            elif content.startswith("</u>", i):
                underline = False
                i += 4
            elif content[i] == "\\" and i + 1 < len(content):
                ch = content[i + 1]
                a = 0
                if bold:
                    a |= BOLD
                if italic:
                    a |= ITALIC
                if underline:
                    a |= UNDERLINE
                chars.append(ch)
                attrs_list.append(a)
                i += 2
            elif content[i] == "*":
                italic = not italic
                i += 1
            else:
                a = 0
                if bold:
                    a |= BOLD
                if italic:
                    a |= ITALIC
                if underline:
                    a |= UNDERLINE
                chars.append(content[i])
                attrs_list.append(a)
                i += 1

        if level == 1:
            attrs_list = [a | H1 for a in attrs_list]
        elif level == 2:
            attrs_list = [a | H2 for a in attrs_list]
        elif level == 3:
            attrs_list = [a | H3 for a in attrs_list]

        document.append("".join(chars))
        formatting.append(attrs_list)
        alignments.append(ALIGN_LEFT)

    if not document:
        document = [""]
        formatting = [[]]
        alignments = [ALIGN_LEFT]

    return document, formatting, alignments


def start_md_save(document, formatting, alignments, target_path):
    try:
        doc_copy = copy.deepcopy(document)
        fmt_copy = copy.deepcopy(formatting)
        al_copy = copy.deepcopy(alignments)

        tmp_dir = tempfile.mkdtemp(prefix="underwood_mdsave_")
        tmp_md = os.path.join(tmp_dir, "doc.md")

        done_event = threading.Event()

        def worker():
            try:
                save_markdown(doc_copy, fmt_copy, al_copy, tmp_md)
            except Exception:
                pass
            finally:
                done_event.set()

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

        return {
            "done_event": done_event,
            "thread": thread,
            "tmp_dir": tmp_dir,
            "tmp_md": tmp_md,
            "target_path": target_path,
            "started_at": time.monotonic(),
            "min_delay": 0.35,
        }, None
    except Exception as e:
        return None, tr("Error: ") + str(e)[:40]


def poll_md_save(state):
    if not state["done_event"].is_set():
        return False, None, None

    if time.monotonic() - state["started_at"] < state["min_delay"]:
        return False, None, None

    try:
        directory = os.path.dirname(
            os.path.abspath(state["target_path"]))
        if directory:
            os.makedirs(directory, exist_ok=True)
        shutil.copy(state["tmp_md"], state["target_path"])
        result = (True, True,
                  tr("Guardado: %s")
                  % os.path.basename(state["target_path"]))
    except Exception as e:
        result = (True, False,
                  tr("Error al copiar: ") + str(e)[:30])

    try:
        shutil.rmtree(state["tmp_dir"], ignore_errors=True)
    except Exception:
        pass

    return result



# ============================================================
# LIBREOFFICE
# ============================================================

def find_libreoffice():
    native = shutil.which("soffice") or shutil.which("libreoffice")
    if native:
        return [native]
    if shutil.which("flatpak"):
        try:
            check = subprocess.run(
                ["flatpak", "info", "org.libreoffice.LibreOffice"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5
            )
            if check.returncode == 0:
                return [
                    "flatpak", "run",
                    "--filesystem=home",
                    "--filesystem=/tmp",
                    "org.libreoffice.LibreOffice"
                ]
        except Exception:
            pass
    return None


def convert_with_libreoffice(input_path, output_ext, output_dir=None):
    base_cmd = find_libreoffice()
    if not base_cmd:
        return False, None, "LibreOffice no instalado"

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="underwood_conv_")

    try:
        subprocess.run(
            base_cmd + [
                "--headless", "--norestore",
                "--convert-to", output_ext,
                "--outdir", output_dir, input_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=90
        )
        base = os.path.splitext(os.path.basename(input_path))[0]
        out_path = os.path.join(output_dir, base + "." + output_ext)
        if os.path.exists(out_path):
            return True, out_path, None
        return False, None, "Conversión fallida"
    except Exception as e:
        return False, None, str(e)[:60]


# ============================================================
# CARGA Y GUARDADO
# ============================================================

def load_document(path):
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return [""], [[]], [ALIGN_LEFT]

    try:
        lower = path.lower()

        if lower.endswith((".docx", ".doc")):
            tmp_dir = tempfile.mkdtemp(prefix="underwood_docx_")
            try:
                ok, rtf_path, _err = convert_with_libreoffice(
                    path, "rtf", tmp_dir)
                if not ok:
                    return [""], [[]], [ALIGN_LEFT]
                with open(rtf_path, "r", encoding="ascii",
                          errors="replace") as f:
                    content = f.read()
                if content.lstrip().startswith("{\\rtf"):
                    return parse_rtf(content)
                doc = string_to_document(content)
                fmt = [[] for _i in doc]
                al = [ALIGN_LEFT for _i in doc]
                return doc, fmt, al
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)

        if lower.endswith(".rtf"):
            with open(path, "r", encoding="ascii",
                      errors="replace") as f:
                content = f.read()
            if content.lstrip().startswith("{\\rtf"):
                return parse_rtf(content)
            doc = string_to_document(content)
            fmt = [[] for _i in doc]
            al = [ALIGN_LEFT for _i in doc]
            return doc, fmt, al

        if lower.endswith((".md", ".markdown")):
            with open(path, "r", encoding="utf-8",
                      errors="replace") as f:
                content = f.read()
            return parse_markdown(content)

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        doc = string_to_document(content)
        fmt = [[] for _i in doc]
        al = [ALIGN_LEFT for _i in doc]
        return doc, fmt, al

    except Exception:
        return [""], [[]], [ALIGN_LEFT]


def save_document(document, formatting, alignments, path):
    try:
        directory = os.path.dirname(os.path.abspath(path))
        if directory:
            os.makedirs(directory, exist_ok=True)

        lower = path.lower()

        if lower.endswith(".rtf"):
            save_rtf(document, formatting, alignments, path)
            return True

        if lower.endswith((".md", ".markdown")):
            save_markdown(document, formatting, alignments, path)
            return True

        if lower.endswith((".docx", ".doc")):
            tmp_dir = tempfile.mkdtemp(prefix="underwood_docx_")
            try:
                tmp_rtf = os.path.join(tmp_dir, "doc.rtf")
                save_rtf(document, formatting, alignments, tmp_rtf)
                ext = "docx" if lower.endswith(".docx") else "doc"
                ok, out_path, _err = convert_with_libreoffice(
                    tmp_rtf, ext, tmp_dir
                )
                if not ok:
                    return False
                shutil.copy(out_path, path)
                return True
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(document_to_string(document))
        return True
    except Exception:
        return False


# ============================================================
# EXPORTACIÓN ASÍNCRONA (PDF y .docx)
# ============================================================

def start_pdf_export(document, formatting, alignments, rtf_path):
    base_cmd = find_libreoffice()
    if not base_cmd:
        return None, tr("LibreOffice no instalado")

    if rtf_path:
        pdf_path = os.path.splitext(rtf_path)[0] + ".pdf"
    else:
        pdf_path = os.path.expanduser("~/underwood/documento.pdf")

    out_dir = os.path.dirname(os.path.abspath(pdf_path)) or "."
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception:
        return None, tr("No se puede crear carpeta")

    try:
        tmp_dir = tempfile.mkdtemp(prefix="underwood_pdf_")
        tmp_rtf = os.path.join(tmp_dir, "doc.rtf")
        save_rtf(document, formatting, alignments, tmp_rtf)

        proc = subprocess.Popen(
            base_cmd + [
                "--headless", "--norestore",
                "--convert-to", "pdf",
                "--outdir", tmp_dir, tmp_rtf
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        state = {
            "proc": proc,
            "tmp_dir": tmp_dir,
            "pdf_path": pdf_path,
            "started_at": time.monotonic(),
        }
        return state, None
    except Exception as e:
        return None, tr("Error: ") + str(e)[:40]


def poll_pdf_export(state):
    proc = state["proc"]
    ret = proc.poll()
    if ret is None:
        return False, None, None

    tmp_dir = state["tmp_dir"]
    pdf_path = state["pdf_path"]

    try:
        proc.communicate(timeout=2)
    except Exception:
        pass

    generated = os.path.join(tmp_dir, "doc.pdf")

    if os.path.exists(generated):
        try:
            shutil.copy(generated, pdf_path)
            result = (True, True,
                      tr("PDF: %s") % os.path.basename(pdf_path))
        except Exception as e:
            result = (True, False,
                      tr("Error al copiar: ") + str(e)[:30])
    else:
        result = (True, False, tr("Error al generar PDF"))

    try:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass

    return result


def start_docx_save(document, formatting, alignments, target_path):
    base_cmd = find_libreoffice()
    if not base_cmd:
        return None, tr("LibreOffice no instalado")

    out_dir = os.path.dirname(os.path.abspath(target_path)) or "."
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception:
        return None, tr("No se puede crear carpeta")

    try:
        tmp_dir = tempfile.mkdtemp(prefix="underwood_docxsave_")
        tmp_rtf = os.path.join(tmp_dir, "doc.rtf")
        save_rtf(document, formatting, alignments, tmp_rtf)

        proc = subprocess.Popen(
            base_cmd + [
                "--headless", "--norestore",
                "--convert-to", "docx",
                "--outdir", tmp_dir, tmp_rtf
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        state = {
            "proc": proc,
            "tmp_dir": tmp_dir,
            "target_path": target_path,
            "started_at": time.monotonic(),
        }
        return state, None
    except Exception as e:
        return None, tr("Error: ") + str(e)[:40]


def poll_docx_save(state):
    proc = state["proc"]
    ret = proc.poll()
    if ret is None:
        return False, None, None

    tmp_dir = state["tmp_dir"]
    target_path = state["target_path"]

    try:
        proc.communicate(timeout=2)
    except Exception:
        pass

    generated = os.path.join(tmp_dir, "doc.docx")

    if os.path.exists(generated):
        try:
            shutil.copy(generated, target_path)
            result = (True, True,
                      tr("Guardado: %s")
                      % os.path.basename(target_path))
        except Exception as e:
            result = (True, False,
                      tr("Error al copiar: ") + str(e)[:30])
    else:
        result = (True, False, tr("Error al guardar .docx"))

    try:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass

    return result


# ============================================================
# DIBUJO
# ============================================================

def draw_title_bar(stdscr, window_title, width):
    base = _base_attr()
    left_text = tr("Herramientas: F9")
    if _TTY_MODE:
        right_text = tr("Selección: Ctrl+Space")
    else:
        right_text = tr("Selección: Shift→")

    # En terminales muy estrechas se omiten las pistas.
    show_left = width >= 50
    show_right = width >= 70

    left_x = 2
    left_end = left_x + len(left_text) if show_left else 0

    right_x = width - len(right_text) - 2
    right_end = right_x + len(right_text)

    # Pista izquierda
    if show_left and left_end < width - 1:
        try:
            stdscr.addstr(TITLE_ROW, left_x, left_text, base)
        except curses.error:
            pass

    # Pista derecha
    if show_right and right_x > left_end + 2 and right_end <= width - 1:
        try:
            stdscr.addstr(TITLE_ROW, right_x, right_text, base)
        except curses.error:
            pass

    # Espacio disponible para el título, entre las dos pistas
    avail_start = (left_end + 2) if show_left else 2
    if show_right and right_x > avail_start + 2:
        avail_end = right_x - 2
    else:
        avail_end = width - 2

    avail = avail_end - avail_start
    if avail <= 0:
        return

    title = window_title
    if len(title) > avail:
        title = title[:avail]

    title_x = avail_start + (avail - len(title)) // 2

    try:
        stdscr.addstr(TITLE_ROW, title_x, title,
                      base | curses.A_BOLD)
    except curses.error:
        pass


def draw_menu_bar(stdscr, menus, menu_open, width):
    layout = menu_bar_layout(menus, width)
    sep = MENU_SEPARATOR
    base = _base_attr()
    for i, (name, start, _end) in enumerate(layout):
        is_open = (i == menu_open)
        attr = base | curses.A_BOLD
        if is_open:
            attr |= curses.A_REVERSE
        try:
            stdscr.addstr(MENU_ROW, start, name, attr)
        except curses.error:
            pass
        if i < len(menus) - 1:
            try:
                stdscr.addstr(MENU_ROW, start + len(name), sep, base)
            except curses.error:
                pass


def draw_dropdown(stdscr, menu, dx, dy, selected_index=-1):
    w = dropdown_size(menu)
    x = dx
    y = dy
    base = _base_attr()

    max_label = 0
    max_shortcut = 0
    for item in menu:
        if item is None:
            continue
        l2, s2, _a = item
        max_label = max(max_label, len(l2))
        max_shortcut = max(max_shortcut, len(s2))

    try:
        stdscr.addstr(y, x, "┌" + "─" * (w - 2) + "┐", base)
    except curses.error:
        pass

    y += 1
    item_index = 0
    for item in menu:
        if item is None:
            try:
                stdscr.addstr(y, x, "├" + "─" * (w - 2) + "┤", base)
            except curses.error:
                pass
        else:
            label, shortcut, _a = item
            inner = (" " + label.ljust(max_label) + "  "
                     + shortcut.rjust(max_shortcut) + " ")
            inner = inner[:w - 2].ljust(w - 2)
            item_attr = base
            if item_index == selected_index:
                item_attr |= curses.A_REVERSE
            try:
                stdscr.addstr(y, x, "│", base)
                stdscr.addstr(y, x + 1, inner, item_attr)
                stdscr.addstr(y, x + w - 1, "│", base)
            except curses.error:
                pass
        item_index += 1
        y += 1

    try:
        stdscr.addstr(y, x, "└" + "─" * (w - 2) + "┘", base)
    except curses.error:
        pass


def _draw_open_menu(stdscr, menu_open, width, selected_index=-1):
    if menu_open < 0 or menu_open >= len(MENUS):
        return
    _name, menu_items = MENUS[menu_open]
    if menu_items is None:
        return
    layout = menu_bar_layout(MENUS, width)
    menu_label_x = layout[menu_open][1]
    dx = dropdown_x(menu_items, menu_label_x, width)
    draw_dropdown(stdscr, menu_items, dx, DROPDOWN_ROW, selected_index)


def draw_editor(
    stdscr, document, formatting, alignments,
    cursor_line, cursor_col, selection_start, selection_end,
    scroll_row, status_message, typing_attrs, window_title,
    mode, prompt_buffer, prompt_label, help_scroll,
    search_active, search_matches, search_index,
    menu_open, menu_selected,
    browse_dir, browse_entries, browse_index, browse_scroll,
    export_animating, export_spinner, export_kind,
    spell_positions=None,
    spell_suggestions=None,
    spell_unavailable_msg="",
    spell_active=False,
    chapter_headings=None,
    chapter_index=0,
    chapter_scroll=0,
):
    height, width = stdscr.getmaxyx()
    stdscr.erase()

    # Fondo negro intenso
    if _COLORS_READY:
        try:
            stdscr.bkgd(" ", curses.color_pair(2))
        except Exception:
            pass

    text_width = min(TEXT_WIDTH, max(1, width - 4))
    text_x = max(2, (width - text_width) // 2)

    top = TEXT_TOP
    bottom = height - 2
    if bottom <= top:
        bottom = top + 1

    draw_title_bar(stdscr, window_title, width)

    try:
        stdscr.addstr(SEP_TITLE_ROW, 0, "─" * max(1, width - 1),
                      _base_attr())
    except curses.error:
        pass

    draw_menu_bar(stdscr, MENUS, menu_open, width)

    try:
        stdscr.addstr(SEP_TOP_ROW, 0, "─" * max(1, width - 1),
                      _base_attr())
    except curses.error:
        pass
    try:
        stdscr.addstr(bottom, 0, "─" * max(1, width - 1), _base_attr())
    except curses.error:
        pass

    status_y = height - 1

    if mode in ("help", "about"):
        if mode == "help":
            source_text = MANUAL_TEXT
            title_line = tr("Manual de Underwood")
        else:
            source_text = ABOUT_TEXT
            title_line = tr("Acerca de")

        doc_lines = source_text.split("\n")
        doc_visual = visual_lines(doc_lines, text_width)

        try:
            tx = max(2, (width - len(title_line)) // 2)
            stdscr.addstr(top, tx, title_line,
                          _base_attr() | curses.A_BOLD)
        except curses.error:
            pass

        body_top = top + 2
        base = _base_attr()

        for visual_row, (_idx, _start, text) in enumerate(doc_visual):
            screen_y = body_top + visual_row - help_scroll
            if screen_y < body_top or screen_y >= bottom:
                continue
            try:
                stdscr.addstr(screen_y, text_x,
                              text[:width - text_x - 1], base)
            except curses.error:
                pass

        try:
            footer = tr("↑↓ desplazar  ·  Esc para volver")
            fx = max(2, (width - len(footer)) // 2)
            stdscr.addstr(status_y, fx, footer[:width - 3], base)
        except curses.error:
            pass

        if menu_open >= 0:
            _draw_open_menu(stdscr, menu_open, width, menu_selected)
        stdscr.refresh()
        return

    lines = visual_lines(document, text_width)
    n_lines = len(lines)

    sel_range = None
    if selection_start is not None and selection_end is not None:
        sel_range = selection_range(
            document, selection_start, selection_end
        )

    offsets = line_offsets(document)

    misspelled_set = set()
    if spell_positions:
        for s, e in spell_positions:
            for p in range(s, e):
                misspelled_set.add(p)

    spell_attr = 0
    if _COLORS_READY:
        try:
            spell_attr = curses.color_pair(1)
        except Exception:
            spell_attr = 0

    for visual_row, (line_index, start, text) in enumerate(lines):
        screen_y = top + visual_row - scroll_row
        if screen_y < top or screen_y >= bottom:
            continue

        if visual_row == n_lines - 1:
            is_last_subline = True
        else:
            is_last_subline = lines[visual_row + 1][0] != line_index

        align = get_line_align(alignments, line_index)
        display_text, offset, mapping = compute_line_layout(
            text, text_width, align, is_last_subline
        )

        fmt_line = (formatting[line_index]
                    if line_index < len(formatting) else [])
        line_base = offsets[line_index] if line_index < len(offsets) else 0

        for i, char in enumerate(display_text):
            screen_x = text_x + offset + i
            if screen_x >= width - 1:
                break
            orig_col = start + (mapping[i] if mapping else i)

            if char == PAGE_BREAK:
                remaining = text_x + text_width - screen_x
                if remaining > 0:
                    try:
                        stdscr.addstr(screen_y, screen_x, "━" * remaining,
                                      _base_attr())
                    except curses.error:
                        pass
                break

            abs_col = line_base + orig_col

            selected = False
            if sel_range is not None:
                selected = sel_range[0] <= abs_col < sel_range[1]

            attrs = fmt_line[orig_col] if orig_col < len(fmt_line) else 0

            if spell_attr and abs_col in misspelled_set:
                if _TTY_MODE:
                    cattr = curses.color_pair(1) | curses.A_UNDERLINE
                else:
                    cattr = spell_attr
                    if attrs & BOLD:
                        cattr |= curses.A_BOLD
                    if attrs & ITALIC:
                        cattr |= getattr(curses, "A_ITALIC", 0)
                    if attrs & UNDERLINE:
                        cattr |= curses.A_UNDERLINE
            else:
                cattr = _style_for_attrs(attrs)
                if not _TTY_MODE:
                    heading_bits = attrs & HEADING_MASK
                    if heading_bits == H1:
                        cattr |= curses.A_BOLD | curses.A_UNDERLINE
                    elif heading_bits == H2:
                        cattr |= curses.A_BOLD
                    elif heading_bits == H3:
                        cattr |= curses.A_BOLD | getattr(
                            curses, "A_ITALIC", 0)

            if selected:
                cattr |= curses.A_REVERSE

            try:
                stdscr.addstr(screen_y, screen_x, char, cattr)
            except curses.error:
                pass

    cursor_row, cursor_subcol = cursor_visual_position(
        document, cursor_line, cursor_col, text_width
    )
    cursor_y = top + cursor_row - scroll_row

    if 0 <= cursor_row < n_lines:
        cl_line, cl_start, cl_text = lines[cursor_row]
        if cursor_row == n_lines - 1:
            is_last = True
        else:
            is_last = lines[cursor_row + 1][0] != cl_line

        cl_align = get_line_align(alignments, cl_line)
        _display_text, cl_offset, cl_mapping = compute_line_layout(
            cl_text, text_width, cl_align, is_last
        )

        if cl_mapping:
            display_pos = len(cl_mapping)
            for k, m in enumerate(cl_mapping):
                if m >= cursor_subcol:
                    display_pos = k
                    break
        else:
            display_pos = cursor_subcol

        cursor_screen_x = text_x + cl_offset + display_pos
    else:
        cursor_screen_x = text_x

    if top <= cursor_y < bottom and 0 <= cursor_screen_x < width:
        try:
            cursor_attr = curses.A_REVERSE | curses_attr_for(typing_attrs)
            if (cursor_line < len(document)
                    and cursor_col < len(document[cursor_line])):
                char = document[cursor_line][cursor_col]
                if char == PAGE_BREAK:
                    stdscr.addstr(cursor_y, cursor_screen_x, "━",
                                  cursor_attr)
                else:
                    stdscr.addstr(cursor_y, cursor_screen_x, char,
                                  cursor_attr)
            else:
                stdscr.addstr(cursor_y, cursor_screen_x, " ", cursor_attr)
            stdscr.move(cursor_y, cursor_screen_x)
        except curses.error:
            pass

    if mode in ("search", "replace_find", "replace_with", "save_as",
                "save_as_docx", "save_as_md"):
        label = prompt_label
        text = label + " " + prompt_buffer
        try:
            stdscr.addstr(status_y, text_x, text[:text_width],
                          _base_attr())
        except curses.error:
            pass
        try:
            cursor_pos = min(
                text_x + len(label) + 1 + len(prompt_buffer),
                text_x + text_width - 1
            )
            stdscr.move(status_y, cursor_pos)
        except curses.error:
            pass

    elif export_animating:
        wc = count_words(document)
        left = tr("Palabras: %d") % wc
        if export_kind == "pdf":
            right = tr("Exportando a PDF… %s") % export_spinner
        elif export_kind == "md":
            right = tr("Guardando .md… %s") % export_spinner
        else:
            right = tr("Guardando .docx… %s") % export_spinner

        try:
            stdscr.addstr(status_y, text_x, left[:text_width],
                          _base_attr())
        except curses.error:
            pass

        rx = text_x + text_width - len(right)
        min_rx = text_x + len(left) + 2
        if rx < min_rx:
            rx = min_rx
        max_len = text_x + text_width - rx
        if max_len > 0:
            try:
                stdscr.addstr(status_y, rx, right[:max_len],
                              _base_attr() | curses.A_BOLD)
            except curses.error:
                pass

    else:
        wc = count_words(document)
        left = tr("Palabras: %d") % wc
        right_parts = []

        indicators = []
        if typing_attrs & BOLD:
            indicators.append("B")
        if typing_attrs & ITALIC:
            indicators.append("I")
        if typing_attrs & UNDERLINE:
            indicators.append("U")
        if indicators:
            right_parts.append("[" + "".join(indicators) + "]")

        if search_active and search_matches:
            right_parts.append("%d/%d" % (search_index + 1,
                                          len(search_matches)))

        if spell_unavailable_msg:
            right_parts.append(spell_unavailable_msg)
        elif spell_suggestions:
            right_parts.append(
                tr("Ortografía: ") + ", ".join(spell_suggestions[:3])
            )
        elif spell_active:
            right_parts.append(tr("Ortografía ✓"))

        if status_message:
            right_parts.append(status_message)

        right = "  ·  ".join(right_parts)

        try:
            stdscr.addstr(status_y, text_x, left[:text_width],
                          _base_attr())
        except curses.error:
            pass

        if right:
            rx = text_x + text_width - len(right)
            min_rx = text_x + len(left) + 2
            if rx < min_rx:
                rx = min_rx
            max_len = text_x + text_width - rx
            if max_len > 0:
                try:
                    stdscr.addstr(status_y, rx, right[:max_len],
                                  _base_attr())
                except curses.error:
                    pass

    if menu_open >= 0:
        _draw_open_menu(stdscr, menu_open, width, menu_selected)

    if mode == "browse":
        draw_browser(
            stdscr, browse_dir, browse_entries,
            browse_index, browse_scroll, width, height
        )

    if mode == "chapters":
        draw_chapter_panel(
            stdscr,
            chapter_headings if chapter_headings else [],
            chapter_index,
            chapter_scroll,
            width, height
        )

    stdscr.refresh()


# ============================================================
# POSICIÓN DEL MOUSE
# ============================================================

def mouse_to_document_position(
    mouse_x, mouse_y, document, alignments,
    text_width, scroll_row, top, bottom, text_x
):
    if mouse_y < top:
        visual_row = scroll_row
    elif mouse_y >= bottom:
        lines = visual_lines(document, text_width)
        visible_rows = max(1, bottom - top)
        visual_row = scroll_row + visible_rows - 1
    else:
        visual_row = mouse_y - top + scroll_row

    lines = visual_lines(document, text_width)
    if not lines:
        return 0, 0
    visual_row = max(0, min(visual_row, len(lines) - 1))
    line_index, start, text = lines[visual_row]

    if visual_row == len(lines) - 1:
        is_last_subline = True
    else:
        is_last_subline = lines[visual_row + 1][0] != line_index

    align = get_line_align(alignments, line_index)
    display_text, offset, mapping = compute_line_layout(
        text, text_width, align, is_last_subline
    )

    screen_col = mouse_x - text_x - offset
    if screen_col < 0:
        screen_col = 0

    if screen_col >= len(display_text):
        orig_col = (mapping[-1] + 1) if mapping else len(text)
    else:
        orig_col = mapping[screen_col] if mapping else screen_col

    if orig_col > len(text):
        orig_col = len(text)

    return line_index, start + orig_col


# ============================================================
# MOVIMIENTO
# ============================================================

def move_left(document, cursor_line, cursor_col):
    if cursor_col > 0:
        cursor_col -= 1
    elif cursor_line > 0:
        cursor_line -= 1
        cursor_col = len(document[cursor_line])
    return cursor_line, cursor_col


def move_right(document, cursor_line, cursor_col):
    if cursor_col < len(document[cursor_line]):
        cursor_col += 1
    elif cursor_line < len(document) - 1:
        cursor_line += 1
        cursor_col = 0
    return cursor_line, cursor_col


def move_up(document, cursor_line, cursor_col, text_width):
    current_row, current_x = cursor_visual_position(
        document, cursor_line, cursor_col, text_width
    )
    if current_row <= 0:
        return cursor_line, cursor_col
    target_row = current_row - 1
    lines = visual_lines(document, text_width)
    line_index, start, text = lines[target_row]
    return line_index, start + min(current_x, len(text))


def move_down(document, cursor_line, cursor_col, text_width):
    current_row, current_x = cursor_visual_position(
        document, cursor_line, cursor_col, text_width
    )
    lines = visual_lines(document, text_width)
    if current_row >= len(lines) - 1:
        return cursor_line, cursor_col
    target_row = current_row + 1
    line_index, start, text = lines[target_row]
    return line_index, start + min(current_x, len(text))


# ============================================================
# ENTRADA
# ============================================================

def parse_mouse_sequence(sequence):
    try:
        text = sequence.decode("ascii", errors="ignore")
        if not text.startswith("\x1b[<"):
            return None
        final = text[-1]
        if final not in ("M", "m"):
            return None
        body = text[3:-1]
        parts = body.split(";")
        if len(parts) != 3:
            return None
        button = int(parts[0])
        x = int(parts[1]) - 1
        y = int(parts[2]) - 1
        return (button, x, y, final)
    except Exception:
        return None


def read_input_event(fd):
    first = os.read(fd, 1)
    if not first:
        return None

    if first == b"\x1b":
        sequence = bytearray(first)
        end_time = time.monotonic() + 0.08

        while time.monotonic() < end_time:
            ready, _r, _w = select.select([fd], [], [], 0.005)
            if not ready:
                continue
            data = os.read(fd, 1)
            if not data:
                break
            sequence.extend(data)
            if (len(sequence) >= 3
                    and sequence[1:2] in (b"[", b"O")
                    and sequence[2:3] in (b"A", b"B", b"C", b"D")):
                break
            if len(sequence) == 3 and sequence[1:2] == b"O":
                break
            if data == b"~":
                break
            if data in (b"M", b"m"):
                break
            if len(sequence) > 64:
                break

        mouse = parse_mouse_sequence(bytes(sequence))
        if mouse is not None:
            return ("mouse", mouse)

        data = bytes(sequence)

        # Shift + flechas / Inicio / Fin / RePág / AvPág
        # (extienden la selección; útiles sin ratón)
        if data in (b"\x1b[1;2A", b"\x1b[2A"):
            return ("key", "SELECT_UP")
        if data in (b"\x1b[1;2B", b"\x1b[2B"):
            return ("key", "SELECT_DOWN")
        if data in (b"\x1b[1;2C", b"\x1b[2C"):
            return ("key", "SELECT_RIGHT")
        if data in (b"\x1b[1;2D", b"\x1b[2D"):
            return ("key", "SELECT_LEFT")
        if data in (b"\x1b[1;2H", b"\x1b[2H"):
            return ("key", "SELECT_HOME")
        if data in (b"\x1b[1;2F", b"\x1b[2F"):
            return ("key", "SELECT_END")
        if data == b"\x1b[5;2~":
            return ("key", "SELECT_PAGE_UP")
        if data == b"\x1b[6;2~":
            return ("key", "SELECT_PAGE_DOWN")

        if data in (b"\x1b[A", b"\x1bOA"):
            return ("key", "UP")
        if data in (b"\x1b[B", b"\x1bOB"):
            return ("key", "DOWN")
        if data in (b"\x1b[C", b"\x1bOC"):
            return ("key", "RIGHT")
        if data in (b"\x1b[D", b"\x1bOD"):
            return ("key", "LEFT")
        if data == b"\x1b[3~":
            return ("key", "DELETE")
        if data == b"\x1b[5~":
            return ("key", "PAGE_UP")
        if data == b"\x1b[6~":
            return ("key", "PAGE_DOWN")
        if data in (b"\x1b[H", b"\x1bOH", b"\x1b[1~"):
            return ("key", "HOME")
        if data in (b"\x1b[F", b"\x1bOF", b"\x1b[4~"):
            return ("key", "END")

        # F2, F3, F4, F5 = niveles de título
        # (algunos terminales usan \x1bO?, otros \x1b[??~)
        if data in (b"\x1bOQ", b"\x1b[12~"):
            return ("key", "H1")
        if data in (b"\x1bOR", b"\x1b[13~"):
            return ("key", "H2")
        if data in (b"\x1bOS", b"\x1b[14~"):
            return ("key", "H3")
        if data == b"\x1b[17~":
            return ("key", "H0")

        # F9 = abrir menú con teclado
        if data == b"\x1b[20~":
            return ("key", "MENU")

        # F7 = corrector ortográfico
        if data == b"\x1b[18~":
            return ("key", "SPELL")

        if data in (b"\x1bb", b"\x1bB"):
            return ("key", "BOLD")
        if data in (b"\x1bi", b"\x1bI"):
            return ("key", "ITALIC")
        if data in (b"\x1bu", b"\x1bU"):
            return ("key", "UNDERLINE")

        return ("key", "ESC")

    # Ctrl+Space solo tiene sentido en consola pura (sin Xorg).
    # En una terminal dentro de Xorg, Shift+flechas y el ratón
    # ya cubren la selección, así que no lo interceptamos.
    if first == b"\x00" and _TTY_MODE:
        return ("key", "MARK")
    if first == b"\x11":
        return ("key", "QUIT")
    if first == b"\x13":
        return ("key", "SAVE")
    if first == b"\x17":
        return ("key", "SAVE_AS")
    if first == b"\x03":
        return ("key", "COPY")
    if first == b"\x18":
        return ("key", "CUT")
    if first == b"\x16":
        return ("key", "PASTE")
    if first == b"\x02":
        return ("key", "BOLD")
    if first == b"\x09":
        return ("key", "ITALIC")
    if first == b"\x15":
        return ("key", "UNDERLINE")
    if first == b"\x06":
        return ("key", "FIND")
    if first == b"\x12":
        return ("key", "REPLACE")
    if first == b"\x10":
        return ("key", "PDF")
    if first == b"\x14":
        return ("key", "CHAPTERS")
    if first == b"\x07":
        return ("key", "HELP")
    if first == b"\x1a":
        return ("key", "UNDO")
    if first == b"\x0b":
        return ("key", "PAGEBREAK")
    if first == b"\x01":
        return ("key", "SELECT_ALL")
    if first == b"\x0e":
        return ("key", "NEW")
    if first == b"\x0f":
        return ("key", "OPEN")
    if first == b"\x08":
        return ("key", "ABOUT")

    if first == b"\x0c":
        return ("key", "ALIGN_LEFT")
    if first == b"\x05":
        return ("key", "ALIGN_CENTER")
    if first == b"\x04":
        return ("key", "ALIGN_RIGHT")
    if first == b"\x0a":
        return ("key", "ALIGN_JUSTIFY")

    if first in (b"\x7f", b"\x08"):
        return ("key", "BACKSPACE")
    if first in (b"\r", b"\n"):
        return ("key", "ENTER")

    expected = 1
    value = first[0]
    if value & 0xE0 == 0xC0:
        expected = 2
    elif value & 0xF0 == 0xE0:
        expected = 3
    elif value & 0xF8 == 0xF0:
        expected = 4

    data = bytearray(first)
    while len(data) < expected:
        part = os.read(fd, 1)
        if not part:
            break
        data.extend(part)

    try:
        char = bytes(data).decode("utf-8")
        if char:
            return ("char", char)
    except UnicodeDecodeError:
        pass

    return None


def has_pending_input(fd, timeout=0):
    try:
        r, _w, _x = select.select([fd], [], [], timeout)
        return bool(r)
    except Exception:
        return False


def enable_mouse_tracking():
    sys.stdout.write("\033[?1002h\033[?1006h")
    sys.stdout.flush()


def disable_mouse_tracking():
    sys.stdout.write("\033[?1002l\033[?1006l")
    sys.stdout.flush()


# ============================================================
# INICIALIZACIÓN DE COLORES
# ============================================================

def init_colors():
    global _COLORS_READY, _USE_256, _TTY_MODE
    try:
        if not curses.has_colors():
            _COLORS_READY = False
            return
        curses.start_color()
        try:
            curses.use_default_colors()
        except Exception:
            pass

        term = os.environ.get("TERM", "").lower()
        _TTY_MODE = term in ("linux", "linux-16color", "cons25")
        _USE_256 = curses.COLORS >= 256

        if _TTY_MODE:
            curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
            curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLUE)
            curses.init_pair(8, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        else:
            if _USE_256:
                try:
                    curses.init_pair(1, 208, curses.COLOR_BLACK)
                except Exception:
                    curses.init_pair(1, curses.COLOR_YELLOW,
                                     curses.COLOR_BLACK)
            else:
                curses.init_pair(1, curses.COLOR_YELLOW,
                                 curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)

        _COLORS_READY = True
    except Exception:
        _COLORS_READY = False


def _style_for_attrs(attrs):
    """Devuelve el atributo curses adecuado según el modo."""
    if _TTY_MODE:
        h = attrs & HEADING_MASK
        b = bool(attrs & BOLD)
        i = bool(attrs & ITALIC)
        u = bool(attrs & UNDERLINE)

        if h == H1:
            return curses.color_pair(7) | curses.A_BOLD
        if h == H2:
            return curses.color_pair(8) | curses.A_BOLD
        if h == H3:
            return curses.color_pair(4) | curses.A_BOLD
        if b and i:
            return curses.color_pair(6) | curses.A_BOLD
        if b:
            return curses.color_pair(3) | curses.A_BOLD
        if i:
            return curses.color_pair(4)
        if u:
            return curses.color_pair(5) | curses.A_UNDERLINE
        return curses.color_pair(2)

    a = _base_attr()
    if attrs & BOLD:
        a |= curses.A_BOLD
    if attrs & ITALIC:
        a |= getattr(curses, "A_ITALIC", 0)
    if attrs & UNDERLINE:
        a |= curses.A_UNDERLINE
    return a


# ============================================================
# BUCLE PRINCIPAL
# ============================================================

def editor(stdscr, initial_path=None):
    curses.raw()
    curses.noecho()
    curses.curs_set(1)
    curses.mousemask(0)
    enable_mouse_tracking()

    init_colors()

    if initial_path:
        document, formatting, alignments = load_document(initial_path)
    else:
        document = [""]
        formatting = [[]]
        alignments = [ALIGN_LEFT]

    current_path = initial_path

    typing_attrs = 0
    cursor_line = 0
    cursor_col = 0

    selection_start = None
    selection_end = None
    selecting = False

    status_message = ""
    status_time = 0

    scroll_row = 0
    auto_scroll = True

    selection_mouse_x = 0
    selection_mouse_y = 0

    mode = "normal"
    prompt_buffer = ""
    prompt_label = ""
    search_term = ""
    replace_term = ""
    help_scroll = 0

    search_active = False
    search_matches = []
    search_index = 0

    undo_stack = []

    menu_open = -1
    menu_selected = 0
    pending_key = None

    browse_dir = ""
    browse_entries = []
    browse_index = 0
    browse_scroll = 0

    export_state = None
    export_kind = None
    export_frames = 0

    spell_check_active = False
    spell_positions = []
    spell_dirty = False
    spell_last_change = 0.0
    spell_suggestions = []
    spell_suggest_cache = {}
    spell_unavailable_msg = ""
    last_spell_doc_str = document_to_string(document)

    chapter_headings = []
    chapter_index = 0
    chapter_scroll = 0

    SCROLL_LINES = 3

    try:
        while True:
            if export_state is not None:
                if export_kind == "pdf":
                    done, success, message = poll_pdf_export(export_state)
                elif export_kind == "md":
                    done, success, message = poll_md_save(export_state)
                else:
                    done, success, message = poll_docx_save(export_state)
                if done:
                    export_state = None
                    export_kind = None
                    export_frames = 0
                    status_message = message
                    status_time = time.monotonic()
                else:
                    export_frames = (export_frames + 1) % len(SPINNER_FRAMES)

            height, width = stdscr.getmaxyx()
            top = TEXT_TOP
            bottom = height - 2
            if bottom <= top:
                bottom = top + 1

            text_width = min(TEXT_WIDTH, max(1, width - 4))
            text_x = max(2, (width - text_width) // 2)
            visible_rows = max(1, bottom - top)

            if spell_check_active:
                cur_str = document_to_string(document)
                if cur_str != last_spell_doc_str:
                    spell_dirty = True
                    spell_last_change = time.monotonic()
                    last_spell_doc_str = cur_str

                if (spell_dirty
                        and time.monotonic() - spell_last_change > 0.5):
                    positions = run_spell_check(cur_str, current_language())
                    if positions is None:
                        spell_positions = []
                        spell_unavailable_msg = tr(
                            "hunspell no instalado")
                        spell_check_active = False
                    else:
                        spell_positions = positions
                        spell_unavailable_msg = ""
                    spell_dirty = False

            spell_suggestions = []
            if spell_check_active and spell_positions:
                doc_str_now = document_to_string(document)
                cursor_abs = position_to_absolute(
                    document, cursor_line, cursor_col)
                for s, e in spell_positions:
                    if s <= cursor_abs < e:
                        word = doc_str_now[s:e]
                        key = (word, current_language())
                        if key in spell_suggest_cache:
                            spell_suggestions = spell_suggest_cache[key]
                        else:
                            spell_suggestions = get_suggestions(
                                word, current_language())
                            spell_suggest_cache[key] = spell_suggestions
                        break

            force_draw = export_state is not None

            if force_draw or not has_pending_input(0, 0):
                if auto_scroll:
                    scroll_row = adjust_scroll(
                        document, cursor_line, cursor_col,
                        text_width, visible_rows, scroll_row
                    )
                else:
                    total_rows = len(visual_lines(document, text_width))
                    max_scroll = max(0, total_rows - visible_rows)
                    scroll_row = max(0, min(scroll_row, max_scroll))

                if (status_message
                        and time.monotonic() - status_time > STATUS_DURATION):
                    status_message = ""

                if current_path:
                    window_title = (
                        "UNDERWOOD  ·  " + os.path.basename(current_path)
                    )
                else:
                    window_title = "UNDERWOOD"

                draw_editor(
                    stdscr, document, formatting, alignments,
                    cursor_line, cursor_col,
                    selection_start, selection_end,
                    scroll_row, status_message, typing_attrs,
                    window_title, mode, prompt_buffer, prompt_label,
                    help_scroll, search_active, search_matches,
                    search_index, menu_open, menu_selected,
                    browse_dir, browse_entries,
                    browse_index, browse_scroll,
                    export_state is not None,
                    SPINNER_FRAMES[export_frames],
                    export_kind,
                    spell_positions,
                    spell_suggestions,
                    spell_unavailable_msg,
                    spell_check_active,
                    chapter_headings,
                    chapter_index,
                    chapter_scroll,
                )

            input_timeout = None
            if export_state is not None:
                input_timeout = 0.12
            elif spell_check_active and spell_dirty:
                input_timeout = 0.1

            if input_timeout is not None:
                r, _w, _x = select.select([0], [], [], input_timeout)
                if not r:
                    continue

            if pending_key is not None:
                event_type = "key"
                value = pending_key
                pending_key = None
            else:
                event = read_input_event(0)
                if event is None:
                    continue
                event_type, value = event

            if (event_type == "mouse"
                    and mode in ("search", "replace_find",
                                 "replace_with", "save_as",
                                 "save_as_docx", "save_as_md")):
                (button, mx, my, action) = value
                if button == 0 and action == "M":
                    mode = "normal"
                    prompt_buffer = ""
                    prompt_label = ""

            # ====================================================
            # MAPA DE CAPÍTULOS
            # ====================================================
            if mode == "chapters":
                _bx, _by, _bw, _bh, _ls, _lh = chapter_panel_geometry(
                    width, height
                )
                if event_type == "key":
                    if value in ("ESC", "QUIT"):
                        mode = "normal"
                    elif value == "UP":
                        if chapter_index > 0:
                            chapter_index -= 1
                    elif value == "DOWN":
                        if chapter_index < len(chapter_headings) - 1:
                            chapter_index += 1
                    elif value == "PAGE_UP":
                        chapter_index = max(0, chapter_index - _lh)
                    elif value == "PAGE_DOWN":
                        chapter_index = min(
                            max(0, len(chapter_headings) - 1),
                            chapter_index + _lh
                        )
                    elif value == "HOME":
                        chapter_index = 0
                    elif value == "END":
                        chapter_index = max(
                            0, len(chapter_headings) - 1
                        )
                    elif value == "ENTER":
                        if 0 <= chapter_index < len(chapter_headings):
                            line_index, _lvl, txt = (
                                chapter_headings[chapter_index]
                            )
                            push_undo(undo_stack, document,
                                      formatting, alignments)
                            cursor_line = line_index
                            cursor_col = 0
                            selection_start = None
                            selection_end = None
                            selecting = False
                            search_active = False
                            auto_scroll = True
                            mode = "normal"
                            scroll_row = adjust_scroll(
                                document, cursor_line, cursor_col,
                                text_width, visible_rows, scroll_row
                            )
                            status_message = (
                                tr("Saltado a: %s") % txt
                            )
                            status_time = time.monotonic()
                    elif value == "CHAPTERS":
                        mode = "normal"
                    elif len(value) == 1 and value.lower() == "n":
                        push_undo(undo_stack, document,
                                  formatting, alignments)
                        new_title = tr("Nuevo capítulo")
                        if document and document[-1] != "":
                            document.append("")
                            formatting.append([])
                            alignments.append(ALIGN_LEFT)
                        if document[-1] == "":
                            idx = len(document) - 1
                        else:
                            document.append("")
                            formatting.append([])
                            alignments.append(ALIGN_LEFT)
                            idx = len(document) - 1
                        document[idx] = new_title
                        formatting[idx] = [H1] * len(new_title)
                        while len(alignments) < len(document):
                            alignments.append(ALIGN_LEFT)
                        alignments = alignments[:len(document)]
                        cursor_line = idx
                        cursor_col = 0
                        selection_start = (idx, 0)
                        selection_end = (idx, len(new_title))
                        selecting = False
                        search_active = False
                        auto_scroll = True
                        mode = "normal"
                        scroll_row = adjust_scroll(
                            document, cursor_line, cursor_col,
                            text_width, visible_rows, scroll_row
                        )
                        status_message = tr("Nuevo capítulo")
                        status_time = time.monotonic()

                    if chapter_index < chapter_scroll:
                        chapter_scroll = chapter_index
                    elif chapter_index >= chapter_scroll + _lh:
                        chapter_scroll = chapter_index - _lh + 1
                    if chapter_scroll < 0:
                        chapter_scroll = 0

                elif event_type == "mouse":
                    (button, mx, my, action) = value

                    # Rueda del ratón: subir
                    if action == "M" and button == 64:
                        chapter_scroll = max(0, chapter_scroll - 3)
                        continue

                    # Rueda del ratón: bajar
                    if action == "M" and button == 65:
                        max_scroll = max(
                            0, len(chapter_headings) - _lh
                        )
                        chapter_scroll = min(
                            max_scroll, chapter_scroll + 3
                        )
                        continue

                    # Clic izquierdo
                    if button == 0 and action == "M":
                        list_x = _bx + 2
                        list_w = _bw - 4
                        if (list_x <= mx < list_x + list_w
                                and _ls <= my < _ls + _lh):
                            clicked_row = my - _ls
                            clicked_idx = (
                                chapter_scroll + clicked_row
                            )
                            if 0 <= clicked_idx < len(
                                    chapter_headings):
                                if clicked_idx == chapter_index:
                                    # Segundo clic sobre el mismo:
                                    # saltar al capítulo
                                    (line_index, _lvl, txt
                                     ) = chapter_headings[clicked_idx]
                                    push_undo(
                                        undo_stack, document,
                                        formatting, alignments
                                    )
                                    cursor_line = line_index
                                    cursor_col = 0
                                    selection_start = None
                                    selection_end = None
                                    selecting = False
                                    search_active = False
                                    auto_scroll = True
                                    mode = "normal"
                                    scroll_row = adjust_scroll(
                                        document,
                                        cursor_line, cursor_col,
                                        text_width, visible_rows,
                                        scroll_row
                                    )
                                    status_message = (
                                        tr("Saltado a: %s") % txt
                                    )
                                    status_time = time.monotonic()
                                else:
                                    # Primer clic: seleccionar
                                    chapter_index = clicked_idx

                    # Ajustar scroll tras mover el índice
                    if chapter_index < chapter_scroll:
                        chapter_scroll = chapter_index
                    elif chapter_index >= chapter_scroll + _lh:
                        chapter_scroll = chapter_index - _lh + 1
                    if chapter_scroll < 0:
                        chapter_scroll = 0
                continue

            # ====================================================
            # AYUDA / ACERCA DE
            # ====================================================
            if mode in ("help", "about"):
                if event_type == "key":
                    if value in ("ESC", "QUIT", "HELP", "ABOUT"):
                        if menu_open >= 0:
                            menu_open = -1
                        else:
                            mode = "normal"
                            help_scroll = 0
                    elif value == "UP":
                        help_scroll = max(0, help_scroll - 1)
                    elif value == "DOWN":
                        help_scroll += 1
                    elif value == "PAGE_UP":
                        help_scroll = max(0, help_scroll - visible_rows)
                    elif value == "PAGE_DOWN":
                        help_scroll += visible_rows

                elif event_type == "mouse":
                    (button, mx, my, action) = value
                    if button == 0 and action == "M":
                        idx = menu_index_at(MENUS, mx, width)
                        if my == MENU_ROW and idx >= 0:
                            name, items = MENUS[idx]
                            if items is None:
                                menu_open = -1
                                pending_key = "QUIT"
                            elif menu_open == idx:
                                menu_open = -1
                            else:
                                menu_open = idx
                            continue
                        if menu_open >= 0:
                            _name, items = MENUS[menu_open]
                            if items is not None:
                                layout = menu_bar_layout(MENUS, width)
                                menu_label_x = layout[menu_open][1]
                                dx = dropdown_x(items,
                                                menu_label_x, width)
                                item_idx = dropdown_item_at(
                                    items, mx, my, dx, DROPDOWN_ROW
                                )
                                if item_idx >= 0:
                                    item = items[item_idx]
                                    action_key = item[2]
                                    menu_open = -1
                                    pending_key = action_key
                                    continue
                            menu_open = -1
                continue

            # ====================================================
            # EXPLORADOR
            # ====================================================
            if mode == "browse":
                box_x, box_y, box_w, box_h = browser_box_geometry(
                    width, height)
                list_x = box_x + 2
                list_y = box_y + 3
                list_w = box_w - 4
                list_h = box_h - 5

                if event_type == "key":
                    if value == "ESC":
                        mode = "normal"
                        browse_dir = ""
                        browse_entries = []
                    elif value == "UP":
                        if browse_index > 0:
                            browse_index -= 1
                    elif value == "DOWN":
                        if browse_index < len(browse_entries) - 1:
                            browse_index += 1
                    elif value == "PAGE_UP":
                        browse_index = max(0, browse_index - list_h)
                    elif value == "PAGE_DOWN":
                        browse_index = min(
                            len(browse_entries) - 1,
                            browse_index + list_h
                        )
                    elif value == "HOME":
                        browse_index = 0
                    elif value == "END":
                        browse_index = max(
                            0, len(browse_entries) - 1)
                    elif value == "ENTER":
                        if 0 <= browse_index < len(browse_entries):
                            name, full, is_dir = (
                                browse_entries[browse_index])
                            if is_dir:
                                browse_dir = full
                                browse_entries = list_directory(
                                    browse_dir)
                                browse_index = 0
                                browse_scroll = 0
                            else:
                                push_undo(undo_stack, document,
                                          formatting, alignments)
                                (document, formatting, alignments
                                 ) = load_document(full)
                                current_path = full
                                cursor_line = 0
                                cursor_col = 0
                                selection_start = None
                                selection_end = None
                                selecting = False
                                search_active = False
                                scroll_row = 0
                                mode = "normal"
                                browse_dir = ""
                                browse_entries = []
                                status_message = (
                                    tr("Abierto: %s")
                                    % os.path.basename(full))
                                status_time = time.monotonic()
                    elif value == "BACKSPACE":
                        parent = os.path.dirname(
                            os.path.abspath(browse_dir))
                        if (parent
                                and parent != os.path.abspath(browse_dir)):
                            old_basename = os.path.basename(browse_dir)
                            browse_dir = parent
                            browse_entries = list_directory(browse_dir)
                            browse_index = 0
                            for i, (nm, _full, is_dir) in enumerate(
                                    browse_entries):
                                if is_dir and nm == old_basename:
                                    browse_index = i
                                    break
                            browse_scroll = 0
                    elif len(value) == 1 and value.isprintable():
                        start = browse_index + 1
                        n_entries = len(browse_entries)
                        for i in range(n_entries):
                            idx = (start + i) % n_entries
                            name = browse_entries[idx][0]
                            if name.lower().startswith(value.lower()):
                                browse_index = idx
                                break

                    if browse_index < browse_scroll:
                        browse_scroll = browse_index
                    elif browse_index >= browse_scroll + list_h:
                        browse_scroll = browse_index - list_h + 1
                    if browse_scroll < 0:
                        browse_scroll = 0

                elif event_type == "mouse":
                    (button, mx, my, action) = value
                    if action == "M" and button == 64:
                        browse_scroll = max(
                            0, browse_scroll - SCROLL_LINES)
                    elif action == "M" and button == 65:
                        max_scroll = max(
                            0, len(browse_entries) - list_h)
                        browse_scroll = min(
                            max_scroll, browse_scroll + SCROLL_LINES
                        )
                    elif button == 0 and action == "M":
                        if (list_x <= mx < list_x + list_w
                                and list_y <= my < list_y + list_h):
                            clicked_row = my - list_y
                            clicked_idx = browse_scroll + clicked_row
                            if 0 <= clicked_idx < len(browse_entries):
                                if clicked_idx == browse_index:
                                    (name, full, is_dir
                                     ) = browse_entries[clicked_idx]
                                    if is_dir:
                                        browse_dir = full
                                        browse_entries = list_directory(
                                            browse_dir)
                                        browse_index = 0
                                        browse_scroll = 0
                                    else:
                                        push_undo(
                                            undo_stack, document,
                                            formatting, alignments
                                        )
                                        (document, formatting,
                                         alignments
                                         ) = load_document(full)
                                        current_path = full
                                        cursor_line = 0
                                        cursor_col = 0
                                        selection_start = None
                                        selection_end = None
                                        selecting = False
                                        search_active = False
                                        scroll_row = 0
                                        mode = "normal"
                                        browse_dir = ""
                                        browse_entries = []
                                        status_message = (
                                            tr("Abierto: %s")
                                            % os.path.basename(full))
                                        status_time = time.monotonic()
                                else:
                                    browse_index = clicked_idx
                continue

            # ====================================================
            # GUARDAR COMO
            # ====================================================
            if mode in ("save_as", "save_as_docx", "save_as_md"):
                if event_type == "key":
                    if value == "ESC":
                        mode = "normal"
                        prompt_buffer = ""
                        prompt_label = ""

                    elif value == "BACKSPACE":
                        prompt_buffer = prompt_buffer[:-1]

                    elif value == "ENTER":
                        name = prompt_buffer.strip()
                        force_docx = (mode == "save_as_docx")
                        force_md = (mode == "save_as_md")
                        mode = "normal"
                        prompt_buffer = ""
                        prompt_label = ""

                        if name:
                            if "/" in name or name.startswith("~"):
                                full_path = os.path.expanduser(name)
                            else:
                                full_path = os.path.expanduser(
                                    os.path.join("~/underwood", name)
                                )

                            lower = full_path.lower()
                            if not lower.endswith(
                                    (".rtf", ".txt", ".docx", ".doc",
                                     ".md", ".markdown")):
                                if force_docx:
                                    full_path += ".docx"
                                elif force_md:
                                    full_path += ".md"
                                else:
                                    full_path += ".rtf"

                            directory = os.path.dirname(
                                os.path.abspath(full_path))
                            if directory:
                                try:
                                    os.makedirs(directory, exist_ok=True)
                                except Exception:
                                    status_message = tr(
                                        "No se puede crear carpeta")
                                    status_time = time.monotonic()
                                    continue

                            if full_path.lower().endswith(
                                    (".docx", ".doc")):
                                if export_state is not None:
                                    status_message = tr(
                                        "Ya hay un guardado en curso")
                                    status_time = time.monotonic()
                                else:
                                    state, err = start_docx_save(
                                        document, formatting,
                                        alignments, full_path
                                    )
                                    if state is None:
                                        status_message = err
                                        status_time = time.monotonic()
                                    else:
                                        current_path = full_path
                                        export_state = state
                                        export_kind = "docx"
                                        export_frames = 0
                                        status_message = ""
                                        status_time = 0
                            elif full_path.lower().endswith(
                                    (".md", ".markdown")):
                                if export_state is not None:
                                    status_message = tr(
                                        "Ya hay un guardado en curso")
                                    status_time = time.monotonic()
                                else:
                                    state, err = start_md_save(
                                        document, formatting,
                                        alignments, full_path
                                    )
                                    if state is None:
                                        status_message = err
                                        status_time = time.monotonic()
                                    else:
                                        current_path = full_path
                                        export_state = state
                                        export_kind = "md"
                                        export_frames = 0
                                        status_message = ""
                                        status_time = 0
                            else:
                                if save_document(document, formatting,
                                                 alignments, full_path):
                                    current_path = full_path
                                    status_message = (
                                        tr("Guardado: %s")
                                        % os.path.basename(full_path))
                                else:
                                    status_message = tr(
                                        "Error al guardar")
                                status_time = time.monotonic()

                elif event_type == "char":
                    if value and value != "\t":
                        prompt_buffer += value

                continue

            # ====================================================
            # BUSCAR / REEMPLAZAR
            # ====================================================
            if mode in ("search", "replace_find", "replace_with"):
                if event_type == "key":
                    if value == "ESC":
                        mode = "normal"
                        prompt_buffer = ""
                        prompt_label = ""
                    elif value == "BACKSPACE":
                        prompt_buffer = prompt_buffer[:-1]
                    elif value == "ENTER":
                        if mode == "search":
                            search_term = prompt_buffer
                            prompt_buffer = ""
                            prompt_label = ""
                            mode = "normal"

                            if search_term:
                                search_matches = find_all(
                                    document, search_term)
                                if search_matches:
                                    current_abs = position_to_absolute(
                                        document, cursor_line, cursor_col
                                    )
                                    start_idx = 0
                                    for idx, (l, c) in enumerate(
                                            search_matches):
                                        m_abs = position_to_absolute(
                                            document, l, c)
                                        if m_abs > current_abs:
                                            start_idx = idx
                                            break
                                    search_index = start_idx
                                    result = search_matches[search_index]
                                    cursor_line, cursor_col = result
                                    selection_start = result
                                    selection_end = (
                                        result[0],
                                        result[1] + len(search_term)
                                    )
                                    search_active = True
                                    auto_scroll = True
                                    status_message = "%d/%d" % (
                                        search_index + 1,
                                        len(search_matches))
                                else:
                                    search_matches = []
                                    search_active = False
                                    status_message = tr("No encontrado")
                                status_time = time.monotonic()

                        elif mode == "replace_find":
                            search_term = prompt_buffer
                            prompt_buffer = replace_term
                            prompt_label = tr("Reemplazar con:")
                            mode = "replace_with"

                        elif mode == "replace_with":
                            replace_term = prompt_buffer
                            prompt_buffer = ""
                            prompt_label = ""
                            mode = "normal"

                            if search_term:
                                push_undo(undo_stack, document,
                                          formatting, alignments)
                                (document, formatting, count
                                 ) = replace_all(
                                     document, formatting,
                                     search_term, replace_term)
                                while len(alignments) < len(document):
                                    alignments.append(ALIGN_LEFT)
                                alignments = alignments[:len(document)]

                                if count == 1:
                                    status_message = tr("1 reemplazo")
                                elif count > 1:
                                    status_message = (
                                        tr("%d reemplazos") % count)
                                else:
                                    status_message = tr("No encontrado")
                                status_time = time.monotonic()

                                if document:
                                    cursor_line = min(
                                        cursor_line, len(document) - 1
                                    )
                                    cursor_col = min(
                                        cursor_col,
                                        len(document[cursor_line])
                                    )
                                auto_scroll = True

                elif event_type == "char":
                    if value and value != "\t":
                        prompt_buffer += value
                continue

            # ====================================================
            # MOUSE
            # ====================================================
            if event_type == "mouse":
                (button, mouse_x, mouse_y, action) = value
                selection_mouse_x = mouse_x
                selection_mouse_y = mouse_y

                if action == "M" and button == 64:
                    scroll_row = max(0, scroll_row - SCROLL_LINES)
                    auto_scroll = False
                    continue
                if action == "M" and button == 65:
                    total_rows = len(visual_lines(document, text_width))
                    max_scroll = max(0, total_rows - visible_rows)
                    scroll_row = min(max_scroll,
                                     scroll_row + SCROLL_LINES)
                    auto_scroll = False
                    continue

                if button == 0 and action == "M":
                    if mouse_y == MENU_ROW:
                        idx = menu_index_at(MENUS, mouse_x, width)
                        if idx >= 0:
                            name, items = MENUS[idx]
                            if items is None:
                                menu_open = -1
                                pending_key = "QUIT"
                            elif menu_open == idx:
                                menu_open = -1
                            else:
                                menu_open = idx
                        else:
                            menu_open = -1
                        continue

                    if menu_open >= 0:
                        _name, items = MENUS[menu_open]
                        if items is not None:
                            layout = menu_bar_layout(MENUS, width)
                            menu_label_x = layout[menu_open][1]
                            dx = dropdown_x(items, menu_label_x, width)
                            item_idx = dropdown_item_at(
                                items, mouse_x, mouse_y, dx, DROPDOWN_ROW
                            )
                            if item_idx >= 0:
                                item = items[item_idx]
                                action_key = item[2]
                                menu_open = -1
                                pending_key = action_key
                                continue
                        menu_open = -1
                        continue

                    auto_scroll = True
                    position = mouse_to_document_position(
                        mouse_x, mouse_y, document, alignments,
                        text_width, scroll_row, top, bottom, text_x
                    )
                    if position is None:
                        continue
                    line, col = position
                    cursor_line = line
                    cursor_col = col
                    selection_start = (cursor_line, cursor_col)
                    selection_end = (cursor_line, cursor_col)
                    selecting = True
                    search_active = False

                elif (button >= 32 and button < 64
                        and action == "M" and selecting):
                    auto_scroll = True
                    if mouse_y >= bottom - 1:
                        total_rows = len(visual_lines(
                            document, text_width))
                        max_scroll = max(0, total_rows - visible_rows)
                        if scroll_row < max_scroll:
                            scroll_row += 1
                    elif mouse_y <= top:
                        if scroll_row > 0:
                            scroll_row -= 1

                    position = mouse_to_document_position(
                        mouse_x, mouse_y, document, alignments,
                        text_width, scroll_row, top, bottom, text_x
                    )
                    if position is not None:
                        line, col = position
                        cursor_line = line
                        cursor_col = col
                        selection_end = (cursor_line, cursor_col)

                elif action == "m" and selecting:
                    auto_scroll = True
                    position = mouse_to_document_position(
                        mouse_x, mouse_y, document, alignments,
                        text_width, scroll_row, top, bottom, text_x
                    )
                    if position is not None:
                        line, col = position
                        cursor_line = line
                        cursor_col = col
                        selection_end = (cursor_line, cursor_col)
                    selecting = False
                    if selection_start == selection_end:
                        selection_start = None
                        selection_end = None
                continue

            # ====================================================
            # TECLADO
            # ====================================================

            if event_type == "key":
                auto_scroll = True

                # F10 abre/cierra la barra de menús
                if value == "MENU":
                    if menu_open >= 0:
                        menu_open = -1
                    else:
                        n = len(MENUS)
                        idx = 0
                        while idx < n and MENUS[idx][1] is None:
                            idx += 1
                        if idx < n:
                            menu_open = idx
                            menu_selected = 0
                            items = MENUS[idx][1]
                            while (menu_selected < len(items)
                                   and items[menu_selected] is None):
                                menu_selected += 1
                    continue

                # Navegación del menú cuando está abierto
                if menu_open >= 0:
                    if value == "ESC":
                        menu_open = -1
                    elif value == "LEFT":
                        n = len(MENUS)
                        for i in range(1, n + 1):
                            idx = (menu_open - i) % n
                            if MENUS[idx][1] is not None:
                                menu_open = idx
                                menu_selected = 0
                                items = MENUS[idx][1]
                                while (menu_selected < len(items)
                                       and items[menu_selected] is None):
                                    menu_selected += 1
                                break
                    elif value == "RIGHT":
                        n = len(MENUS)
                        for i in range(1, n + 1):
                            idx = (menu_open + i) % n
                            if MENUS[idx][1] is not None:
                                menu_open = idx
                                menu_selected = 0
                                items = MENUS[idx][1]
                                while (menu_selected < len(items)
                                       and items[menu_selected] is None):
                                    menu_selected += 1
                                break
                    elif value == "UP":
                        items = MENUS[menu_open][1]
                        idx = menu_selected - 1
                        while idx >= 0 and items[idx] is None:
                            idx -= 1
                        if idx >= 0:
                            menu_selected = idx
                    elif value == "DOWN":
                        items = MENUS[menu_open][1]
                        idx = menu_selected + 1
                        while (idx < len(items)
                               and items[idx] is None):
                            idx += 1
                        if idx < len(items):
                            menu_selected = idx
                    elif value == "ENTER":
                        items = MENUS[menu_open][1]
                        if (items and 0 <= menu_selected
                                < len(items)):
                            item = items[menu_selected]
                            if item is not None:
                                action_key = item[2]
                                menu_open = -1
                                pending_key = action_key
                                continue
                    continue

                if value == "NEW":
                    push_undo(undo_stack, document, formatting,
                              alignments)
                    document = [""]
                    formatting = [[]]
                    alignments = [ALIGN_LEFT]
                    current_path = None
                    cursor_line = 0
                    cursor_col = 0
                    selection_start = None
                    selection_end = None
                    selecting = False
                    search_active = False
                    scroll_row = 0
                    status_message = tr("Nuevo documento")
                    status_time = time.monotonic()
                    continue

                if value == "OPEN":
                    if current_path:
                        start_dir = os.path.dirname(
                            os.path.abspath(current_path))
                    else:
                        start_dir = os.path.expanduser("~/underwood")
                    if not os.path.isdir(start_dir):
                        start_dir = os.path.expanduser("~")
                    browse_dir = start_dir
                    browse_entries = list_directory(browse_dir)
                    browse_index = 0
                    browse_scroll = 0
                    mode = "browse"
                    continue

                if search_active and value != "ENTER":
                    search_active = False

                if value == "ENTER" and search_active and search_matches:
                    search_index = (search_index + 1) % len(search_matches)
                    result = search_matches[search_index]
                    cursor_line, cursor_col = result
                    selection_start = result
                    selection_end = (result[0],
                                     result[1] + len(search_term))
                    status_message = "%d/%d" % (
                        search_index + 1, len(search_matches))
                    status_time = time.monotonic()
                    scroll_row = adjust_scroll(
                        document, cursor_line, cursor_col,
                        text_width, visible_rows, scroll_row
                    )
                    continue

                if value == "MARK" and _TTY_MODE:
                    if selecting:
                        selecting = False
                        status_message = tr("Selección terminada")
                    else:
                        selection_start = (cursor_line, cursor_col)
                        selection_end = (cursor_line, cursor_col)
                        selecting = True
                        status_message = tr("Selección iniciada")
                    status_time = time.monotonic()
                    continue

                if value == "QUIT":
                    break

                elif value == "HELP":
                    mode = "help"
                    help_scroll = 0

                elif value == "ABOUT":
                    mode = "about"
                    help_scroll = 0

                elif value == "CHAPTERS":
                    chapter_headings = collect_headings(
                        document, formatting)
                    chapter_index = 0
                    chapter_scroll = 0
                    for k, (ln, _lvl, _t) in enumerate(chapter_headings):
                        if ln >= cursor_line:
                            chapter_index = k
                            break
                    else:
                        if chapter_headings:
                            chapter_index = len(chapter_headings) - 1
                    _bx, _by, _bw, _bh, _ls, _lh = (
                        chapter_panel_geometry(width, height)
                    )
                    if chapter_index >= chapter_scroll + _lh:
                        chapter_scroll = max(
                            0, chapter_index - _lh + 1
                        )
                    mode = "chapters"

                elif value in ("H1", "H2", "H3", "H0"):
                    push_undo(undo_stack, document, formatting,
                              alignments)
                    lvl = {"H1": 1, "H2": 2, "H3": 3, "H0": 0}[value]
                    if (selection_start is not None
                            and selection_end is not None):
                        # Aplicar a todas las líneas de la selección
                        sel = selection_range(document,
                                              selection_start,
                                              selection_end)
                        if sel is not None:
                            text = document_to_string(document)
                            sline, _u = absolute_to_position(
                                text, sel[0])
                            eline, _u = absolute_to_position(
                                text, sel[1])
                            if sel[1] > sel[0]:
                                before = text[:sel[1]]
                                last_nl = before.rfind("\n")
                                if (last_nl == len(before) - 1
                                        and eline > sline):
                                    eline -= 1
                            for ln in range(sline, eline + 1):
                                if 0 <= ln < len(formatting):
                                    formatting = set_line_heading(
                                        formatting, ln, lvl
                                    )
                    else:
                        formatting = set_line_heading(
                            formatting, cursor_line, lvl
                        )
                    if lvl == 0:
                        status_message = tr("Nivel quitado")
                    else:
                        status_message = tr(
                            "Nivel %d aplicado") % lvl
                    status_time = time.monotonic()

                elif value == "SPELL":
                    if not _spell_tool():
                        status_message = tr("hunspell no instalado")
                        status_time = time.monotonic()
                    else:
                        spell_check_active = not spell_check_active
                        spell_dirty = True
                        spell_last_change = 0.0
                        spell_suggest_cache = {}
                        if spell_check_active:
                            status_message = tr("Ortografía activada")
                        else:
                            spell_positions = []
                            spell_suggestions = []
                            spell_unavailable_msg = ""
                            status_message = tr(
                                "Ortografía desactivada")
                        status_time = time.monotonic()

                elif value in ("LANG_ES", "LANG_EN"):
                    new_lang = "es" if value == "LANG_ES" else "en"

                    if new_lang == current_language():
                        status_message = tr("Ya estás en ese idioma")
                        status_time = time.monotonic()
                        continue

                    save_language_preference(new_lang)

                    if current_path is None:
                        save_path = os.path.expanduser(
                            "~/underwood/documento.rtf")
                    else:
                        save_path = current_path

                    save_document(document, formatting,
                                  alignments, save_path)

                    disable_mouse_tracking()
                    try:
                        curses.nocbreak()
                        curses.echo()
                        curses.endwin()
                    except Exception:
                        pass

                    os.environ["UNDERWOOD_LANG"] = new_lang

                    if getattr(sys, "frozen", False):
                        new_argv = [sys.executable]
                    else:
                        new_argv = [
                            sys.executable,
                            os.path.abspath(__file__),
                        ]

                    new_argv.append(save_path)

                    os.execv(sys.executable, new_argv)

                elif value in (
                    "ALIGN_LEFT", "ALIGN_CENTER",
                    "ALIGN_RIGHT", "ALIGN_JUSTIFY"
                ):
                    push_undo(undo_stack, document, formatting,
                              alignments)
                    new_align = {
                        "ALIGN_LEFT": ALIGN_LEFT,
                        "ALIGN_CENTER": ALIGN_CENTER,
                        "ALIGN_RIGHT": ALIGN_RIGHT,
                        "ALIGN_JUSTIFY": ALIGN_JUSTIFY,
                    }[value]
                    alignments = apply_alignment(
                        document, alignments, cursor_line,
                        selection_start, selection_end, new_align
                    )
                    labels = {
                        "ALIGN_LEFT": tr("Izquierda"),
                        "ALIGN_CENTER": tr("Centrada"),
                        "ALIGN_RIGHT": tr("Derecha"),
                        "ALIGN_JUSTIFY": tr("Justificada"),
                    }
                    status_message = labels[value]
                    status_time = time.monotonic()

                elif value == "SELECT_ALL":
                    if document:
                        last_line = len(document) - 1
                        selection_start = (0, 0)
                        selection_end = (
                            last_line,
                            len(document[last_line])
                        )
                        cursor_line = last_line
                        cursor_col = len(document[last_line])

                        n_lines = len(document)
                        wc = count_words(document)

                        status_message = tr(
                            "Seleccionado todo: %d líneas · %d palabras"
                        ) % (n_lines, wc)
                        status_time = time.monotonic()

                elif value == "UNDO":
                    if undo_stack:
                        entry = undo_stack.pop()
                        if len(entry) == 3:
                            document, formatting, alignments = entry
                        else:
                            document, formatting = entry
                            while len(alignments) < len(document):
                                alignments.append(ALIGN_LEFT)
                            alignments = alignments[:len(document)]
                        if cursor_line >= len(document):
                            cursor_line = max(0, len(document) - 1)
                        if cursor_col > len(document[cursor_line]):
                            cursor_col = len(document[cursor_line])
                        while len(alignments) < len(document):
                            alignments.append(ALIGN_LEFT)
                        alignments = alignments[:len(document)]
                        selection_start = None
                        selection_end = None
                        selecting = False
                        search_active = False
                        status_message = tr("Deshecho")
                    else:
                        status_message = tr("Nada que deshacer")
                    status_time = time.monotonic()

                elif value == "PAGEBREAK":
                    push_undo(undo_stack, document, formatting,
                              alignments)
                    if (selection_start is not None
                            and selection_end is not None):
                        (document, formatting, alignments,
                         cursor_line, cursor_col
                         ) = delete_selection_rich(
                             document, formatting, alignments,
                             selection_start, selection_end)
                        selection_start = None
                        selection_end = None
                        selecting = False
                    (document, formatting, alignments,
                     cursor_line, cursor_col
                     ) = insert_page_break_rich(
                         document, formatting, alignments,
                         cursor_line, cursor_col)
                    status_message = tr("Salto de página")
                    status_time = time.monotonic()

                elif value == "FIND":
                    mode = "search"
                    prompt_label = tr("Buscar:")
                    prompt_buffer = search_term

                elif value == "REPLACE":
                    mode = "replace_find"
                    prompt_label = tr("Buscar:")
                    prompt_buffer = search_term

                elif value == "PDF":
                    if export_state is not None:
                        status_message = tr(
                            "Ya hay una exportación en curso")
                        status_time = time.monotonic()
                    else:
                        if current_path is None:
                            base_path = os.path.expanduser(
                                "~/underwood/documento.rtf")
                        else:
                            base_path = current_path

                        state, err = start_pdf_export(
                            document, formatting, alignments, base_path
                        )

                        if state is None:
                            status_message = err
                            status_time = time.monotonic()
                        else:
                            export_state = state
                            export_kind = "pdf"
                            export_frames = 0
                            status_message = ""
                            status_time = 0

                elif value == "SAVE":
                    if current_path is None:
                        mode = "save_as"
                        prompt_label = tr(
                            "Nombre (se guarda en ~/underwood/):")
                        prompt_buffer = ""
                    else:
                        if save_document(
                            document, formatting, alignments,
                            current_path
                        ):
                            status_message = tr("Guardado: %s") % (
                                os.path.basename(current_path))
                        else:
                            status_message = tr("Error al guardar")
                        status_time = time.monotonic()

                elif value == "SAVE_AS":
                    mode = "save_as"
                    prompt_label = tr(
                        "Nombre (se guarda en ~/underwood/):")
                    if current_path:
                        base = os.path.basename(current_path)
                        prompt_buffer = os.path.splitext(base)[0]
                    else:
                        prompt_buffer = ""

                elif value == "SAVE_AS_DOCX":
                    mode = "save_as_docx"
                    prompt_label = tr(
                        "Nombre para .docx (se guarda en ~/underwood/):")
                    if current_path:
                        base = os.path.basename(current_path)
                        prompt_buffer = os.path.splitext(base)[0]
                    else:
                        prompt_buffer = ""

                elif value == "SAVE_AS_MD":
                    mode = "save_as_md"
                    prompt_label = tr(
                        "Nombre para .md (se guarda en ~/underwood/):")
                    if current_path:
                        base = os.path.basename(current_path)
                        prompt_buffer = os.path.splitext(base)[0]
                    else:
                        prompt_buffer = ""

                elif value == "COPY":
                    cells = selected_cells(
                        document, formatting,
                        selection_start, selection_end
                    )
                    if cells:
                        global internal_rich_clipboard
                        internal_rich_clipboard = cells
                        set_system_clipboard(cells_to_text(cells))
                        status_message = tr("Copiado")
                        status_time = time.monotonic()

                elif value == "CUT":
                    cells = selected_cells(
                        document, formatting,
                        selection_start, selection_end
                    )
                    if cells:
                        push_undo(undo_stack, document,
                                  formatting, alignments)
                        internal_rich_clipboard = cells
                        set_system_clipboard(cells_to_text(cells))
                        (document, formatting, alignments,
                         cursor_line, cursor_col
                         ) = delete_selection_rich(
                             document, formatting, alignments,
                             selection_start, selection_end)
                        selection_start = None
                        selection_end = None
                        selecting = False
                        status_message = tr("Cortado")
                        status_time = time.monotonic()

                elif value == "PASTE":
                    plain = get_system_clipboard()
                    rich_plain = cells_to_text(internal_rich_clipboard)
                    if internal_rich_clipboard and plain == rich_plain:
                        paste_cells = list(internal_rich_clipboard)
                    else:
                        paste_cells = text_to_cells(plain, typing_attrs)

                    if paste_cells:
                        push_undo(undo_stack, document,
                                  formatting, alignments)
                        if (selection_start is not None
                                and selection_end is not None):
                            (document, formatting, alignments,
                             cursor_line, cursor_col
                             ) = delete_selection_rich(
                                 document, formatting, alignments,
                                 selection_start, selection_end)
                            selection_start = None
                            selection_end = None
                            selecting = False
                        (document, formatting, alignments,
                         cursor_line, cursor_col
                         ) = insert_cells_at_cursor(
                             document, formatting, alignments,
                             cursor_line, cursor_col, paste_cells)
                        status_message = tr("Pegado")
                        status_time = time.monotonic()

                elif value == "BOLD":
                    if (selection_start is not None
                            and selection_end is not None):
                        push_undo(undo_stack, document,
                                  formatting, alignments)
                        formatting = apply_attr_to_selection(
                            document, formatting,
                            selection_start, selection_end, BOLD
                        )
                        status_message = tr("Negrita")
                    else:
                        typing_attrs ^= BOLD
                        status_message = tr("Negrita")
                    status_time = time.monotonic()

                elif value == "ITALIC":
                    if (selection_start is not None
                            and selection_end is not None):
                        push_undo(undo_stack, document,
                                  formatting, alignments)
                        formatting = apply_attr_to_selection(
                            document, formatting,
                            selection_start, selection_end, ITALIC
                        )
                        status_message = tr("Cursiva")
                    else:
                        typing_attrs ^= ITALIC
                        status_message = tr("Cursiva")
                    status_time = time.monotonic()

                elif value == "UNDERLINE":
                    if (selection_start is not None
                            and selection_end is not None):
                        push_undo(undo_stack, document,
                                  formatting, alignments)
                        formatting = apply_attr_to_selection(
                            document, formatting,
                            selection_start, selection_end, UNDERLINE
                        )
                        status_message = tr("Subrayado")
                    else:
                        typing_attrs ^= UNDERLINE
                        status_message = tr("Subrayado")
                    status_time = time.monotonic()

                elif value == "BACKSPACE":
                    push_undo(undo_stack, document, formatting,
                              alignments)
                    if (selection_start is not None
                            and selection_end is not None):
                        (document, formatting, alignments,
                         cursor_line, cursor_col
                         ) = delete_selection_rich(
                             document, formatting, alignments,
                             selection_start, selection_end)
                        selection_start = None
                        selection_end = None
                        selecting = False
                    else:
                        (document, formatting, alignments,
                         cursor_line, cursor_col
                         ) = delete_before_cursor_rich(
                             document, formatting, alignments,
                             cursor_line, cursor_col)

                elif value == "DELETE":
                    push_undo(undo_stack, document, formatting,
                              alignments)
                    if (selection_start is not None
                            and selection_end is not None):
                        (document, formatting, alignments,
                         cursor_line, cursor_col
                         ) = delete_selection_rich(
                             document, formatting, alignments,
                             selection_start, selection_end)
                        selection_start = None
                        selection_end = None
                        selecting = False
                    else:
                        (document, formatting, alignments,
                         cursor_line, cursor_col
                         ) = delete_at_cursor_rich(
                             document, formatting, alignments,
                             cursor_line, cursor_col)

                elif value == "ENTER":
                    push_undo(undo_stack, document, formatting,
                              alignments)
                    if (selection_start is not None
                            and selection_end is not None):
                        (document, formatting, alignments,
                         cursor_line, cursor_col
                         ) = delete_selection_rich(
                             document, formatting, alignments,
                             selection_start, selection_end)
                        selection_start = None
                        selection_end = None
                        selecting = False
                    (document, formatting, alignments,
                     cursor_line, cursor_col
                     ) = enter_rich(
                         document, formatting, alignments,
                         cursor_line, cursor_col)

                elif value in ("SELECT_LEFT", "SELECT_RIGHT",
                               "SELECT_UP", "SELECT_DOWN",
                               "SELECT_HOME", "SELECT_END",
                               "SELECT_PAGE_UP", "SELECT_PAGE_DOWN"):
                    # Extender selección con Shift + flechas.
                    # Si aún no hay selección, la iniciamos aquí.
                    if selection_start is None:
                        selection_start = (cursor_line, cursor_col)

                    if value == "SELECT_LEFT":
                        cursor_line, cursor_col = move_left(
                            document, cursor_line, cursor_col
                        )
                    elif value == "SELECT_RIGHT":
                        cursor_line, cursor_col = move_right(
                            document, cursor_line, cursor_col
                        )
                    elif value == "SELECT_UP":
                        cursor_line, cursor_col = move_up(
                            document, cursor_line, cursor_col,
                            text_width
                        )
                    elif value == "SELECT_DOWN":
                        cursor_line, cursor_col = move_down(
                            document, cursor_line, cursor_col,
                            text_width
                        )
                    elif value == "SELECT_HOME":
                        cursor_col = 0
                    elif value == "SELECT_END":
                        cursor_col = len(document[cursor_line])
                    elif value == "SELECT_PAGE_UP":
                        for _ in range(visible_rows):
                            cursor_line, cursor_col = move_up(
                                document, cursor_line, cursor_col,
                                text_width
                            )
                    elif value == "SELECT_PAGE_DOWN":
                        for _ in range(visible_rows):
                            cursor_line, cursor_col = move_down(
                                document, cursor_line, cursor_col,
                                text_width
                            )

                    selection_end = (cursor_line, cursor_col)
                    # Si la selección vuelve al punto de origen,
                    # la cancelamos (se comporta como el ratón).
                    if selection_start == selection_end:
                        selection_start = None
                        selection_end = None
                    auto_scroll = True

                    scroll_row = adjust_scroll(
                        document, cursor_line, cursor_col,
                        text_width, visible_rows, scroll_row
                    )
                    continue

                elif value == "LEFT":
                    cursor_line, cursor_col = move_left(
                        document, cursor_line, cursor_col
                    )
                elif value == "RIGHT":
                    cursor_line, cursor_col = move_right(
                        document, cursor_line, cursor_col
                    )
                elif value == "UP":
                    cursor_line, cursor_col = move_up(
                        document, cursor_line, cursor_col, text_width
                    )
                elif value == "DOWN":
                    cursor_line, cursor_col = move_down(
                        document, cursor_line, cursor_col, text_width
                    )

                if value in ("LEFT", "RIGHT", "UP", "DOWN"):
                    if selecting and _TTY_MODE:
                        selection_end = (cursor_line, cursor_col)
                    else:
                        selection_start = None
                        selection_end = None
                elif value in ("BACKSPACE", "DELETE", "ENTER"):
                    selection_start = None
                    selection_end = None
                    selecting = False

                scroll_row = adjust_scroll(
                    document, cursor_line, cursor_col,
                    text_width, visible_rows, scroll_row
                )
                continue

            # ====================================================
            # TEXTO
            # ====================================================
            if event_type == "char":
                if menu_open >= 0:
                    continue
                char = value
                push_undo(undo_stack, document, formatting, alignments)
                if (selection_start is not None
                        and selection_end is not None):
                    (document, formatting, alignments,
                     cursor_line, cursor_col
                     ) = delete_selection_rich(
                         document, formatting, alignments,
                         selection_start, selection_end)
                    selection_start = None
                    selection_end = None
                    selecting = False

                (document, formatting, cursor_line, cursor_col
                 ) = insert_character_rich(
                     document, formatting, cursor_line, cursor_col,
                     char, typing_attrs)

                while len(alignments) < len(document):
                    alignments.append(ALIGN_LEFT)
                alignments = alignments[:len(document)]

                scroll_row = adjust_scroll(
                    document, cursor_line, cursor_col,
                    text_width, visible_rows, scroll_row
                )

    finally:
        if export_state is not None:
            try:
                export_state["proc"].terminate()
            except Exception:
                pass
        disable_mouse_tracking()


def main():
    path = None
    if len(sys.argv) > 1:
        path = sys.argv[1]

    try:
        curses.wrapper(lambda stdscr: editor(stdscr, path))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
