#!/usr/bin/env python3
"""Read a BibTeX file and render Chicago-style bibliography entries (stdlib only).

Purpose: the citation half of the bibliography explorer (templates/bibliography-explorer/CONTRACT.md).
    parse_bib() reads entries, latex_to_unicode() decodes LaTeX, split_names() reads author lists and
    render_chicago() writes one bibliography entry as runs of plain and italic text.
Lifecycle: UTILITY (imported by build_bibliography_explorer.py)
Created: 2026-11-18

CEILING (do not soften): a rendered citation is a formatting of the fields the .bib holds. It is not a
check that the source exists or that the fields are right. Nothing is inferred: a missing field is left
out, and an entry, name or LaTeX command this module cannot read raises BibError.

Templates (Chicago notes-bibliography, bibliography-entry form; [x] = only when the field is present;
/x/ = italic). The first author is inverted; up to ten authors are listed, and for more the first seven
then "et al.". A title ending in ? or ! takes no extra period.

  book          Authors. /Title/. [Edited by Editors.] [Vol. V.] [Series Number.]
                [Address: Publisher, Year.] [Link.]
                With no author, the editors lead: "Editors, ed." or "Editors, eds."
  article       Authors. "Title." /Journal/ [V][, no. N] [(Month Year)][: Pages]. [Link.]
  incollection  Authors. "Title." In /Booktitle/[, edited by Editors][, vol. V][, Pages].
                [Series Number.] [Address: Publisher, Year.] [Link.]
  phdthesis     Authors. "Title." PhD diss.[, School][, Year]. [Link.]
  misc          Authors. "Title." [Howpublished.] [Series Number.] [Vol. V.]
                [Address: Publisher, Month Year.] [Link.]

Link is https://doi.org/<doi> when there is a DOI, otherwise the url. The note field is never part of
the citation.
"""
from __future__ import annotations

import re
import unicodedata

ENTRY_TYPES = ("book", "article", "incollection", "phdthesis", "misc")
TEXT_FIELDS = (
    "title", "year", "month", "journal", "booktitle", "publisher", "address", "volume", "number",
    "series", "pages", "school", "howpublished", "note",
)
RAW_FIELDS = ("doi", "isbn", "issn", "url")
NAME_FIELDS = ("author", "editor")
KNOWN_FIELDS = TEXT_FIELDS + RAW_FIELDS + NAME_FIELDS
RENDERER_ID = "researchteam-chicago-v1"

_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
           "October", "November", "December"]
_MONTH_MACROS = {m[:3].lower(): m for m in _MONTHS}

# Accent commands -> combining character.
_ACCENTS = {
    "'": "́", "`": "̀", "^": "̂", '"': "̈", "~": "̃", "=": "̄",
    ".": "̇", "u": "̆", "v": "̌", "H": "̋", "c": "̧", "d": "̣",
    "b": "̱", "k": "̨", "r": "̊",
}
_SYMBOLS = {
    "ss": "ß", "ae": "æ", "AE": "Æ", "oe": "œ", "OE": "Œ", "o": "ø", "O": "Ø", "aa": "å", "AA": "Å",
    "l": "ł", "L": "Ł", "i": "ı", "j": "ȷ", "dh": "ð", "DH": "Ð", "th": "þ", "TH": "Þ", "dj": "đ",
    "DJ": "Đ", "S": "§", "P": "¶", "dots": "…", "ldots": "…", "textendash": "–", "textemdash": "—",
    "textquoteleft": "‘", "textquoteright": "’", "textquotedblleft": "“", "textquotedblright": "”",
    "textasciitilde": "~", "textbackslash": "\\",
}
# Commands whose argument is kept as plain text.
_WRAPPERS = {"emph", "textit", "textbf", "textsc", "textrm", "textsf", "texttt", "textup", "mbox"}
_ESCAPED = "&%$#_{}"
_DOTLESS = {"ı": "i", "ȷ": "j"}


class BibError(ValueError):
    """A .bib file, entry, name or LaTeX string that cannot be read."""


# --------------------------------------------------------------------------- LaTeX -> Unicode
def latex_to_unicode(text: str) -> str:
    """Decode LaTeX to Unicode plain text. Raises BibError on anything it does not know."""
    out, i = _decode(text, 0, False)
    if i != len(text):
        raise BibError(f"unbalanced '}}' in {text!r}")
    return unicodedata.normalize("NFC", re.sub(r"[ \t\r\n]+", " ", out).strip())


def _decode(s: str, i: int, in_group: bool) -> tuple[str, int]:
    out: list[str] = []
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == "{":
            inner, i = _decode(s, i + 1, True)
            out.append(inner)
        elif ch == "}":
            if in_group:
                return "".join(out), i + 1
            return "".join(out), i          # the caller reports the stray brace
        elif ch == "\\":
            piece, i = _command(s, i + 1)
            out.append(piece)
        elif ch == "$":
            raise BibError(f"math mode is not supported: {s!r}")
        elif ch == "~":
            out.append(" ")
            i += 1
        elif ch == "-":
            j = i
            while j < n and s[j] == "-":
                j += 1
            run = j - i
            out.append({1: "-", 2: "–", 3: "—"}.get(run, "-" * run))
            i = j
        elif s.startswith("``", i):
            out.append("“")
            i += 2
        elif s.startswith("''", i):
            out.append("”")
            i += 2
        else:
            out.append(ch)
            i += 1
    if in_group:
        raise BibError(f"unclosed '{{' in {s!r}")
    return "".join(out), i


def _command(s: str, i: int) -> tuple[str, int]:
    """Decode the command that starts after a backslash at s[i-1]."""
    n = len(s)
    if i >= n:
        raise BibError(f"a backslash ends the text: {s!r}")
    ch = s[i]
    if ch in _ESCAPED:
        return ch, i + 1
    if ch in " \n\t":
        return " ", i + 1
    if ch == ",":
        return " ", i + 1
    if ch in "-/":
        return "", i + 1
    if not ch.isalpha():
        if ch in _ACCENTS:
            return _accent(s, i + 1, _ACCENTS[ch])
        raise BibError(f"unknown LaTeX command \\{ch} in {s!r}")
    j = i
    while j < n and s[j].isalpha():
        j += 1
    name = s[i:j]
    k = j
    while k < n and s[k] in " \t\n":        # a control word swallows the spaces after it
        k += 1
    if name in _SYMBOLS:
        if s.startswith("{}", k):
            k += 2
        return _SYMBOLS[name], k
    if name in _ACCENTS:
        return _accent(s, k, _ACCENTS[name])
    if name in _WRAPPERS:
        return "", k
    raise BibError(f"unknown LaTeX command \\{name} in {s!r}")


def _accent(s: str, i: int, combining: str) -> tuple[str, int]:
    """Apply a combining accent to the argument that starts at s[i]."""
    n = len(s)
    if i >= n:
        raise BibError(f"an accent has no letter: {s!r}")
    if s[i] == "{":
        arg, i = _decode(s, i + 1, True)
    elif s[i] == "\\":
        arg, i = _command(s, i + 1)
    else:
        arg, i = s[i], i + 1
    if not arg:
        raise BibError(f"an accent has no letter: {s!r}")
    base = _DOTLESS.get(arg[0], arg[0])
    return unicodedata.normalize("NFC", base + combining) + arg[1:], i


def _raw_value(text: str, field: str) -> str:
    """A url, doi, isbn or issn: braces dropped and escaped characters restored, nothing else decoded."""
    out = re.sub(r"\\([&%#_~])", r"\1", text)
    out = out.replace("{", "").replace("}", "").strip()
    if "\\" in out or re.search(r"\s", out):
        raise BibError(f"the {field} field cannot be read as plain text: {text!r}")
    return out


# --------------------------------------------------------------------------- BibTeX parser
def parse_bib(text: str) -> list[dict]:
    """Return [{"key", "type", "line", "fields": {lowercase name: raw value}}] in file order."""
    entries: list[dict] = []
    macros = dict(_MONTH_MACROS)
    seen: set[str] = set()
    i, n = 0, len(text)
    head = re.compile(r"@\s*([A-Za-z]+)\s*([{(])")
    while True:
        at = text.find("@", i)
        if at < 0:
            break
        line_start = text.rfind("\n", 0, at) + 1
        if text[line_start:at].lstrip().startswith("%"):
            nl = text.find("\n", at)
            i = n if nl < 0 else nl
            continue
        line = text.count("\n", 0, at) + 1
        m = head.match(text, at)
        if not m:
            raise BibError(f"line {line}: '@' does not start an entry")
        etype = m.group(1).lower()
        close = "}" if m.group(2) == "{" else ")"
        i = m.end()
        if etype in ("comment", "preamble"):
            i = _skip_block(text, i, close, line)
            continue
        if etype == "string":
            name, value, i = _field(text, i, close, macros, f"@string at line {line}")
            macros[name] = value
            i = _expect_close(text, i, close, f"@string at line {line}")
            continue
        km = re.compile(r"\s*([^,\s{}()]+)\s*,").match(text, i)
        if not km:
            raise BibError(f"line {line}: the @{etype} entry has no key")
        key = km.group(1)
        where = f"entry {key!r} (line {line})"
        if key.lower() in seen:
            raise BibError(f"{where}: the key is used twice (keys are compared without regard to case)")
        seen.add(key.lower())
        i = km.end()
        fields: dict[str, str] = {}
        while True:
            i = _skip_ws(text, i, ",")
            if i >= n:
                raise BibError(f"{where}: the entry is not closed")
            if text[i] == close:
                i += 1
                break
            name, value, i = _field(text, i, close, macros, where)
            if i < n and text[i] not in ("," + close):
                raise BibError(f"{where}: a comma is missing after the field {name!r}")
            if name in fields:
                raise BibError(f"{where}: the field {name!r} appears twice")
            if re.search(r"\n\s*@[A-Za-z]+\s*[{(]", value):
                raise BibError(f"{where}: the field {name!r} runs into the next entry (unclosed brace?)")
            fields[name] = value
        entries.append({"key": key, "type": etype, "line": line, "fields": fields})
    return entries


def _skip_ws(text: str, i: int, also: str = "") -> int:
    while i < len(text) and (text[i].isspace() or text[i] in also):
        i += 1
    return i


def _skip_block(text: str, i: int, close: str, line: int) -> int:
    depth = 1
    opener = "{" if close == "}" else "("
    while i < len(text):
        if text[i] == opener:
            depth += 1
        elif text[i] == close:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise BibError(f"line {line}: the block is not closed")


def _expect_close(text: str, i: int, close: str, where: str) -> int:
    i = _skip_ws(text, i, ",")
    if i >= len(text) or text[i] != close:
        raise BibError(f"{where}: not closed")
    return i + 1


def _field(text: str, i: int, close: str, macros: dict, where: str) -> tuple[str, str, int]:
    """Read `name = value [# value ...]` starting at text[i]."""
    m = re.compile(r"\s*([A-Za-z][\w:.+-]*)\s*=\s*").match(text, i)
    if not m:
        raise BibError(f"{where}: expected a field near {text[i:i + 30]!r}")
    name = m.group(1).lower()
    i = m.end()
    parts: list[str] = []
    n = len(text)
    while True:
        if i >= n:
            raise BibError(f"{where}: the field {name!r} has no value")
        ch = text[i]
        if ch == "{":
            j, depth = i + 1, 1
            while j < n and depth:
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                j += 1
            if depth:
                raise BibError(f"{where}: unclosed brace in the field {name!r}")
            parts.append(text[i + 1:j - 1])
            i = j
        elif ch == '"':
            j, depth = i + 1, 0
            while j < n and not (text[j] == '"' and depth == 0):
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                    if depth < 0:
                        raise BibError(f"{where}: unbalanced brace in the field {name!r}")
                j += 1
            if j >= n:
                raise BibError(f"{where}: unclosed quote in the field {name!r}")
            parts.append(text[i + 1:j])
            i = j + 1
        else:
            wm = re.compile(r"[A-Za-z0-9][\w.:+-]*").match(text, i)
            if not wm:
                raise BibError(f"{where}: the field {name!r} has no value")
            word = wm.group(0)
            if word.isdigit():
                parts.append(word)
            elif word.lower() in macros:
                parts.append(macros[word.lower()])
            else:
                raise BibError(f"{where}: undefined abbreviation {word!r} in the field {name!r}")
            i = wm.end()
        i = _skip_ws(text, i)
        if i < n and text[i] == "#":
            i = _skip_ws(text, i + 1)
            continue
        return name, "".join(parts), i


# --------------------------------------------------------------------------- names
def _split_depth0(text: str, pattern: str) -> list[str]:
    """Split on a regex, but only where the match starts outside braces."""
    parts, depth, start, i = [], 0, 0, 0
    rx = re.compile(pattern)
    while i < len(text):
        ch = text[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif depth == 0:
            m = rx.match(text, i)
            if m and m.end() > i:
                parts.append(text[start:i])
                start = i = m.end()
                continue
        i += 1
    parts.append(text[start:])
    return parts


def _wholly_braced(text: str) -> bool:
    if not (text.startswith("{") and text.endswith("}")):
        return False
    depth = 0
    for i, ch in enumerate(text):
        if ch == "\\":
            continue
        if ch == "{" and (i == 0 or text[i - 1] != "\\"):
            depth += 1
        elif ch == "}" and text[i - 1] != "\\":
            depth -= 1
            if depth == 0 and i != len(text) - 1:
                return False
    return depth == 0


def _is_particle(word: str) -> bool:
    """True for a lower-case name particle such as "von" or "de"."""
    if word.startswith("{"):
        return False
    decoded = latex_to_unicode(word)
    first = next((c for c in decoded if c.isalpha()), "")
    return bool(first) and first.islower()


def split_names(raw: str) -> tuple[list[dict], bool]:
    """Read a BibTeX name list. Returns (names, et_al). A name is {"family", "given"?, "suffix"?} or
    {"literal"} for a brace-protected (corporate) name."""
    names: list[dict] = []
    et_al = False
    for item in _split_depth0(raw.strip(), r"\s+[aA][nN][dD]\s+"):
        item = item.strip()
        if not item:
            raise BibError(f"an empty name in {raw!r}")
        if et_al:
            raise BibError(f"'others' must be the last name: {raw!r}")
        if item.lower() == "others":
            et_al = True
            continue
        if _wholly_braced(item):
            literal = latex_to_unicode(item)
            if not literal:
                raise BibError(f"an empty name in {raw!r}")
            names.append({"literal": literal})
            continue
        parts = [p.strip() for p in _split_depth0(item, r",")]
        if len(parts) == 1:
            words = [w for w in _split_depth0(parts[0], r"\s+") if w]
            if len(words) == 1:
                family, given = words, []
            else:
                particles = [k for k, w in enumerate(words[:-1]) if _is_particle(w)]
                cut = particles[0] if particles else len(words) - 1
                given, family = words[:cut], words[cut:]
            name = {"family": latex_to_unicode(" ".join(family))}
            if given:
                name["given"] = latex_to_unicode(" ".join(given))
        elif len(parts) == 2:
            name = {"family": latex_to_unicode(parts[0])}
            if parts[1]:
                name["given"] = latex_to_unicode(parts[1])
        elif len(parts) == 3:
            name = {"family": latex_to_unicode(parts[0])}
            if parts[2]:
                name["given"] = latex_to_unicode(parts[2])
            if parts[1]:
                name["suffix"] = latex_to_unicode(parts[1])
        else:
            raise BibError(f"too many commas in the name {item!r}")
        if not name["family"]:
            raise BibError(f"a name without a family name: {item!r}")
        names.append(name)
    if et_al and not names:
        raise BibError(f"'others' with no name before it: {raw!r}")
    return names, et_al


# --------------------------------------------------------------------------- decoded entry
def decode_entry(entry: dict) -> tuple[dict, list[str]]:
    """Decode a parsed entry's fields. Returns (fields, names of fields that are not carried)."""
    raw = entry["fields"]
    where = f"entry {entry['key']!r}"
    fields: dict = {}
    try:
        for name in TEXT_FIELDS:
            if raw.get(name, "").strip():
                fields[name] = latex_to_unicode(raw[name])
        for name in RAW_FIELDS:
            if raw.get(name, "").strip():
                fields[name] = _raw_value(raw[name], name)
        for name, out in (("author", "authors"), ("editor", "editors")):
            if raw.get(name, "").strip():
                names, et_al = split_names(raw[name])
                fields[out] = names
                if et_al:
                    fields[out + "_et_al"] = True
    except BibError as exc:
        raise BibError(f"{where}: {exc}") from None
    if "doi" in fields:
        doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", fields["doi"], flags=re.IGNORECASE)
        if not doi.startswith("10."):
            raise BibError(f"{where}: the doi does not start with '10.': {fields['doi']!r}")
        fields["doi"] = doi
    if "month" in fields:
        fields["month"] = _month(fields["month"])
    if "pages" in fields:
        fields["pages"] = re.sub(r"(?<=\d)\s*-\s*(?=\d)", "–", fields["pages"])
    extra = sorted(k for k, v in raw.items() if k not in KNOWN_FIELDS and v.strip())
    return fields, extra


def _month(value: str) -> str:
    v = value.strip().rstrip(".")
    if v.isdigit() and 1 <= int(v) <= 12:
        return _MONTHS[int(v) - 1]
    return _MONTH_MACROS.get(v[:3].lower(), value) if len(v) == 3 else value


# --------------------------------------------------------------------------- Chicago
def _format_name(name: dict, inverted: bool) -> str:
    if "literal" in name:
        return name["literal"]
    family, given, suffix = name["family"], name.get("given", ""), name.get("suffix", "")
    if inverted:
        return ", ".join(p for p in (family, given, suffix) if p)
    return " ".join(p for p in (given, family, suffix) if p)


def format_names(names: list[dict], et_al: bool = False, invert_first: bool = True) -> str:
    shown = names
    if len(names) > 10:
        shown, et_al = names[:7], True
    parts = [_format_name(nm, invert_first and k == 0) for k, nm in enumerate(shown)]
    if et_al:
        return ", ".join(parts) + ", et al."
    if len(parts) <= 1:
        return "".join(parts)
    if len(parts) == 2:
        return f"{parts[0]}, and {parts[1]}" if invert_first else f"{parts[0]} and {parts[1]}"
    return ", ".join(parts[:-1]) + ", and " + parts[-1]


class _Runs:
    """Sentences of plain and italic text, joined by one space."""

    def __init__(self) -> None:
        self.runs: list[list] = []

    def _add(self, text: str, italic: bool) -> None:
        if not text:
            return
        if self.runs and self.runs[-1][1] == italic:
            self.runs[-1][0] += text
        else:
            self.runs.append([text, italic])

    def sentence(self, *pieces) -> None:
        """Add one sentence. A piece is a str (plain) or a (str, True) tuple (italic)."""
        pieces = [p for p in pieces if (p if isinstance(p, str) else p[0])]
        if not pieces:
            return
        if self.runs:
            self._add(" ", False)
        last = ""
        for p in pieces:
            text, italic = (p, False) if isinstance(p, str) else p
            self._add(text, italic)
            last = text
        if not last.rstrip("”’\"')").endswith((".", "?", "!")):
            self._add(".", False)

    def result(self) -> list[dict]:
        return [{"text": t, "italic": i} for t, i in self.runs]


def _quoted(title: str) -> str:
    title = title.replace("“", "‘").replace("”", "’")      # quotes inside quotes become single
    return "“" + title + ("" if title.endswith(("?", "!", ".")) else ".") + "”"


def _publication(fields: dict, date: str) -> str:
    place = ": ".join(p for p in (fields.get("address", ""), fields.get("publisher", "")) if p)
    return ", ".join(p for p in (place, date) if p)


def _series(fields: dict, with_number: bool) -> str:
    series = fields.get("series", "")
    if not series:
        return ""
    return f"{series} {fields['number']}" if with_number and fields.get("number") else series


def _link(fields: dict) -> str:
    if fields.get("doi"):
        return "https://doi.org/" + fields["doi"]
    return fields.get("url", "")


def render_chicago(etype: str, fields: dict) -> list[dict]:
    """Render decoded fields as [{"text", "italic"}]. The joined text is the citation."""
    if etype not in ENTRY_TYPES:
        raise BibError(f"unsupported entry type @{etype} (supported: {', '.join(ENTRY_TYPES)})")
    f = fields
    out = _Runs()
    authors = format_names(f.get("authors", []), f.get("authors_et_al", False))
    editors = f.get("editors", [])
    editors_plain = format_names(editors, f.get("editors_et_al", False), invert_first=False)
    title = f.get("title", "")
    year = f.get("year", "")
    month_year = " ".join(p for p in (f.get("month", ""), year) if p)

    if authors:
        out.sentence(authors)
    elif editors and etype == "book":
        lead = format_names(editors, f.get("editors_et_al", False))
        out.sentence(lead + (", eds." if len(editors) > 1 or f.get("editors_et_al") else ", ed."))
        editors_plain = ""

    if etype == "book":
        out.sentence((title, True))
        if editors_plain:
            out.sentence("Edited by " + editors_plain)
        if f.get("volume"):
            out.sentence("Vol. " + f["volume"])
        out.sentence(_series(f, True))
        out.sentence(_publication(f, year))
    elif etype == "article":
        if title:
            out.sentence(_quoted(title))
        tail = ""
        if f.get("volume"):
            tail += " " + f["volume"]
        if f.get("number"):
            tail += ", no. " + f["number"]
        if month_year:
            tail += f" ({month_year})"
        if f.get("pages"):
            tail += ": " + f["pages"]
        journal = f.get("journal", "")
        out.sentence((journal, True), tail if journal else tail.lstrip(" ,:"))
    elif etype == "incollection":
        if title:
            out.sentence(_quoted(title))
        tail = [("edited by " + editors_plain) if editors_plain else "",
                ("vol. " + f["volume"]) if f.get("volume") else "", f.get("pages", "")]
        tail = ", ".join(p for p in tail if p)
        book = f.get("booktitle", "")
        if book:
            out.sentence("In ", (book, True), (", " + tail) if tail else "")
        elif tail:
            out.sentence(tail[0].upper() + tail[1:])
        out.sentence(_series(f, True))
        out.sentence(_publication(f, year))
    elif etype == "phdthesis":
        if title:
            out.sentence(_quoted(title))
        out.sentence(", ".join(p for p in ("PhD diss.", f.get("school", ""), year) if p))
    else:  # misc
        if title:
            out.sentence(_quoted(title))
        out.sentence(f.get("howpublished", ""))
        out.sentence(_series(f, True))
        if f.get("volume"):
            out.sentence("Vol. " + f["volume"])
        out.sentence(_publication(f, month_year))
    out.sentence(_link(f))
    return out.result()
