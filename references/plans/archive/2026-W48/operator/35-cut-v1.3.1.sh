#!/usr/bin/env bash
# 35 — Fast-forward release/1.3 to the reviewed head of the v1.3.1 backport and sign researchteam v1.3.1 there with
# the release key. A patch of the 1.3 line whose only new content is the pin to agentteams v1.3.3.
# Plan: references/plans/release-1.3.1.plan.md (D3 to D5). Written from 30-cut-v1.3.0.sh. Different here:
#   - the commit to tag is the head of the backport pull request into release/1.3, not a merge commit on main;
#   - between v1.3.0 and that commit lie exactly three commits: a cherry-pick of the pin files, one regeneration
#     commit made on the line (operator ruling R5, 2026-11-28), and a cherry-pick of the release files;
#   - there is no candidate (operator ruling R2);
#   - the line's trust state is unchanged from v1.3.0 (operator ruling R1);
#   - no decision row is required as a line of text (H3 step 16): each row the cut rests on must CLEAR.
# Running this script is the operator's go for v1.3.1 (the go/no-go stays with the operator).
# OPERATOR ONLY, plain Terminal, from any directory:
#   /bin/bash <checkout>/tmp/by-week/2026-W48/operator/35-cut-v1.3.1.sh <40-hex reviewed backport head>
# (the runnable copy lives under the ignored tmp/; this tracked copy is the record and holds placeholders. It does
# not run: run_log refuses a folder that git does not ignore, and the placeholder checks would stop it next)
# The session hands over one command that first checks this copy's sha256 and that the shell is not an agent's or
# an editor's. Every run writes its own log under logs/ beside this file.
# Until the question "Move release/1.3 ..." nothing is pushed or signed.
source "$(dirname "$0")/common.sh"
refuse_agent
run_log 35-cut
TAG="v1.3.1"; AT_TAG="v1.3.3"; LINE="release/1.3"
SHA="${1:?usage: $0 <40-hex reviewed backport head>}"
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || die "the commit must be a full 40-hex SHA"

# Filled in the runnable copy once the backport exists and @security has reviewed it (plan steps 13 to 16).
BP_PR="<backport pull request number>"
PICK_PIN="<main commit of the pin files>"            # 40 hex; on origin/main
REGEN="<regeneration commit on the line>"            # 40 hex; reproduced by @security
REGEN_MAIN="<main commit of the regeneration>"       # 40 hex; on origin/main; named in the line commit's message
PICK_REL="<main commit of the release files>"        # 40 hex; on origin/main
SIGNER_VERSION="<agentteams version of the root-owned install>"   # X.Y.Z; the script refuses another
AGENTTEAMS_BIN="<signer>"                            # root-owned install built from a signed agentteams tag
# Rows the cut rests on. Each must clear at the commit (signature, lineage, no later HALT or retraction).
# Settled in plan step 5 on the line's tree and checked again at the backport head in step 14.
ROWS=(release-line-agentteams-1.3)
[[ "$BP_PR" =~ ^[1-9][0-9]*$ ]] || die "BP_PR is not a pull-request number (this is the tracked copy, or the copy is not filled in)"
for v in "$PICK_PIN" "$REGEN" "$REGEN_MAIN" "$PICK_REL"; do [[ "$v" =~ ^[0-9a-f]{40}$ ]] || die "a commit placeholder is not filled in"; done
[[ "$SIGNER_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "SIGNER_VERSION is not X.Y.Z"

fp="$(/usr/bin/ssh-keygen -lf "$RELEASE_PUB" | awk '{print $2}')" || die "cannot read the release key file"
[ "$fp" = "$RELEASE_FP" ] || die "$RELEASE_PUB is $fp, not the release key $RELEASE_FP"
RT_URL="https://github.com/$REPO"
cd "$MAIN"
# Identity for the tag. The email is fixed here, not read from the checkout: it is the account's GitHub no-reply
# address, which GitHub always treats as verified (release policy). Every git call below runs neutralised.
GH_LOGIN="jlcatonjr"
EMAIL="12754578+jlcatonjr@users.noreply.github.com"
NAME="$(git config user.name)"
[ -n "$NAME" ] || die "set git user.name in $MAIN first"
[ "$(gh api "users/$GH_LOGIN" -q .id)" = "${EMAIL%%+*}" ] || die "the no-reply address does not carry the account id of $GH_LOGIN"
# GitHub shows a tag as verified only if the signing key is registered on the tagger's account as a SIGNING key.
SIGNING_KEYS="$(gh api "users/$GH_LOGIN/ssh_signing_keys" -q '.[].key')" || die "cannot list the signing keys of $GH_LOGIN"
registered=0
while IFS= read -r key; do
  if [ -n "$key" ] && [ "$(printf '%s\n' "$key" | /usr/bin/ssh-keygen -lf - | awk '{print $2}')" = "$RELEASE_FP" ]; then registered=1; fi
done <<EOF_KEYS
$SIGNING_KEYS
EOF_KEYS
[ "$registered" = 1 ] || die "the release key $RELEASE_FP is not a signing key on $GH_LOGIN"

# The root-owned install, and its version.
[[ -x "$AGENTTEAMS_BIN" && "$(/usr/bin/stat -f %Su "$AGENTTEAMS_BIN")" == root ]] || die "no root-owned agentteams at $AGENTTEAMS_BIN"
SIGNER_PY="${AGENTTEAMS_BIN%/agentteams}/python"
[[ -x "$SIGNER_PY" ]] || die "no python beside the root-owned agentteams"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir "$TMP/empty"
got_version="$(cd "$TMP/empty" && "$SIGNER_PY" -I -P -c 'from importlib.metadata import version; print(version("agentteams"))')" || die "cannot read the root-owned install's version"
[ "$got_version" = "$SIGNER_VERSION" ] || die "the root-owned install is agentteams $got_version, not the expected $SIGNER_VERSION"

ngit fetch --quiet --tags "$RT_URL" "+refs/heads/main:refs/remotes/origin/main" || die "cannot fetch main and the tags"

# The previous release: signed, exactly the tag object recorded at its cut, and the base of the backport.
PREV="v1.3.0"; PREV_OBJ="68d0dcd826ce7a8da5aa7a44ee217bfb07299cf3"   # read from the remote on 2026-11-28
BASE="570724f5792412c2427763b4c6b102e33a9493e9"                       # the v1.3.0 commit; release/1.3 before this cut
[ "$(ngit rev-parse "refs/tags/$PREV")" = "$PREV_OBJ" ] || die "local $PREV is not tag object $PREV_OBJ"
[ "$(ngit ls-remote "$RT_URL" "refs/tags/$PREV" | cut -f1)" = "$PREV_OBJ" ] || die "remote $PREV is not tag object $PREV_OBJ"
verify_tag "$MAIN" "$PREV"
[ "$(ngit rev-parse "refs/tags/$PREV^{commit}")" = "$BASE" ] || die "$PREV does not peel to $BASE"
existing="$(ngit ls-remote "$RT_URL" "refs/heads/$LINE" | cut -f1)" || die "cannot read $LINE on the remote; nothing was pushed or signed"
[ "$existing" = "$BASE" ] || [ "$existing" = "$SHA" ] || die "$LINE is at ${existing:-nothing}, neither $PREV (${BASE:0:12}) nor $SHA"

# The backport pull request: in this repository, into the line, at exactly the reviewed head. It is OPEN before the
# push. After an earlier run's push GitHub may show it MERGED; that is accepted only if the line is already at $SHA.
pr="$(gh pr view "$BP_PR" -R "$REPO" --json state,headRefOid,baseRefName,isCrossRepository,isDraft \
      -q '"\(.state) \(.headRefOid) \(.baseRefName) \(.isCrossRepository) \(.isDraft)"')" || die "cannot read PR #$BP_PR"
case "$pr" in
  "OPEN $SHA $LINE false false") ;;
  "MERGED $SHA $LINE false false") [ "$existing" = "$SHA" ] || die "PR #$BP_PR reads MERGED but $LINE is not at $SHA" ;;
  *) die "PR #$BP_PR is '$pr'; expected an open, non-draft pull request of this repository into $LINE at $SHA" ;;
esac
ngit fetch --quiet --no-tags "$RT_URL" "+refs/pull/$BP_PR/head:refs/remotes/origin/pr-$BP_PR-head" || die "cannot fetch the head of PR #$BP_PR"
[ "$(ngit rev-parse "refs/remotes/origin/pr-$BP_PR-head")" = "$SHA" ] || die "the fetched head of PR #$BP_PR is not $SHA"
# Both test checks must have run and passed on exactly this commit (no checks at all is not green).
for check in "tests (3.10)" "tests (3.13)"; do
  got="$(gh api "repos/$REPO/commits/$SHA/check-runs" --paginate -q ".check_runs[] | select(.name == \"$check\" and .app.slug == \"github-actions\") | .conclusion" | sort -u | tr '\n' ' ')"
  [ "$got" = "success " ] || die "check '$check' on $SHA is '${got:-absent}', not success"
done

# What lies between v1.3.0 and the commit: exactly three commits, none a merge, in this order.
ngit merge-base --is-ancestor "$BASE" "$SHA" || die "$SHA does not contain $PREV (${BASE:0:12})"
COMMITS=()
while IFS= read -r c; do COMMITS+=("$c"); done < <(ngit rev-list --reverse "$BASE..$SHA")
[ "${#COMMITS[@]}" = 3 ] || die "expected exactly 3 commits between $PREV and $SHA, found ${#COMMITS[@]}"
for c in "${COMMITS[@]}"; do
  [ "$(ngit rev-list --parents -n 1 "$c" | wc -w | tr -d ' ')" = 2 ] || die "$c is a merge or a root commit"
done
C_PIN="${COMMITS[0]}"; C_REGEN="${COMMITS[1]}"; C_REL="${COMMITS[2]}"
patch_id() { ngit diff-tree --no-renames -p "$@" | ngit patch-id --stable | cut -d' ' -f1; }
# patch-id ignores whitespace inside a line, so the patches are also compared as text: every changed and context
# line must be equal. Only the blob ids and the hunk headers (line numbers, which differ between main and the
# line) are left out.
exact() { ngit diff-tree --no-renames --no-commit-id -p "$@" | grep -v '^index ' | sed -E 's/^@@ .*/@@/'; }
for src in "$PICK_PIN" "$REGEN_MAIN" "$PICK_REL"; do
  ngit merge-base --is-ancestor "$src" refs/remotes/origin/main || die "$src is not on origin/main"
  [ "$(ngit rev-list --parents -n 1 "$src" | wc -w | tr -d ' ')" = 2 ] || die "$src is a merge commit; the pick must name the branch's own commit"
done
# 1. The pin files: the same patch as the main commit the plan names (not only the commit's own text).
[ -n "$(patch_id "$PICK_PIN")" ] && [ "$(patch_id "$C_PIN")" = "$(patch_id "$PICK_PIN")" ] || die "${C_PIN:0:12} is not the same patch as the main commit ${PICK_PIN:0:12}"
[ -n "$(exact "$PICK_PIN")" ] && [ "$(exact "$C_PIN")" = "$(exact "$PICK_PIN")" ] || die "${C_PIN:0:12} is not line for line the patch of the main commit ${PICK_PIN:0:12}"
ngit log -1 --format=%B "$C_PIN" | grep -xF "(cherry picked from commit $PICK_PIN)" >/dev/null || die "${C_PIN:0:12} does not record its source $PICK_PIN"
# 2. The regeneration commit: the one @security reproduced, generated output only, and its message names the
# main commit it corresponds to (release policy).
[ "$C_REGEN" = "$REGEN" ] || die "the second commit is ${C_REGEN:0:12}, not the reviewed regeneration ${REGEN:0:12}"
ngit log -1 --format=%B "$C_REGEN" | grep -F "$REGEN_MAIN" >/dev/null || die "the regeneration commit's message does not name the main commit $REGEN_MAIN"
REGEN_PATHS="$(ngit diff-tree --no-renames --no-commit-id --name-only -r "$C_REGEN")" || die "cannot list the regeneration commit's paths"
[ -n "$REGEN_PATHS" ] || die "the regeneration commit changes nothing"
# An allow-list of the generated surfaces first. Hook, settings and sandbox files are not on it; if the reviewed
# regeneration writes one, it is added by name in the runnable copy after @security's second review.
OUTSIDE="$(printf '%s\n' "$REGEN_PATHS" | grep -vE '^(\.github/agents/|\.claude/agents/|\.codex/agents/|\.goose/recipes/|\.claude/(agent-team|README|quickstart-snippet|CLAUDE)\.md$|AGENTS\.md$|\.github/copilot-instructions\.md$)' || true)"
[ -z "$OUTSIDE" ] || die "the regeneration commit touches paths outside the generated surfaces: $(printf '%s' "$OUTSIDE" | tr '\n' ' ')"
# Then a deny-list, which also catches a trust root that sits inside a generated surface.
NOT_GENERATED="$(printf '%s\n' "$REGEN_PATHS" | grep -E '^(toolchain\.lock|pyproject\.toml|brief\.json|CHANGELOG\.md|\.agentteams/|\.github/workflows/|\.github/ci/|\.github/agentteams-autosync-ref$|scripts/|researchteam/|tests/|docs/|docs_src/|Projects/|references/)|/authorized-verify-keys/|\.log\.csv$|allowed_signers|roster|/exception-registry\.json$' || true)"
[ -z "$NOT_GENERATED" ] || die "the regeneration commit touches paths that are not generated output: $(printf '%s' "$NOT_GENERATED" | tr '\n' ' ')"
# 3. The release files: the same patch as the main commit, except CHANGELOG.md, which was resolved by the plan's
# fixed rule: the line's own file plus the 1.3.1 entry of the main commit, and nothing else.
[ -n "$(patch_id "$PICK_REL" -- . ':(exclude)CHANGELOG.md')" ] && [ "$(patch_id "$C_REL" -- . ':(exclude)CHANGELOG.md')" = "$(patch_id "$PICK_REL" -- . ':(exclude)CHANGELOG.md')" ] || die "${C_REL:0:12} differs from the main commit ${PICK_REL:0:12} outside CHANGELOG.md"
[ -n "$(exact "$PICK_REL" -- . ':(exclude)CHANGELOG.md')" ] && [ "$(exact "$C_REL" -- . ':(exclude)CHANGELOG.md')" = "$(exact "$PICK_REL" -- . ':(exclude)CHANGELOG.md')" ] || die "${C_REL:0:12} is not line for line the patch of the main commit ${PICK_REL:0:12} outside CHANGELOG.md"
ngit log -1 --format=%B "$C_REL" | grep -xF "(cherry picked from commit $PICK_REL)" >/dev/null || die "${C_REL:0:12} does not record its source $PICK_REL"
HEADING='## 1.3.1 (tag `v1.3.1`, on `release/1.3`)'
{ ngit show "$BASE:CHANGELOG.md" > "$TMP/cl.base" && ngit show "$SHA:CHANGELOG.md" > "$TMP/cl.now" && ngit show "$PICK_REL:CHANGELOG.md" > "$TMP/cl.main"; } || die "cannot read CHANGELOG.md at the three commits"
( cd "$TMP/empty" && "$SIGNER_PY" -I -P - "$TMP/cl.base" "$TMP/cl.now" "$TMP/cl.main" "$HEADING" ) <<'PY' || die "CHANGELOG.md at $SHA is not the line's file plus the 1.3.1 entry of the main commit; nothing was pushed or signed"
import sys
base, now, main = (open(p, encoding="utf-8").read().split("\n") for p in sys.argv[1:4])
heading = sys.argv[4]
def section(lines):
    if lines.count(heading) != 1:
        return None
    i = lines.index(heading)
    j = next((k for k in range(i + 1, len(lines)) if lines[k].startswith("## ")), len(lines))
    return i, j
a, b = section(now), section(main)
if a is None or b is None or heading in base:
    print("  the 1.3.1 heading is missing, repeated, or already in the previous release"); sys.exit(1)
if now[a[0]:a[1]] != main[b[0]:b[1]]:
    print("  the 1.3.1 entry differs from the main commit's"); sys.exit(1)
if now[:a[0]] + now[a[1]:] != base:
    print("  CHANGELOG.md differs from the previous release outside the 1.3.1 entry"); sys.exit(1)
print(f"  CHANGELOG.md: the previous release's file plus the 1.3.1 entry ({a[1] - a[0]} lines)")
PY

# The line's trust state is unchanged from v1.3.0 (R1): key stores, every governance log (decisions, waivers),
# allowed-signers files, registries, rosters and the group file.
SINCE_PREV="$(ngit diff --no-renames --name-only "$BASE" "$SHA")" || die "cannot list the changes since $PREV"
[ -n "$SINCE_PREV" ] || die "$SHA changes nothing since $PREV"
TRUST_DIFF="$(printf '%s\n' "$SINCE_PREV" | grep -E '\.log\.csv$|/authorized-verify-keys/|allowed_signers|/exception-registry\.json$|roster|^\.agentteams/' || true)"
[ -z "$TRUST_DIFF" ] || die "the trust state differs from $PREV: $(printf '%s' "$TRUST_DIFF" | tr '\n' ' ')"

# The agentteams pin at the commit: the stable AT_TAG, verified HERE (signature, remote object), in the lock, in
# both extras and in the autosync ref.
ngit init -q "$TMP/at"
ngit -C "$TMP/at" fetch -q --no-tags "$AT_REPO_URL" "refs/tags/$AT_TAG:refs/tags/$AT_TAG" || die "agentteams $AT_TAG is not tagged"
verify_tag "$TMP/at" "$AT_TAG"
AT_OBJ="$(ngit -C "$TMP/at" rev-parse "refs/tags/$AT_TAG")"
AT_PEELED="$(ngit -C "$TMP/at" rev-parse "refs/tags/$AT_TAG^{commit}")"
[ "$(ngit ls-remote "$AT_REPO_URL" "refs/tags/$AT_TAG" | cut -f1)" = "$AT_OBJ" ] || die "remote $AT_TAG object differs from the verified one"
ngit show "$SHA:toolchain.lock" | grep -x "agentteams=jlcatonjr/agentteams@$AT_PEELED" >/dev/null || die "lock at $SHA is not pinned to $AT_TAG ($AT_PEELED)"
ngit show "$SHA:toolchain.lock" | grep -x "agentteams.tag=$AT_TAG" >/dev/null || die "lock at $SHA is not release-locked at $AT_TAG"
[ "$(ngit show "$SHA:pyproject.toml" | grep -c "jlcatonjr/agentteams@$AT_PEELED")" = 2 ] || die "the update/research extras at $SHA do not both pin $AT_PEELED"
[ "$(ngit show "$SHA:.github/agentteams-autosync-ref")" = "$AT_PEELED" ] || die "the autosync ref at $SHA is not $AT_PEELED"
ngit cat-file -e "$SHA:.agentteams/toolchain-group.json" || die "no .agentteams/toolchain-group.json at $SHA"
NOTES="$(ngit show "$SHA:docs/release/release-notes-v1.3.1.md")" || die "no docs/release/release-notes-v1.3.1.md at $SHA"
for f in CLAUDE.md researchteam/scaffold/CLAUDE.template.md; do
  ngit show "$SHA:$f" | grep -xF '# a release instead of main: append the signed tag, e.g. ...researchteam.git@v1.3.1' >/dev/null \
    || die "$f at $SHA does not carry the install example naming v1.3.1"
done

# The group file must VERIFY at the commit (signature, workspace binding, no HALT on s10-toolchain-group), not
# merely exist. Run from the root-owned install, in a detached worktree of the commit so the workspace binding
# sees origin.
ngit worktree add -q --detach "$TMP/rt" "$SHA" || die "cannot check out $SHA for the checks"
trap 'ngit worktree remove --force "$TMP/rt" 2>/dev/null; rm -rf "$TMP"' EXIT
( cd "$TMP/rt" && "$AGENTTEAMS_BIN" --verify-toolchain-pin toolchain.lock --allowed-signers "$ALLOWED_SIGNERS" \
    --output .github/agents --description brief.json ) || die "the toolchain-group pin does not verify at $SHA (must exit 0)"
# Each row the cut rests on must CLEAR at the commit, not merely be present as text (C-2; H3 step 16). A
# non-consuming gate check, from an empty directory. No row is required as a line of text.
for a in "${ROWS[@]}"; do
  ( cd "$TMP/empty" && "$SIGNER_PY" -I -P - "$TMP/rt/.github/agents" "$a" ) <<'PY' || die "$a does not clear at $SHA; nothing was pushed or signed"
import sys
from pathlib import Path
from agentteams.cli.security_gate import check_clearance
ok, why = check_clearance(Path(sys.argv[1]), action=sys.argv[2], consume=False) if "consume" in check_clearance.__code__.co_varnames else check_clearance(Path(sys.argv[1]), action=sys.argv[2])
print(f"  {sys.argv[2]}: {'clears' if ok else 'REFUSED: ' + str(why)[:200]}")
sys.exit(0 if ok else 1)
PY
done
# The decisions log of every surface at the commit: no unretracted HALT anywhere (a HALT in any surface's log
# binds, C-2). The logs equal the previous release's, checked above, so no row was added and no new pending
# condition can exist.
SURFACES=0
for surface in .github/agents .claude/agents .codex/agents .goose/recipes; do
  ngit cat-file -e "$SHA:$surface/references/security-decisions.log.csv" 2>/dev/null || continue
  SURFACES=$((SURFACES + 1))
  ngit show "$SHA:$surface/references/security-decisions.log.csv" > "$TMP/log.now.csv" || die "cannot read the decisions log of $surface at $SHA"
  ( cd "$TMP/empty" && "$SIGNER_PY" -I -P - "$TMP/log.now.csv" "$surface" ) <<'PY' || die "the decisions log of $surface at $SHA has an unretracted HALT; nothing was pushed or signed"
import csv, sys
with open(sys.argv[1], newline="", encoding="utf-8") as f:
    now = list(csv.DictReader(f))
bad = 0
for i, r in enumerate(now):
    verdict, action = (r.get("verdict") or "").strip().upper(), (r.get("action_reviewed") or "").strip()
    if verdict == "HALT":
        retracted = any((n.get("verdict") or "").strip().upper() == "HALT-RETRACTED"
                        and (n.get("action_reviewed") or "").strip() == action for n in now[i + 1:])
        if not retracted:
            print(f"  HALT stands: {action}"); bad += 1
print(f"  decisions log of {sys.argv[2]}: {len(now)} rows; {bad} blocking")
sys.exit(1 if bad else 0)
PY
done
ngit cat-file -e "$SHA:.github/agents/references/security-decisions.log.csv" || die "no decisions log under .github/agents at $SHA"
[ "$SURFACES" -ge 1 ] || die "no decisions log was scanned"
# The copied term-index core at the commit: it matches its manifest, every file equals the signed agentteams tag
# the manifest names, and its commit is the commit the lock pins. The comparing code is the checkout's own package,
# run from an empty directory with the root-owned python (-I: no current directory, no user site).
( cd "$TMP/empty" && AGENTTEAMS_ALLOWED_SIGNERS="$ALLOWED_SIGNERS" "$SIGNER_PY" -I -B -c 'import sys, runpy
sys.path.insert(0, sys.argv[1]); sys.argv = ["researchteam._term_core_upstream", "--root", sys.argv[1]]
runpy.run_module("researchteam._term_core_upstream", run_name="__main__")' "$TMP/rt" ) || die "the copied term-index core does not equal the signed agentteams tag at $SHA; nothing was pushed or signed"
ngit show "$SHA:scripts/term-index-core/PINNED.json" | grep -F "\"commit\": \"$AT_PEELED\"" >/dev/null || die "the core manifest at $SHA does not name the lock's commit $AT_PEELED"

ngit rev-parse -q --verify "refs/tags/$TAG" >/dev/null && die "$TAG already exists; tags are immutable. If an earlier run signed it here but did not push it, stop and tell the researchteam session; do not delete it yourself"
# Captured first, so a failed listing stops the run instead of reading as "no such tag".
remote_tag="$(ngit ls-remote "$RT_URL" "refs/tags/$TAG")" || die "cannot list the remote's tags; nothing was pushed or signed"
[ -z "$remote_tag" ] || die "$TAG already exists on the remote; tags are immutable"

say "$LINE and $TAG at $SHA (pins agentteams $AT_TAG ${AT_PEELED:0:12})"
ngit log --format='  %h %s' "$BASE..$SHA"
echo "  Paths that differ from $PREV (${BASE:0:12}):"; printf '%s\n' "$SINCE_PREV" | sed 's/^/    /'
confirm "Move $LINE forward to ${SHA:0:12} and sign $TAG there? (This is the go for v1.3.1.)"
# Pushes use your credentials (so plain git, but no hooks and an explicit URL); everything else stays neutralised.
# Forward only: the lease names the v1.3.0 commit, so the branch moves only if it is still exactly there, and the
# commit contains it (checked above), so the move is a fast-forward. GitHub may then show the backport pull
# request as merged and may delete its head branch.
[ "$existing" = "$SHA" ] || git -c core.hooksPath=/dev/null push --quiet --force-with-lease="refs/heads/$LINE:$BASE" "$RT_URL" "$SHA:refs/heads/$LINE"
[ "$(ngit ls-remote "$RT_URL" "refs/heads/$LINE" | cut -f1)" = "$SHA" ] || die "remote $LINE is not at $SHA after the push; nothing was signed"
ngit -c user.name="$NAME" -c user.email="$EMAIL" -c gpg.format=ssh -c gpg.ssh.program=/usr/bin/ssh-keygen \
  -c user.signingkey="$RELEASE_PUB" tag -s "$TAG" "$SHA" -m "researchteam 1.3.1 — a patch of the 1.3 line (release/1.3): agentteams 1.3.3

Pins agentteams $AT_TAG ($AT_PEELED). See CHANGELOG.md and docs/release-policy.md."
verify_tag "$MAIN" "$TAG"
[ "$(ngit describe --tags --match 'v[0-9]*' --exact-match "$SHA")" = "$TAG" ] || die "git describe does not name $TAG at $SHA"
OBJ="$(ngit rev-parse "refs/tags/$TAG")"; PEELED="$(ngit rev-parse "refs/tags/$TAG^{commit}")"
[ "$PEELED" = "$SHA" ] || die "peeled $PEELED != $SHA"
confirm "Push $TAG (object ${OBJ:0:12}) to origin?"
git -c core.hooksPath=/dev/null push --quiet "$RT_URL" "refs/tags/$TAG"
[ "$(ngit ls-remote "$RT_URL" "refs/tags/$TAG" | cut -f1)" = "$OBJ" ] || die "remote tag object differs"
if ! gh release view "$TAG" -R "$REPO" >/dev/null 2>&1; then
  drain; read -r -p "Create the GitHub release for $TAG (marked Latest)? [y/N] " answer
  if [ "$answer" = y ]; then
    gh release create "$TAG" -R "$REPO" --verify-tag --latest --title "researchteam 1.3.1" --notes "$NOTES" \
      || echo "  WARNING: the GitHub release was not created; the tag is signed and pushed. Tell the researchteam session."
  fi
fi
# Report only: the tag is public and immutable, so nothing here can stop or undo the release.
VERIFIED="unknown"
for _ in 1 2 3 4 5 6; do
  VERIFIED="$(gh api "repos/$REPO/git/tags/$OBJ" -q '"\(.verification.verified) (\(.verification.reason))"' 2>/dev/null || echo unknown)"
  case "$VERIFIED" in true*) break ;; esac
  sleep 10
done
say "Signed and pushed $TAG"
echo "  tag object : $OBJ"
echo "  peeled     : $PEELED"
echo "  $LINE: $(ngit ls-remote "$RT_URL" "refs/heads/$LINE" | cut -f1)"
echo "  GitHub verification : $VERIFIED"
echo "  run log    : $RUN_LOG"
echo "Tell the researchteam session. It then opens the pull request that merges $LINE forward into main."
echo "Leave the autosync paused until that pull request has merged."
