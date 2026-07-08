#!/usr/bin/env bash
# Test suite for scripts/check_citation_integrity.sh
#
# Self-contained: builds throwaway RT_ROOT fixtures under a temp dir and asserts the detector's
# exit code + a signature substring per scenario. No network, no repo mutation. Runs under
# bash 3.2 (macOS system bash) and modern bash.
#
#   bash scripts/tests/test_citation_integrity.sh
#
# Exit 0 = all scenarios pass; 1 = at least one failed.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DETECTOR="$(cd "$HERE/.." && pwd)/check_citation_integrity.sh"

if [[ ! -f "$DETECTOR" ]]; then
  echo "FATAL: detector not found at $DETECTOR" >&2
  exit 1
fi

TMP_ROOT="$(mktemp -d 2>/dev/null || mktemp -d -t rt-citint-test)"
trap 'rm -rf "$TMP_ROOT"' EXIT

pass=0
fail=0

mkfile() { mkdir -p "$(dirname "$1")"; cat > "$1"; }   # mkfile <path> <<'EOF' ... EOF

# assert <label> <expected_exit> <expected_substr> <actual_exit> <actual_out>
assert() {
  local label="$1" exp_code="$2" exp_sub="$3" act_code="$4" act_out="$5"
  if [[ "$act_code" == "$exp_code" ]] && printf '%s' "$act_out" | grep -q -- "$exp_sub"; then
    printf '  ok    %s\n' "$label"; pass=$((pass + 1))
  else
    printf '  FAIL  %s\n        expected exit=%s substr=%q\n        got      exit=%s\n%s\n' \
      "$label" "$exp_code" "$exp_sub" "$act_code" "$act_out" >&2
    fail=$((fail + 1))
  fi
}

# assert_absent <label> <forbidden_substr> <actual_out>  (exit-agnostic)
assert_absent() {
  local label="$1" bad="$2" act_out="$3"
  if printf '%s' "$act_out" | grep -q -- "$bad"; then
    printf '  FAIL  %s\n        forbidden substr present: %q\n%s\n' "$label" "$bad" "$act_out" >&2
    fail=$((fail + 1))
  else
    printf '  ok    %s\n' "$label"; pass=$((pass + 1))
  fi
}

run() {  # run <RT_ROOT> [args...] -> sets OUT, CODE
  local root="$1"; shift
  OUT="$(RT_ROOT="$root" bash "$DETECTOR" "$@" 2>&1)"; CODE=$?
}
run_advisory() {
  local root="$1"; shift
  OUT="$(RT_ROOT="$root" CITATION_INTEGRITY_ADVISORY=1 bash "$DETECTOR" "$@" 2>&1)"; CODE=$?
}

echo "Citation-integrity detector — test scenarios"

# 1. PASS: clean bib (with a valid PARENTHESIZED DOI) + a deliverable that cites it.
R="$TMP_ROOT/s1"
mkfile "$R/Projects/Good/references/bibliography.bib" <<'EOF'
@article{Diamond1971,
  author  = {Diamond, Peter A.},
  title   = {A Model of Price Adjustment},
  year    = {1971},
  journal = {Journal of Economic Theory},
  doi     = {10.1016/0022-0531(71)90013-5}
}
EOF
mkfile "$R/Projects/Good/01-analysis.md" <<'EOF'
# Analysis
Search frictions matter (Diamond 1971).

## References
Diamond, Peter A. 1971. "A Model of Price Adjustment." Journal of Economic Theory. https://doi.org/10.1016/0022-0531(71)90013-5
EOF
run "$R" Good
assert        "clean project PASSes"            0 "PASS" "$CODE" "$OUT"
assert_absent "valid paren-DOI not flagged"       "\[DOI\]" "$OUT"
assert_absent "clean project has no DEFECT"       "DEFECT\[" "$OUT"

# 2. DEFECT[DUP] duplicate key -> exit 1
R="$TMP_ROOT/s2"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@article{Foo2020, author = {Foo, A.}, title = {First}, year = {2020}}
@article{Foo2020, author = {Foo, A.}, title = {Dup},   year = {2020}}
EOF
run "$R" P; assert "duplicate key is DEFECT"     1 "DEFECT\[DUP\]" "$CODE" "$OUT"

# 3. DEFECT[META] missing title -> exit 1
R="$TMP_ROOT/s3"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@book{NoTitle2019, author = {Bar, Bob}, year = {2019}}
EOF
run "$R" P; assert "missing title is DEFECT"     1 "missing required field(s): title" "$CODE" "$OUT"

# 4. DEFECT[META] missing author AND editor -> exit 1
R="$TMP_ROOT/s4"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@misc{NoWho2018, title = {Orphan Work}, year = {2018}}
EOF
run "$R" P; assert "missing author/editor is DEFECT" 1 "author/editor" "$CODE" "$OUT"

# 5. editor satisfies the "who" requirement (edited volume) -> no DEFECT
R="$TMP_ROOT/s5"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@book{Fell1998, editor = {Fellbaum, Christiane}, title = {WordNet}, year = {1998}, url = {https://search.worldcat.org/isbn/9780262061971}}
EOF
mkfile "$R/Projects/P/01-x.md" <<'EOF'
# X
As shown (Fellbaum 1998).

## References
Fellbaum, Christiane, ed. 1998. WordNet. https://search.worldcat.org/isbn/9780262061971
EOF
run "$R" P
assert        "editor satisfies who (PASS)"     0 "PASS" "$CODE" "$OUT"
assert_absent "editor: no META defect"            "DEFECT\[META\]" "$OUT"

# 6. missing YEAR is advisory (NEEDS-REVIEW[META]), NOT a DEFECT -> exit 0
R="$TMP_ROOT/s6"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@misc{Repo2021, author = {Doe, Jane}, title = {A Tool}, howpublished = {GitHub}, url = {https://example.org/tool}}
EOF
mkfile "$R/Projects/P/01-x.md" <<'EOF'
# X
We use the tool (Doe 2021).

## References
Doe, Jane. A Tool. GitHub.
EOF
run "$R" P
assert        "missing year is advisory, exit 0" 0 "NEEDS-REVIEW\[META\]" "$CODE" "$OUT"
assert_absent "missing year not a DEFECT"          "DEFECT\[" "$OUT"

# 7. in-text citation with no bib backing -> NEEDS-REVIEW[CU], exit 0
R="$TMP_ROOT/s7"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@article{Real2010, author = {Real, R.}, title = {T}, year = {2010}, doi = {10.1000/real.2010}}
EOF
mkfile "$R/Projects/P/01-x.md" <<'EOF'
# X
A claim with a fabricated cite (Ghost 2099) and a real one (Real 2010).

## References
Real, R. 2010. "T." https://doi.org/10.1000/real.2010
EOF
run "$R" P
assert "in-text miss is advisory CU"             0 "NEEDS-REVIEW\[CU\]" "$CODE" "$OUT"
assert "CU names the offending cite"             0 "ghost 2099" "$CODE" "$OUT"

# 8. @-in-field robustness: a stray '@' inside an author value must NOT break parsing
#    (title/year present -> no false META).
R="$TMP_ROOT/s8"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@article{Team2024,
  author = {{Llama Team, AI @ Meta}},
  title  = {A Big Model},
  year   = {2024},
  url    = {https://example.org/big-model}
}
EOF
mkfile "$R/Projects/P/01-x.md" <<'EOF'
# X
Per the team (Team 2024).

## References
Llama Team. 2024. "A Big Model." https://example.org/big-model
EOF
run "$R" P
assert        "@-in-field parses (PASS)"        0 "PASS" "$CODE" "$OUT"
assert_absent "@-in-field: no false META"         "DEFECT\[META\]" "$OUT"

# 9. Citation-free project (DiacriticReplacement shape) must NOT hard-fail.
R="$TMP_ROOT/s9"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@article{A2001, author = {A, A.}, title = {One}, year = {2001}, url = {https://example.org/a}}
@article{B2002, author = {B, B.}, title = {Two}, year = {2002}, doi = {10.1000/b.2002}}
EOF
mkfile "$R/Projects/P/02-claims-inventory.md" <<'EOF'
# Claims Inventory
This deliverable enumerates assertions but contains no author-date citations by design.
EOF
run "$R" P
assert "citation-free project is exit 0"         0 "unverified against usage" "$CODE" "$OUT"
assert "citation-free project PASSes"            0 "PASS" "$CODE" "$OUT"

# 10. Advisory downgrade: a DEFECT under CITATION_INTEGRITY_ADVISORY=1 -> exit 0
R="$TMP_ROOT/s10"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@book{NoTitle2019, author = {Bar, Bob}, year = {2019}}
EOF
run_advisory "$R" P
assert "advisory downgrade exits 0"              0 "ADVISORY" "$CODE" "$OUT"

# 11. Recursive discovery of a NESTED project (Projects/Category/Proj).
R="$TMP_ROOT/s11"
mkfile "$R/Projects/Category/Proj/references/bibliography.bib" <<'EOF'
@article{X2000, author = {X, X.}, title = {T}, year = {2000}, url = {https://example.org/x}}
EOF
mkfile "$R/Projects/Category/Proj/01-x.md" <<'EOF'
# X
See (X 2000).

## References
X, X. 2000. "T." https://example.org/x
EOF
run "$R"
assert "nested project discovered"               0 "Category/Proj" "$CODE" "$OUT"
assert "nested: exactly one project"             0 "Projects checked: 1" "$CODE" "$OUT"

# 12. Backup/asset trees are pruned from discovery.
R="$TMP_ROOT/s12"
mkfile "$R/Projects/Real/references/bibliography.bib" <<'EOF'
@article{X2000, author = {X, X.}, title = {T}, year = {2000}, url = {https://example.org/x}}
EOF
mkfile "$R/Projects/Real/01-x.md" <<'EOF'
# X
See (X 2000).
## References
X, X. 2000. "T." https://example.org/x
EOF
# a would-be "project" inside a backup tree that MUST be excluded
mkfile "$R/Projects/.agentteams-backups/Shadow/references/bibliography.bib" <<'EOF'
@article{Dup2000, author = {X, X.}, title = {T}, year = {2000}}
@article{Dup2000, author = {X, X.}, title = {T2}, year = {2000}}
EOF
run "$R"
assert        "backup tree excluded (1 project)" 0 "Projects checked: 1" "$CODE" "$OUT"
assert_absent "backup DEFECT not surfaced"         "Shadow" "$OUT"

# 13. Hidden .projects/ is discovered by default.
R="$TMP_ROOT/s13"
mkfile "$R/.projects/Hidden/references/bibliography.bib" <<'EOF'
@article{X2000, author = {X, X.}, title = {T}, year = {2000}, url = {https://example.org/x}}
EOF
mkfile "$R/.projects/Hidden/01-x.md" <<'EOF'
# X
See (X 2000).
## References
X, X. 2000. "T." https://example.org/x
EOF
run "$R"
assert ".projects/ discovered"                   0 ".projects/Hidden" "$CODE" "$OUT"

# 14. Nonexistent named target -> exit 2
R="$TMP_ROOT/s14"; mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@article{X2000, author = {X, X.}, title = {T}, year = {2000}, url = {https://example.org/x}}
EOF
run "$R" does-not-exist; assert "nonexistent target exit 2" 2 "no research project matches" "$CODE" "$OUT"

# 15. Empty root (no Projects/ or .projects/) -> exit 0
R="$TMP_ROOT/s15"; mkdir -p "$R"
run "$R"; assert "empty root exit 0"             0 "nothing to check" "$CODE" "$OUT"

# 15b. DEFECT[LINK]: an entry with no url and no doi (isbn only is NOT a link) -> exit 1
R="$TMP_ROOT/s15b"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@book{NoLink2000, author = {A, A.}, title = {A Book}, year = {2000}, isbn = {9780000000000}}
EOF
run "$R" P
assert "no source link is DEFECT[LINK]"          1 "DEFECT\[LINK\]" "$CODE" "$OUT"
assert "LINK message guides remediation"         1 "no source link" "$CODE" "$OUT"

# 15c. A url OR a doi satisfies the link requirement (no LINK defect)
R="$TMP_ROOT/s15c"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@book{HasUrl2001, author = {B, B.}, title = {T}, year = {2001}, url = {https://search.worldcat.org/isbn/9780000000001}}
@article{HasDoi2002, author = {C, C.}, title = {T}, year = {2002}, doi = {10.1000/x}}
EOF
mkfile "$R/Projects/P/01-x.md" <<'EOF'
# X
See (B 2001) and (C 2002).
## References
B, B. 2001. "T." https://search.worldcat.org/isbn/9780000000001
C, C. 2002. "T." https://doi.org/10.1000/x
EOF
run "$R" P
assert        "url/doi entries PASS"             0 "PASS" "$CODE" "$OUT"
assert_absent "url/doi entries not flagged LINK"   "DEFECT\[LINK\]" "$OUT"

# 15d. Advisory mode downgrades a LINK defect to exit 0
R="$TMP_ROOT/s15d"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@book{NoLink2000, author = {A, A.}, title = {A Book}, year = {2000}, isbn = {9780000000000}}
EOF
run_advisory "$R" P
assert "LINK advisory downgrade exits 0"         0 "ADVISORY" "$CODE" "$OUT"

# 15e. DEFECT[REFURL]: a reference-list entry that embeds no URL -> exit 1
R="$TMP_ROOT/s15e"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@article{Link2010, author = {Link, L.}, title = {T}, year = {2010}, url = {https://example.org/link}}
EOF
mkfile "$R/Projects/P/01-x.md" <<'EOF'
# X
As shown (Link 2010).

## References
Link, L. 2010. "T." Journal of Things.
EOF
run "$R" P
assert "reference-list entry w/o URL is DEFECT[REFURL]" 1 "DEFECT\[REFURL\]" "$CODE" "$OUT"

# 15f. A reference-list entry that embeds the URL is clean (no REFURL)
R="$TMP_ROOT/s15f"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@article{Link2010, author = {Link, L.}, title = {T}, year = {2010}, url = {https://example.org/link}}
EOF
mkfile "$R/Projects/P/01-x.md" <<'EOF'
# X
As shown (Link 2010).

## References
Link, L. 2010. "T." Journal of Things. https://example.org/link
EOF
run "$R" P
assert        "reference-list entry w/ URL passes"   0 "PASS" "$CODE" "$OUT"
assert_absent "no REFURL when URL embedded"            "DEFECT\[REFURL\]" "$OUT"

# 15g. "Works cited (trailing text)" heading is detected; bulleted entries are checked; a
#      non-author bullet (**Primary texts:**) is excluded.
R="$TMP_ROOT/s15g"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@book{Author2000, author = {Author, An}, title = {A Book}, year = {2000}, url = {https://example.org/book}}
EOF
mkfile "$R/Projects/P/01-x.md" <<'EOF'
# X
As shown (Author 2000).

## Works cited (Chicago author-date)
- Author, An. 2000. *A Book.* City: Press.
- **Primary texts:** Acts 6:1-6; 1 Clement 42-44.
EOF
run "$R" P
assert        "Works-cited heading + bullet -> REFURL"   1 "DEFECT\[REFURL\]" "$CODE" "$OUT"
assert_absent "non-author bullet excluded"                "Primary texts" "$OUT"
assert_absent "Works-cited detected (no no-refs STRUCT)"  "no '## References' section" "$OUT"

# 15h. Advisory mode downgrades a REFURL defect to exit 0
R="$TMP_ROOT/s15h"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@article{Link2010, author = {Link, L.}, title = {T}, year = {2010}, url = {https://example.org/link}}
EOF
mkfile "$R/Projects/P/01-x.md" <<'EOF'
# X
As shown (Link 2010).

## References
Link, L. 2010. "T." Journal of Things.
EOF
run_advisory "$R" P
assert "REFURL advisory downgrade exits 0"       0 "ADVISORY" "$CODE" "$OUT"

# 16. Ceiling banner is always printed (WELL-FORMED != RESOLVED honesty).
run "$TMP_ROOT/s1" Good
assert "ceiling banner present"                  0 "WELL-FORMED, not RESOLVED" "$CODE" "$OUT"

# 17. Determinism guard: two runs on the same fixture produce byte-identical output.
O1="$(RT_ROOT="$TMP_ROOT/s1" bash "$DETECTOR" 2>&1)"
O2="$(RT_ROOT="$TMP_ROOT/s1" bash "$DETECTOR" 2>&1)"
if [[ "$O1" == "$O2" ]]; then
  printf '  ok    %s\n' "determinism guard (identical output twice)"; pass=$((pass + 1))
else
  printf '  FAIL  %s\n' "determinism guard (output differed between runs)" >&2; fail=$((fail + 1))
fi

echo "---"
echo "Passed: $pass  Failed: $fail"
[[ "$fail" -eq 0 ]]
