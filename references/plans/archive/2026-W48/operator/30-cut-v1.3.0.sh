#!/usr/bin/env bash
# 30 — Fast-forward release/1.3 to a reviewed main commit (1.3.0) and sign researchteam v1.3.0 with the release key.
# The final of the 1.3 line. Copied from 29-cut-v1.3.0-rc.1.sh; every check of that script is kept. Different here:
# the base is the signed candidate v1.3.0-rc.1 (its recorded tag object, verified, and an ancestor); the commit
# differs from the candidate only in release files, records and the install instructions (a fixed list of files,
# with CLAUDE.md and its scaffold template limited to one changed line each); release/1.3 must already exist at the
# candidate's commit and is moved forward only, under a lease on that commit; the GitHub release is marked Latest.
# Running this script is the operator's go for v1.3.0 (the go/no-go stays with the operator).
# OPERATOR ONLY, plain Terminal, from any directory:
#   /bin/bash <checkout>/tmp/by-week/2026-W48/operator/30-cut-v1.3.0.sh <40-hex reviewed main SHA>
# (the runnable copy lives under the ignored tmp/; this tracked copy is the record and holds placeholders)
# The session hands over one command that first checks this copy's sha256 and that the shell is not an agent's or
# an editor's. Every run writes its own log under logs/ beside this file.
# Run it after the final release-prep PR has merged, with that merge commit, and after the downstream dry run
# against the candidate has reported. It asks before each push and verifies the new tag exactly as consumers will.
# release/1.3 then equals main at that commit, so no merge-forward is needed. Until the first "Move release/1.3 ..."
# question nothing is pushed or signed.
source "$(dirname "$0")/common.sh"
refuse_agent
run_log 30-cut
TAG="v1.3.0"; AT_TAG="v1.3.0"
SHA="${1:?usage: $0 <40-hex reviewed main SHA>}"
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || die "the commit must be a full 40-hex SHA"
fp="$(/usr/bin/ssh-keygen -lf "$RELEASE_PUB" | awk '{print $2}')"
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
ngit fetch --quiet --tags "$RT_URL" "+refs/heads/main:refs/remotes/origin/main"
ngit merge-base --is-ancestor "$SHA" refs/remotes/origin/main || die "$SHA is not on origin/main"
# The cut commit is the release-prep PR's merge commit and nothing later, merged at the head that was reviewed.
PREP_PR="<final release-prep PR number>"     # filled in the runnable copy once the PR exists
PR_HEAD="<reviewed head of the final release-prep PR>"   # filled in the runnable copy once this file is committed
[[ "$PREP_PR" =~ ^[1-9][0-9]*$ ]] || die "PREP_PR is not a pull-request number"
[ "$(gh pr view "$PREP_PR" -R "$REPO" --json state,headRefOid -q '"\(.state) \(.headRefOid)"')" = "MERGED $PR_HEAD" ] || die "PR #$PREP_PR is not merged at the reviewed head $PR_HEAD"
PR_MERGE="$(gh pr view "$PREP_PR" -R "$REPO" --json mergeCommit -q .mergeCommit.oid)" || die "cannot read the merge commit of PR #$PREP_PR"
[ "$SHA" = "$PR_MERGE" ] || die "$SHA is not the merge commit of PR #$PREP_PR (${PR_MERGE:-none})"
# The merged tree is exactly the tree that was reviewed: nothing merged to main between the review and the merge
# rides into the tag. (So main must still have been at the candidate's commit when the PR merged.)
ngit fetch --quiet --no-tags "$RT_URL" "+refs/pull/$PREP_PR/head:refs/remotes/origin/pr-$PREP_PR-head" || die "cannot fetch the head of PR #$PREP_PR"
[ "$(ngit rev-parse "refs/remotes/origin/pr-$PREP_PR-head")" = "$PR_HEAD" ] || die "the fetched head of PR #$PREP_PR is not the reviewed head $PR_HEAD"
ngit diff --quiet "$PR_HEAD" "$SHA" || die "the tree of $SHA differs from the reviewed head $PR_HEAD; nothing was pushed or signed"
# Both test checks must have run and passed on exactly this commit (no checks at all is not green).
for check in "tests (3.10)" "tests (3.13)"; do
  got="$(gh api "repos/$REPO/commits/$SHA/check-runs" --paginate -q ".check_runs[] | select(.name == \"$check\" and .app.slug == \"github-actions\") | .conclusion" | sort -u | tr '\n' ' ')"
  [ "$got" = "success " ] || die "check '$check' on $SHA is '${got:-absent}', not success"
done

# The candidate: v1.3.0-rc.1 is exactly the tag object recorded at its cut, signed by the release key, and an
# ancestor of the cut commit. The cut commit differs from it only in release files, records and the install
# instructions. No pin, lock, workflow, agent, script or package file may differ. The files outside the release
# folders are named one by one; researchteam update copies documents from docs/ and the managed CLAUDE.md block
# into every derived repository, where agents follow them, so those are limited further below.
RC="v1.3.0-rc.1"; RC_OBJ="22359c747fd2bd86e8af826e31fd84ca476181ab"   # read back from the remote after the cut, 2026-11-24
[ "$(ngit rev-parse "refs/tags/$RC")" = "$RC_OBJ" ] || die "local $RC is not tag object $RC_OBJ"
[ "$(ngit ls-remote "$RT_URL" "refs/tags/$RC" | cut -f1)" = "$RC_OBJ" ] || die "remote $RC is not tag object $RC_OBJ"
verify_tag "$MAIN" "$RC"
FROZEN="$(ngit rev-parse "refs/tags/$RC^{commit}")"
[ "$SHA" != "$FROZEN" ] || die "$SHA is the candidate's own commit (the final's release files are missing)"
ngit merge-base --is-ancestor "$FROZEN" "$SHA" || die "$SHA does not contain the candidate $RC (${FROZEN:0:12})"
SINCE_FREEZE="$(ngit diff --no-renames --name-only "$FROZEN" "$SHA")" || die "cannot list the changes since the candidate"
[ -n "$SINCE_FREEZE" ] || die "$SHA changes nothing since the candidate (the release files are missing)"
EXTRA="$(printf '%s\n' "$SINCE_FREEZE" | grep -vxE 'CHANGELOG\.md|docs/release/.*|(docs_src|references/plans|workSummaries)/.*|README\.md|CLAUDE\.md|researchteam/scaffold/CLAUDE\.template\.md|docs/(CONTRIBUTING|researchteam-framework|term-index-protocol)\.md|tests/test_install_pins\.py' || true)"
[ -z "$EXTRA" ] || die "changes since the candidate outside release files, records and install instructions: $(printf '%s' "$EXTRA" | tr '\n' ' ')"
# The instruction file agents read, and the template every new repository gets it from: at most the one install line.
for f in CLAUDE.md researchteam/scaffold/CLAUDE.template.md; do
  stat_line="$(ngit diff --no-renames --numstat "$FROZEN" "$SHA" -- "$f" | cut -f1,2 | tr '\t' ' ')"
  [ -z "$stat_line" ] || [ "$stat_line" = "1 1" ] || die "$f changes more than one line since the candidate ($stat_line)"
  [ -z "$stat_line" ] || ngit diff --no-renames -U0 "$FROZEN" "$SHA" -- "$f" | grep -xF '+# a release instead of main: append the signed tag, e.g. ...researchteam.git@v1.3.0' >/dev/null \
    || die "the changed line in $f is not the install example naming v1.3.0"
  [ -z "$stat_line" ] || ngit diff --no-renames -U0 "$FROZEN" "$SHA" -- "$f" | grep -xF -- '-# a release instead of main: append the signed tag, e.g. ...researchteam.git@v1.0.2' >/dev/null \
    || die "the removed line in $f is not the old install example"
done
# The previous stable release is signed, is exactly the tag object recorded at its cut, and is an ancestor.
PREV="v1.2.1"; PREV_OBJ="84dd75865cfae792c91935c008161f35ed39c048"   # read from the remote on 2026-11-24
[ "$(ngit rev-parse "refs/tags/$PREV")" = "$PREV_OBJ" ] || die "local $PREV is not tag object $PREV_OBJ"
[ "$(ngit ls-remote "$RT_URL" "refs/tags/$PREV" | cut -f1)" = "$PREV_OBJ" ] || die "remote $PREV is not tag object $PREV_OBJ"
verify_tag "$MAIN" "$PREV"
ngit merge-base --is-ancestor "refs/tags/$PREV^{commit}" "$SHA" || die "$SHA does not contain $PREV"

# The agentteams pin at that commit: the stable v1.3.0 (AT_TAG), verified HERE (signature, remote object), in the
# lock, in both extras and in the autosync ref.
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
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
LOG="$(ngit show "$SHA:.github/agents/references/security-decisions.log.csv")"
# A group-member pin move needs no per-release row. The rows it rests on must be present as PASS rows (a text
# check; their signatures are checked by the gate and by --verify-toolchain-pin below).
for a in release-line-agentteams-1.3 s10-release-cooldown-restored s10-first-party-releases-2026-11 management-roster-enroll:infrastructure-management; do
  printf '%s\n' "$LOG" | grep -F ",$a,PASS," >/dev/null || die "no signed $a row at $SHA"
done
ngit cat-file -e "$SHA:.agentteams/toolchain-group.json" || die "no .agentteams/toolchain-group.json at $SHA"
ngit show "$SHA:CHANGELOG.md" | grep -F '## 1.3.0 (tag `v1.3.0`, on `release/1.3`)' >/dev/null || die "no '## 1.3.0' CHANGELOG entry at $SHA"
NOTES="$(ngit show "$SHA:docs/release/release-notes-v1.3.0.md")" || die "no docs/release/release-notes-v1.3.0.md at $SHA"
# The group file must VERIFY at $SHA (signature, workspace binding, no HALT on s10-toolchain-group), not merely
# exist. Run from the root-owned agentteams install, in a detached worktree of $SHA so the workspace binding sees
# origin.
AGENTTEAMS_BIN="<signer>"   # root-owned install built from a signed agentteams tag
[[ -x "$AGENTTEAMS_BIN" && "$(/usr/bin/stat -f %Su "$AGENTTEAMS_BIN")" == root ]] || die "no root-owned agentteams at $AGENTTEAMS_BIN"
SIGNER_PY="${AGENTTEAMS_BIN%/agentteams}/python"
[[ -x "$SIGNER_PY" ]] || die "no python beside the root-owned agentteams"
ngit worktree add -q --detach "$TMP/rt" "$SHA" || die "cannot check out $SHA for the checks"
trap 'ngit worktree remove --force "$TMP/rt" 2>/dev/null; rm -rf "$TMP"' EXIT
( cd "$TMP/rt" && "$AGENTTEAMS_BIN" --verify-toolchain-pin toolchain.lock --allowed-signers "$ALLOWED_SIGNERS" \
    --output .github/agents --description brief.json ) || die "the toolchain-group pin does not verify at $SHA (must exit 0)"
# The line-move row must CLEAR at $SHA (signature, lineage, no later HALT or retraction), not merely be present as
# text (C-2). A non-consuming gate check, from an empty directory.
mkdir "$TMP/empty"
( cd "$TMP/empty" && "$SIGNER_PY" -I -P - "$TMP/rt/.github/agents" release-line-agentteams-1.3 ) <<'PY' || die "release-line-agentteams-1.3 does not clear at $SHA; nothing was pushed or signed"
import sys
from pathlib import Path
from agentteams.cli.security_gate import check_clearance
ok, why = check_clearance(Path(sys.argv[1]), action=sys.argv[2], consume=False) if "consume" in check_clearance.__code__.co_varnames else check_clearance(Path(sys.argv[1]), action=sys.argv[2])
print(f"  {sys.argv[2]}: {'clears' if ok else 'REFUSED: ' + str(why)[:200]}")
sys.exit(0 if ok else 1)
PY
# The decisions log at $SHA: no unretracted HALT anywhere, and no pending condition in a row added since the
# previous release (operator ruling, 2026-11-24: older pending rows are reported, not refused). A row counts as
# added when its (date, action, verdict) is not in the log at the previous release's commit.
ngit show "refs/tags/$PREV^{commit}:.github/agents/references/security-decisions.log.csv" > "$TMP/log.prev.csv" || die "cannot read the decisions log at $PREV"
printf '%s\n' "$LOG" > "$TMP/log.now.csv"
( cd "$TMP/empty" && "$SIGNER_PY" -I -P - "$TMP/log.prev.csv" "$TMP/log.now.csv" ) <<'PY' || die "the decisions log at $SHA has an unretracted HALT or a new pending condition; nothing was pushed or signed"
import csv, sys
def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
def key(r):
    return ((r.get("timestamp") or "").strip(), (r.get("action_reviewed") or "").strip(), (r.get("verdict") or "").strip())
prev, now = rows(sys.argv[1]), rows(sys.argv[2])
old = {key(r) for r in prev}
bad = 0
for i, r in enumerate(now):
    verdict, action = (r.get("verdict") or "").strip().upper(), (r.get("action_reviewed") or "").strip()
    if verdict == "HALT":
        retracted = any((n.get("verdict") or "").strip().upper() == "HALT-RETRACTED"
                        and (n.get("action_reviewed") or "").strip() == action for n in now[i + 1:])
        if not retracted:
            print(f"  HALT stands: {action}"); bad += 1
    if (r.get("conditions_verified") or "").strip().lower() == "pending":
        if key(r) in old:
            print(f"  reported, not refused (older than the previous release): pending condition on {action}")
        else:
            print(f"  PENDING condition on a row added since the previous release: {action}"); bad += 1
print(f"  decisions log: {len(now)} rows, {len(now) - len(prev)} more than at the previous release; {bad} blocking")
sys.exit(1 if bad else 0)
PY
# The copied term-index core at $SHA: it matches its manifest, every file equals the signed agentteams tag the
# manifest names, and its commit is the commit the lock pins. The comparing code is the checkout's own package,
# run from an empty directory with the root-owned python (-I: no current directory, no user site).
( cd "$TMP/empty" && AGENTTEAMS_ALLOWED_SIGNERS="$ALLOWED_SIGNERS" "$SIGNER_PY" -I -B -c 'import sys, runpy
sys.path.insert(0, sys.argv[1]); sys.argv = ["researchteam._term_core_upstream", "--root", sys.argv[1]]
runpy.run_module("researchteam._term_core_upstream", run_name="__main__")' "$TMP/rt" ) || die "the copied term-index core does not equal the signed agentteams tag at $SHA; nothing was pushed or signed"
ngit show "$SHA:scripts/term-index-core/PINNED.json" | grep -F "\"commit\": \"$AT_PEELED\"" >/dev/null || die "the core manifest at $SHA does not name the lock's commit $AT_PEELED"

ngit rev-parse -q --verify "refs/tags/$TAG" >/dev/null && die "$TAG already exists; tags are immutable. If an earlier run signed it here but did not push it, stop and tell the researchteam session; do not delete it yourself"
# Captured first, so a failed listing stops the run instead of reading as "no such tag".
remote_tag="$(ngit ls-remote "$RT_URL" "refs/tags/$TAG")" || die "cannot list the remote's tags; nothing was pushed or signed"
[ -z "$remote_tag" ] || die "$TAG already exists on the remote; tags are immutable"
existing="$(ngit ls-remote "$RT_URL" refs/heads/release/1.3 | cut -f1)" || die "cannot read release/1.3 on the remote; nothing was pushed or signed"
[ "$existing" = "$FROZEN" ] || [ "$existing" = "$SHA" ] || die "release/1.3 is at ${existing:-nothing}, neither the candidate ${FROZEN:0:12} nor $SHA"

say "release/1.3 and $TAG at $SHA (pins agentteams $AT_TAG ${AT_PEELED:0:12})"
ngit log -1 --format='  %h %s' "$SHA"
echo "  Paths that differ from the candidate $RC (${FROZEN:0:12}):"; printf '%s\n' "$SINCE_FREEZE" | sed 's/^/    /'
confirm "Move release/1.3 forward to ${SHA:0:12} and sign $TAG there? (This is the go for v1.3.0.)"
# Pushes use your credentials (so plain git, but no hooks and an explicit URL); everything else stays neutralised.
# Forward only: the lease names the candidate's commit, so the branch moves only if it is still exactly there, and
# the cut commit contains that commit (checked above), so the move is a fast-forward.
[ "$existing" = "$SHA" ] || git -c core.hooksPath=/dev/null push --quiet --force-with-lease="refs/heads/release/1.3:$FROZEN" "$RT_URL" "$SHA:refs/heads/release/1.3"
[ "$(ngit ls-remote "$RT_URL" refs/heads/release/1.3 | cut -f1)" = "$SHA" ] || die "remote release/1.3 is not at $SHA after the push; nothing was signed"
ngit -c user.name="$NAME" -c user.email="$EMAIL" -c gpg.format=ssh -c gpg.ssh.program=/usr/bin/ssh-keygen \
  -c user.signingkey="$RELEASE_PUB" tag -s "$TAG" "$SHA" -m "researchteam 1.3.0 — first release of the 1.3 line (release/1.3): agentteams 1.3

Pins agentteams $AT_TAG ($AT_PEELED). See CHANGELOG.md and docs/release-policy.md."
verify_tag "$MAIN" "$TAG"
[ "$(ngit describe --tags --match 'v[0-9]*' --exact-match "$SHA")" = "$TAG" ] || die "git describe does not name $TAG at $SHA"
OBJ="$(ngit rev-parse "refs/tags/$TAG")"; PEELED="$(ngit rev-parse "refs/tags/$TAG^{commit}")"
[ "$PEELED" = "$SHA" ] || die "peeled $PEELED != $SHA"
confirm "Push $TAG (object ${OBJ:0:12}) to origin?"
git -c core.hooksPath=/dev/null push --quiet "$RT_URL" "refs/tags/$TAG"
[ "$(ngit ls-remote "$RT_URL" "refs/tags/$TAG" | cut -f1)" = "$OBJ" ] || die "remote tag object differs"
if ! gh release view "$TAG" -R "$REPO" >/dev/null 2>&1; then
  drain; read -r -p "Create the GitHub release for $TAG (marked Latest)? [y/N] " a
  if [ "$a" = y ]; then
    gh release create "$TAG" -R "$REPO" --verify-tag --latest --title "researchteam 1.3.0" --notes "$NOTES" \
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
echo "  release/1.3: $(ngit ls-remote "$RT_URL" refs/heads/release/1.3 | cut -f1)"
echo "  GitHub verification : $VERIFIED"
echo "  run log    : $RUN_LOG"
echo "Tell the researchteam session. Then resume the autosync (script 28, resume)."
