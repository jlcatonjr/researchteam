#!/usr/bin/env bash
set -euo pipefail

# Validate scope and fence integrity for agentteams and researchteam update runs.
#
# Allowed paths cover two update layers:
#   Layer-1 (agentteams-managed): .github/, .vscode/tasks.json (agentteams meta-tasks,
#                                 sentinel-merged so user tasks are preserved)
#   Layer-2 (researchteam-managed): docs/, scripts/, .claude/, CLAUDE.md,
#                                   README.md, .gitignore, .researchteam

allowed_paths_regex='^(\.github/|\.vscode/tasks\.json$|brief\.json$|CLAUDE\.md$|README\.md$|\.gitignore$|\.researchteam$|docs/|scripts/|\.claude/)'
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
  changed_files="$(git diff --name-only)"
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

  if [[ ! "$file" =~ $allowed_paths_regex ]]; then
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
    begin_count=$(grep -c 'AGENTTEAMS:BEGIN' "$file" || true)
    end_count=$(grep -c 'AGENTTEAMS:END' "$file" || true)
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
