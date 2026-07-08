#!/usr/bin/env bash
# NOTE: intentionally NOT `set -e`. This is a multi-grep/awk stdout scanner; a grep with
# no match (exit 1) is normal and must not abort the run. We manage errors explicitly.
set -uo pipefail

# check_citation_integrity.sh
#
# Deterministic detector for the *mechanical* subset of the 2-fold citation & claim audit
# (Dimension A = citation/bibliography/URL integrity; a light Dimension-B in-text signal).
# The *semantic* audit — does a source actually support a claim — is the job of the doubled
# @reference-manager / @technical-validator protocol (docs/citation-claim-audit-protocol.md),
# not this script.
#
# ANTI-FABRICATION CEILING (do not soften): a green run establishes WELL-FORMED, never RESOLVED.
# No script or model can PROVE a citation or claim is genuine — a syntactically valid but
# fabricated DOI, or a plausible but unsupported paraphrase, passes every check here. This tool
# catches structural defects deterministically and *surfaces* fabrication-shaped signals; final
# resolution is a human, out-of-band act.
#
# Result classes (each finding line is code-tagged so @conflict-auditor consolidation into its
# CU/FU/AE/RM/RX/PE taxonomy is mechanical):
#   DEFECT        gate-eligible, MECHANICALLY CERTAIN ONLY:
#                   [DUP]  duplicate citation key within a .bib
#                   [META] .bib entry with no title, or with no author AND no editor
#                   [LINK] .bib entry with no source link (no url and no doi). Every citation
#                          must link to its source; a purchase link or a descriptive URL
#                          (e.g. RePEc, WorldCat) is acceptable when no direct link exists.
#   NEEDS-REVIEW  ADVISORY ONLY (never affects exit code) — every heuristic/fuzzy signal:
#                   [CU]   in-text (Author Year) with no bibliography backing
#                   [RM]   a deliverable "## References" entry absent from the .bib
#                   [PE]   a .bib entry apparently never cited
#                   [META] .bib entry missing a year (legitimate for @misc/software/forthcoming)
#                   [URL]  a url= value that does not look like a URL
#                   [DOI]  a doi= value that does not look like a DOI
#                   [STRUCT] project has no .bib, or a deliverable has no "## References"
#   PASS          none of the above
#
# Usage:
#   scripts/check_citation_integrity.sh [project-name-or-path]
#     no arg  -> scan every research project under Projects/ and .projects/ (recursive)
#     <name>  -> check only the matching project
#
# Exit codes (mirrors check_methodology_coverage.sh):
#   0  no DEFECT (or advisory mode, or nothing in scope). NEEDS-REVIEW never changes the code.
#   1  at least one DEFECT in blocking mode
#   2  usage / environment error
#
# Environment:
#   RT_ROOT=<path>                    override repo root (used by the test harness)
#   CITATION_INTEGRITY_ADVISORY=1     warn-only: report DEFECTs but always exit 0

ROOT_DIR="${RT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
ADVISORY="${CITATION_INTEGRITY_ADVISORY:-0}"
target="${1:-}"

WORK="$(mktemp -d 2>/dev/null || mktemp -d -t rt-citint)"
trap 'rm -rf "$WORK"' EXIT

# ---------------------------------------------------------------------------
# Project discovery — marker-based, recursive, over Projects/ and .projects/,
# pruning backup/plan/asset trees. (Diverges from methodology's flat glob by design.)
# ---------------------------------------------------------------------------
discover_projects() {
  local base d
  for base in "$ROOT_DIR/Projects" "$ROOT_DIR/.projects"; do
    [ -d "$base" ] || continue
    find "$base" \
      \( -name '.agentteams-backups' -o -name '.git' -o -name 'plans' \
         -o -name 'JSModules' -o -name 'cssfiles' -o -name 'node_modules' \) -prune \
      -o -type d -print 2>/dev/null
  done | while IFS= read -r d; do
    is_research_project "$d" && printf '%s\n' "$d"
  done
}

# A directory is a research project if it DIRECTLY contains a research marker.
is_research_project() {
  local d="$1"
  [ -f "$d/00-research-plan.md" ] && return 0
  [ -d "$d/references" ] && return 0
  ls "$d"/[0-9][0-9]-*.md >/dev/null 2>&1 && return 0
  return 1
}

resolve_target() {
  local t="$1" p
  if [ -d "$t" ] && is_research_project "$t"; then printf '%s\n' "$(cd "$t" && pwd)"; return 0; fi
  for p in $(discover_projects); do
    case "$p" in
      */"$t") printf '%s\n' "$p"; return 0 ;;
    esac
  done
  return 1
}

project_bibs() { find "$1" -type f -name '*.bib' 2>/dev/null | sort; }

# Deliverable markdown = the asserted-claims articles: top-level NN-*.md and other top-level .md,
# EXCLUDING the research plan (scaffolding, not an article) and anything under references/.
project_deliverables() {
  find "$1" -maxdepth 1 -type f -name '*.md' 2>/dev/null \
    | grep -v '/00-research-plan\.md$' | sort
}

# ---------------------------------------------------------------------------
# Robust BibTeX entry assembler (line-based; tolerant of stray '@' inside field values,
# multi-line fields, and nested braces). Emits one TSV row per real entry:
#   key <TAB> year <TAB> who(0|1) <TAB> title(0|1) <TAB> hasyear(0|1) <TAB> "surname1 surname2 ..."
# ---------------------------------------------------------------------------
bib_entries_tsv() {
  awk '
    function clean(s){ gsub(/[{}"'"'"'.]/,"",s); gsub(/^[ \t]+|[ \t]+$/,"",s); return tolower(s) }
    function field_val(rec, name,   p, rest, e, e2){
      if (!match(rec, name "[ \t]*=[ \t]*\\{")) return ""
      rest = substr(rec, RSTART+RLENGTH)          # text right after the opening "{"
      e = index(rest, "},")                        # field terminator "}," (value braces may nest)
      if (e > 0) return substr(rest, 1, e-1)
      e2 = index(rest, "}")
      return (e2 > 0) ? substr(rest, 1, e2-1) : rest
    }
    function surnames_of(rec,   av, n, aa, i, a, m, ww, s, out){
      av = field_val(rec, "[Aa][Uu][Tt][Hh][Oo][Rr]")
      if (av == "") av = field_val(rec, "[Ee][Dd][Ii][Tt][Oo][Rr]")
      if (av == "") return ""
      n = split(av, aa, / and /)
      out = ""
      for (i=1;i<=n;i++){
        a = aa[i]
        if (index(a, ",") > 0){ sub(/,.*/, "", a); s = a }
        else { m = split(a, ww, " "); s = ww[m] }
        s = clean(s)
        if (s != "") out = out (out==""?"":" ") s
      }
      return out
    }
    function flush(   lc, t, key, yr, who, tit, hy, hl, s){
      if (cur == "") return
      lc = tolower(cur)
      t = ""; if (match(cur, /@[A-Za-z]+/)) t = tolower(substr(cur, RSTART+1, RLENGTH-1))
      if (t=="string" || t=="comment" || t=="preamble"){ cur=""; return }
      key = ""
      if (match(cur, /@[A-Za-z]+[ \t]*\{[ \t]*[^,\r\n{} \t]+/)){
        key = substr(cur, RSTART, RLENGTH); sub(/@[A-Za-z]+[ \t]*\{[ \t]*/, "", key)
      }
      key = clean(key)
      if (key == ""){ cur=""; return }
      who = (lc ~ /author[ \t]*=/ || lc ~ /editor[ \t]*=/) ? 1 : 0
      tit = (lc ~ /title[ \t]*=/) ? 1 : 0
      hy  = (lc ~ /year[ \t]*=/) ? 1 : 0
      # source link present = a url= or doi= field (a doi resolves via https://doi.org/...).
      # The url may be a direct, purchase, or descriptive URL (RePEc, WorldCat, etc.).
      hl  = (lc ~ /[^a-z]url[ \t]*=/ || lc ~ /[^a-z]doi[ \t]*=/ || lc ~ /^url[ \t]*=/ || lc ~ /^doi[ \t]*=/) ? 1 : 0
      yr = ""
      if (match(cur, /[Yy][Ee][Aa][Rr][ \t]*=[ \t]*[{"]?[ \t]*[0-9][0-9][0-9][0-9]/)){
        s = substr(cur, RSTART, RLENGTH); if (match(s, /[0-9][0-9][0-9][0-9]/)) yr = substr(s, RSTART, RLENGTH)
      }
      if (yr == "") yr = "-"    # placeholder: keep the TSV column count stable ("read" collapses empty tab fields)
      printf "%s\t%s\t%d\t%d\t%d\t%d\t%s\n", key, yr, who, tit, hy, hl, surnames_of(cur)
      cur = ""
    }
    /^[ \t]*@[A-Za-z]+[ \t]*\{/ { flush(); cur = $0 " "; next }
    { if (cur != "") cur = cur $0 " " }
    END { flush() }
  ' "$1"
}

# Index for the fuzzy (advisory) matchers:  year <TAB> lowerkey <TAB> surnames
bib_index() { bib_entries_tsv "$1" | awk -F'\t' '{ printf "%s\t%s\t%s\n", $2, $1, $7 }'; }

# Is (surname, year) backed by any entry in the index file? 0=backed, 1=not.
backed_in_index() {
  local qs="$1" qy="$2" idx="$3"
  awk -F'\t' -v qs="$qs" -v qy="$qy" '
    { if ($1!=qy) next
      if (index($2,qs)>0){ found=1; exit }
      n=split($3,w," "); for(i=1;i<=n;i++) if(w[i]==qs){ found=1; exit }
    } END{ exit(found?0:1) }' "$idx"
}

# Cited (surname<TAB>year) pairs from a markdown BODY (References already stripped).
#   (a) citation-group adjacency "(Surname 2005" / "; Surname 2005"
#   (b) narrative "Surname (2005)", but NOT when preceded by another Capitalized word
#       (that pattern is a multi-word Title, e.g. "Hyrule Historia (2011)", not an author).
intext_pairs() {
  local body="$1"
  {
    grep -oE '[(;] ?[A-Z][A-Za-z'"'"'.-]+ [12][0-9][0-9][0-9][a-z]?' "$body" 2>/dev/null \
      | sed -E 's/^[(;] ?//'
    grep -oE '[A-Za-z][A-Za-z'"'"'.-]* [A-Z][A-Za-z'"'"'.-]+ \([12][0-9][0-9][0-9][a-z]?\)' "$body" 2>/dev/null \
      | awk '{ if ($1 ~ /^[A-Z]/) next; print $2, $3 }' | sed -E 's/[()]//g'
  } | while IFS= read -r m; do
      [ -n "$m" ] || continue
      local s y
      s="$(printf '%s' "$m" | sed -E 's/ [0-9]{4}[a-z]?$//' | tr -d '.' | tr '[:upper:]' '[:lower:]')"
      y="$(printf '%s' "$m" | grep -oE '[0-9]{4}' | head -1)"
      [ -n "$s" ] && [ -n "$y" ] && printf '%s\t%s\n' "$s" "$y"
    done | sort -u
}

# "leading surname <TAB> year" from each entry line of a "## References" block.
refs_pairs() {
  local block="$1"
  grep -oE '^[A-Z][A-Za-z'"'"'.-]+.*[12][0-9][0-9][0-9]' "$block" 2>/dev/null \
    | while IFS= read -r line; do
        local s y
        s="$(printf '%s' "$line" | sed -E 's/[ ,].*$//' | tr -d '.' | tr '[:upper:]' '[:lower:]')"
        y="$(printf '%s' "$line" | grep -oE '[12][0-9][0-9][0-9]' | head -1)"
        [ -n "$s" ] && [ -n "$y" ] && printf '%s\t%s\n' "$s" "$y"
      done | sort -u
}

# Split a deliverable into BODY (pre-references) and REFS. Truncates both first so nothing
# leaks between files (a "## References"-less deliverable yields an EMPTY refs file).
split_deliverable() {
  : > "$WORK/refs"; : > "$WORK/body"
  awk '
    BEGIN{ inref=0 }
    /^#{1,6}[ \t]+([Rr]eferences|[Bb]ibliography|[Ww]orks [Cc]ited)[ \t]*$/ { inref=1; next }
    /^#{1,6}[ \t]+/ { if (inref==1) inref=0 }
    { if (inref==1) print > REFS; else print > BODY }
  ' REFS="$WORK/refs" BODY="$WORK/body" "$1"
}

emit() { printf '  %-16s %s\n' "$1" "$2"; }

check_bib_defects() {
  local bib="$1" rel="$2"
  bib_entries_tsv "$bib" | cut -f1 | sort | uniq -d | while IFS= read -r k; do
    [ -n "$k" ] && emit "DEFECT[DUP]" "$rel: citation key defined more than once: '$k'"
  done
  bib_entries_tsv "$bib" | while IFS=$'\t' read -r key year who title hasyear haslink surn; do
    [ -n "$key" ] || continue
    local miss=""
    [ "$title" = "0" ] && miss="${miss}title "
    [ "$who" = "0" ]   && miss="${miss}author/editor "
    [ -n "$miss" ] && emit "DEFECT[META]" "$rel: entry '$key' missing required field(s): $miss"
    [ "$haslink" = "0" ] && emit "DEFECT[LINK]" "$rel: entry '$key' has no source link — add a url (direct, a purchase link, or a descriptive URL e.g. RePEc/WorldCat) or a doi"
    [ "$hasyear" = "0" ] && emit "NEEDS-REVIEW[META]" "$rel: entry '$key' has no year (ok for software/forthcoming — verify)"
  done
}

# Locator syntax (ADVISORY). Deliberately lenient so valid parenthesized DOIs
# (e.g. 10.1016/0022-0531(71)90013-5) and normal URLs never trip.
check_bib_locators() {
  local bib="$1" rel="$2"
  grep -oE '[Uu][Rr][Ll][ \t]*=[ \t]*[{"][^}"]*' "$bib" 2>/dev/null \
    | sed -E 's/.*[{"]//' | while IFS= read -r v; do
        [ -n "$v" ] || continue
        case "$v" in
          http://*|https://*|ftp://*) : ;;
          *) emit "NEEDS-REVIEW[URL]" "$rel: url value does not look like a URL: '$v'" ;;
        esac
      done
  grep -oE '[Dd][Oo][Ii][ \t]*=[ \t]*[{"][^}"]*' "$bib" 2>/dev/null \
    | sed -E 's/.*[{"]//' | while IFS= read -r v; do
        [ -n "$v" ] || continue
        case "$v" in
          10.*/*) : ;;
          *) emit "NEEDS-REVIEW[DOI]" "$rel: doi value does not look like a DOI: '$v'" ;;
        esac
      done
}

audit_project() {
  local dir="$1" name idx cited bibs nbib b rel f frel
  name="$(printf '%s' "${dir#$ROOT_DIR/}")"
  printf '\n=== %s\n' "$name"

  bibs="$(project_bibs "$dir")"
  nbib="$(printf '%s' "$bibs" | grep -c . || true)"
  [ "$nbib" -eq 0 ] && emit "NEEDS-REVIEW[STRUCT]" "no .bib file under the project (bibliography audit skipped)"

  printf '%s\n' "$bibs" | while IFS= read -r b; do
    [ -n "$b" ] || continue
    rel="${b#$dir/}"
    check_bib_defects "$b" "$rel"
    check_bib_locators "$b" "$rel"
  done

  idx="$WORK/idx"; : > "$idx"
  printf '%s\n' "$bibs" | while IFS= read -r b; do
    [ -n "$b" ] || continue
    bib_index "$b"
  done > "$idx"

  cited="$WORK/cited"; : > "$cited"
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    frel="${f#$dir/}"
    split_deliverable "$f"
    intext_pairs "$WORK/body" > "$WORK/itp"

    # STRUCT: a deliverable that cites sources in-text but carries no reference list.
    if [ -s "$WORK/itp" ] && [ ! -s "$WORK/refs" ]; then
      emit "NEEDS-REVIEW[STRUCT]" "$frel: has in-text citations but no '## References' section"
    fi

    if [ "$nbib" -gt 0 ]; then
      while IFS=$'\t' read -r s y; do
        [ -n "$s" ] || continue
        backed_in_index "$s" "$y" "$idx" || emit "NEEDS-REVIEW[CU]" "$frel: in-text '($s $y)' has no matching bibliography entry"
      done < "$WORK/itp"
    fi

    if [ "$nbib" -gt 0 ] && [ -s "$WORK/refs" ]; then
      refs_pairs "$WORK/refs" | while IFS=$'\t' read -r s y; do
        [ -n "$s" ] || continue
        backed_in_index "$s" "$y" "$idx" || emit "NEEDS-REVIEW[RM]" "$frel: reference '$s $y' not found in the .bib"
      done
    fi

    { cat "$WORK/itp"; refs_pairs "$WORK/refs"; } >> "$cited"
  done <<EOF
$(project_deliverables "$dir")
EOF

  if [ "$nbib" -gt 0 ] && [ -s "$idx" ]; then
    sort -u "$cited" > "$WORK/cited.u" 2>/dev/null || : > "$WORK/cited.u"
    if [ ! -s "$WORK/cited.u" ]; then
      # No deliverable cites anything — collapse N per-entry [PE] into one signal.
      local nent; nent="$(grep -c . "$idx" 2>/dev/null || true)"; nent="${nent:-0}"
      emit "NEEDS-REVIEW[STRUCT]" "no in-text citations found in the project's article deliverables — $nent bibliography entries unverified against usage"
    else
      # [PE] is a low-value tidiness signal (an uncited entry is not fabrication). Collapse all
      # uncited entries into ONE advisory summary line rather than one line per entry.
      : > "$WORK/phantom"
      while IFS=$'\t' read -r year key surn; do
        [ -n "$key" ] || continue
        [ "$year" != "-" ] || continue    # can't phantom-check an entry with no year
        local hit=1 cs cy
        while IFS=$'\t' read -r cs cy; do
          [ "$cy" = "$year" ] || continue
          [ -n "$cs" ] || continue
          case " $surn " in *" $cs "*) hit=0; break;; esac
          case "$key" in *"$cs"*) hit=0; break;; esac
        done < "$WORK/cited.u"
        [ "$hit" -eq 0 ] || printf '%s\n' "$key" >> "$WORK/phantom"
      done < "$idx"
      local np egs
      np="$(grep -c . "$WORK/phantom" 2>/dev/null || true)"; np="${np:-0}"
      if [ "$np" -gt 0 ]; then
        egs="$(head -3 "$WORK/phantom" | paste -sd, - | sed 's/,/, /g')"
        emit "NEEDS-REVIEW[PE]" "$np bibliography entries appear uncited in deliverables (e.g. $egs)"
      fi
    fi
  fi
}

main() {
  if [ ! -d "$ROOT_DIR/Projects" ] && [ ! -d "$ROOT_DIR/.projects" ]; then
    echo "No Projects/ or .projects/ under $ROOT_DIR; nothing to check."
    return 0
  fi

  local projects="" resolved p
  if [ -n "$target" ]; then
    resolved="$(resolve_target "$target" || true)"
    if [ -z "$resolved" ]; then echo "ERROR: no research project matches: $target" >&2; return 2; fi
    projects="$resolved"
  else
    projects="$(discover_projects | sort -u)"
  fi
  if [ -z "$projects" ]; then echo "No research projects in scope; nothing to check."; return 0; fi

  echo "Citation & claim integrity check (root: $ROOT_DIR)"
  echo "NOTE: structural checks establish WELL-FORMED, not RESOLVED. This tool cannot prove a"
  echo "      citation or claim is genuine; it surfaces defects and drives residuals to human"
  echo "      review. DEFECT = mechanically certain; NEEDS-REVIEW = advisory (never blocks)."

  local out="$WORK/out"
  : > "$out"
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    audit_project "$p" >> "$out"
  done <<EOF
$projects
EOF
  cat "$out"

  local defects nreview projcount
  defects="$(grep -c 'DEFECT\[' "$out" 2>/dev/null || true)"; defects="${defects:-0}"
  nreview="$(grep -c 'NEEDS-REVIEW\[' "$out" 2>/dev/null || true)"; nreview="${nreview:-0}"
  projcount="$(printf '%s\n' "$projects" | grep -c . || true)"

  echo ""
  echo "---"
  echo "Projects checked: $projcount  |  DEFECT: $defects  |  NEEDS-REVIEW: $nreview"

  if [ "$defects" -gt 0 ]; then
    if [ "$ADVISORY" = "1" ]; then
      echo "ADVISORY mode: DEFECT(s) found but not blocking (exit 0)."
      echo "Remediation: fix duplicate keys / missing title or author-editor / missing source links, then re-run."
      return 0
    fi
    echo "GATE FAILED: resolve DEFECT(s) (duplicate key / missing title or author-editor / missing source link) before compiling."
    return 1
  fi

  if [ "$nreview" -gt 0 ]; then
    echo "PASS (no DEFECT). NEEDS-REVIEW items are advisory — route them to the 2-fold audit"
    echo "protocol (docs/citation-claim-audit-protocol.md); they do not block."
    return 0
  fi

  echo "PASS: no structural citation defects detected. (WELL-FORMED, not RESOLVED — the semantic"
  echo "2-fold audit still applies before release.)"
  return 0
}

main
