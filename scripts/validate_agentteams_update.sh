#!/usr/bin/env bash
set -euo pipefail

# Validate scope and fence integrity for agentteams and researchteam update runs.
#
# Allowed paths cover the update layers plus the generated/user-owned identity files that
# init/personalize/materialize legitimately write:
#   Layer-1 (agentteams-managed): .github/, .vscode/tasks.json (agentteams meta-tasks,
#                                 sentinel-merged so user tasks are preserved), the native and
#                                 interop agent surfaces (.claude/, .goose/, .codex/, .agents/,
#                                 AGENTS.md), bridge records (references/bridges/ only; the rest
#                                 of references/ is user-owned), and sandbox/ confinement scripts
#                                 (a security boundary: an update PR that touches it needs
#                                 @security review before merge)
#   Layer-2 (researchteam-synced): docs/, scripts/, .claude/, .gitignore, and CLAUDE.md's
#                                  fenced-preserve managed block
#   Layer-1 root artifacts (exact paths only; the rest of references/ stays user-owned):
#                                 references/architecture-{graph.md,graph.svg,modules.svg}
#                                 (architecture-map refresh on --update), .goosehints,
#                                 SETUP-REQUIRED.md, and .agentteams/bin/ (Codex role gate and
#                                 runner server under an orchestrator-only write_policy; a security
#                                 boundary like sandbox/)
#   Generated / user-owned (permitted to change, NOT wholesale-synced): README.md and CLAUDE.md's
#                                  project header (generated from brief.json by personalize),
#                                  brief.json, .researchteam
#
# This is a DRIFT check, not a control against a compromised upstream: in the autosync job,
# agentteams code has already run (with the job's write token) before this script runs, so a
# malicious upstream could alter this script or the tree first. Its job is to catch an update that
# writes somewhere it should not. A stronger control would regenerate in a job that holds no write
# token and hand the diff to a separate, privileged job.

allowed_paths_regex='^(\.github/|\.vscode/tasks\.json$|brief\.json$|CLAUDE\.md$|README\.md$|\.gitignore$|\.researchteam$|docs/|scripts/|\.claude/|\.goose/|\.codex/|\.agents/|AGENTS\.md$|references/bridges/|references/architecture-graph\.(md|svg)$|references/architecture-modules\.svg$|\.goosehints$|SETUP-REQUIRED\.md$|\.agentteams/bin/|sandbox/)'
legacy_exclude_regex='^\.github/agents/\.agentteams-backups/'
forbidden_nested_mirror_regex='^\.github/agents/\.github(/|$)'

if [[ -d ".github/agents/.github" ]]; then
  echo "ERROR: Forbidden nested mirror exists: .github/agents/.github"
  exit 1
fi

# Optional override for local/non-git testing.
if [[ -n "${VALIDATION_CHANGED_FILES:-}" ]]; then
  changed_files="$VALIDATION_CHANGED_FILES"
elif git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  # Tracked changes (staged or not) PLUS new untracked files: a brand-new file written outside the
  # allowlist must not skip the scope check just because it was never added.
  # core.quotePath=false: a non-ASCII name must reach the allowlist as itself, not "\303\251"-quoted.
  tracked="$(git -c core.quotePath=false diff --name-only HEAD 2>/dev/null || git -c core.quotePath=false diff --name-only)"
  untracked="$(git -c core.quotePath=false ls-files --others --exclude-standard)"
  changed_files="$(printf '%s\n%s\n' "$tracked" "$untracked" | sed '/^$/d' | sort -u)"
else
  if [[ "${VALIDATION_ALLOW_NO_GIT:-0}" == "1" ]]; then
    echo "WARNING: No git worktree detected and VALIDATION_CHANGED_FILES not set; skipping diff-based validation due to VALIDATION_ALLOW_NO_GIT=1."
    exit 0
  fi
  echo "ERROR: No git worktree detected and VALIDATION_CHANGED_FILES not set. Set VALIDATION_ALLOW_NO_GIT=1 to allow skip."
  exit 1
fi
if [[ -z "${changed_files}" ]]; then
  echo "No file changes detected; validation passed."
  exit 0
fi

echo "Validating changed file scope..."
while IFS= read -r file; do
  [[ -z "$file" ]] && continue

  if [[ "$file" =~ $forbidden_nested_mirror_regex ]]; then
    echo "ERROR: Forbidden nested mirror path changed or reintroduced: $file"
    exit 1
  fi

  if [[ "$file" =~ $legacy_exclude_regex ]]; then
    continue
  fi

  # The scope allowlist describes what an agentteams/researchteam UPDATE may touch. For ordinary
  # project edits (derived repos have their own content outside these paths) the bridge's
  # `validate` sets VALIDATION_SKIP_SCOPE=1; fence and placeholder checks still run.
  if [[ "${VALIDATION_SKIP_SCOPE:-0}" != "1" && ! "$file" =~ $allowed_paths_regex ]]; then
    echo "ERROR: Out-of-scope file changed: $file"
    exit 1
  fi

done <<< "$changed_files"

echo "Checking AGENTTEAMS fence pairing..."
# Restrict check to markdown-like files likely to contain fences.
markdown_files="$(printf '%s\n' "$changed_files" | grep -E '\.(md|agent\.md|reference\.md)$' || true)"
if [[ -n "$markdown_files" ]]; then
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    # Exempt generated bridge report/inventory artifacts: they DISPLAY marker syntax as
    # table data (agent-inventory.md lists each agent's real BEGIN marker), which a balance
    # check miscounts as unpaired fences (e.g. 8 BEGIN / 0 END) — a false positive.
    case "$file" in references/bridges/*|*/references/bridges/*) continue;; esac
    # Count only REAL HTML-comment fence markers, not prose mentions of the marker
    # syntax. A reference may legitimately quote `AGENTTEAMS:BEGIN` in backticks while
    # carrying no fence (e.g. instruction-authority.reference.md) — a bare-substring grep
    # miscounts that as an extra BEGIN and reports a phantom mismatch.
    begin_count=$(grep -cE '<!--[[:space:]]*AGENTTEAMS:BEGIN[[:space:]]' "$file" || true)
    end_count=$(grep -cE '<!--[[:space:]]*AGENTTEAMS:END[[:space:]]' "$file" || true)
    if [[ "$begin_count" -ne "$end_count" ]]; then
      echo "ERROR: Fence mismatch in $file (BEGIN=$begin_count END=$end_count)"
      exit 1
    fi
  done <<< "$markdown_files"
fi

echo "Checking unresolved manual placeholders..."
placeholder_hits=""
while IFS= read -r file; do
  [[ -z "$file" ]] && continue
  [[ ! -f "$file" ]] && continue

  # Ignore backup trees and docs intentionally discussing MANUAL tokens.
  if [[ "$file" =~ $legacy_exclude_regex ]]; then
    continue
  fi

  # Enforce placeholder resolution only in active agent definitions and root copilot instructions.
  if [[ ! "$file" =~ ^\.github/agents/.*\.agent\.md$ ]] && [[ "$file" != ".github/copilot-instructions.md" ]]; then
    continue
  fi

  case "$file" in
    .github/agents/agent-updater.agent.md|.github/agents/content-enricher.agent.md|.github/agents/SETUP-REQUIRED.md)
      continue
      ;;
  esac

  file_hits=$(grep --line-number '{MANUAL:' "$file" 2>/dev/null || true)
  if [[ -n "$file_hits" ]]; then
    placeholder_hits+="$file:$file_hits"$'\n'
  fi
done <<< "$changed_files"

if [[ -n "$placeholder_hits" ]]; then
  echo "ERROR: Unresolved manual placeholders found in changed files:"
  printf "%s" "$placeholder_hits"
  exit 1
fi

if [[ -d ".github/agents/.github" ]]; then
  echo "ERROR: Forbidden nested mirror exists after validation: .github/agents/.github"
  exit 1
fi

echo "Validation passed."
