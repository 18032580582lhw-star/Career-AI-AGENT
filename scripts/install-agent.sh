#!/usr/bin/env bash
set -euo pipefail

repo_url=""
install_root="$PWD"
agent="all"
checkout_dir=""
update=0
skip_eval=0

usage() {
  cat <<'EOF'
Usage:
  bash scripts/install-agent.sh --repo-url https://github.com/OWNER/REPO.git [options]

Options:
  --install-root DIR     Directory that will contain the checkout.
  --agent NAME           codex, claude, opencode, or all. Default: all.
  --checkout-dir NAME    Override checkout directory name.
  --update               Run git pull --ff-only in an existing checkout.
  --skip-eval            Skip eval and eval-matrix after install.
  -h, --help             Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-url)
      repo_url="${2:-}"
      shift 2
      ;;
    --install-root)
      install_root="${2:-}"
      shift 2
      ;;
    --agent)
      agent="${2:-}"
      shift 2
      ;;
    --checkout-dir)
      checkout_dir="${2:-}"
      shift 2
      ;;
    --update)
      update=1
      shift
      ;;
    --skip-eval)
      skip_eval=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$repo_url" ]]; then
  echo "--repo-url is required" >&2
  usage >&2
  exit 2
fi

case "$agent" in
  codex|claude|opencode|all) ;;
  *)
    echo "--agent must be codex, claude, opencode, or all" >&2
    exit 2
    ;;
esac

step() {
  printf '\n==> %s\n' "$1"
}

need_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "$1 was not found. Install $1 and rerun this script." >&2
    exit 1
  fi
}

repo_name_from_url() {
  local trimmed leaf
  trimmed="${1%/}"
  leaf="${trimmed##*/}"
  leaf="${leaf%.git}"
  printf '%s\n' "$leaf"
}

find_python() {
  for candidate in python3.12 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      "$candidate" --version >/dev/null
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  echo "Python 3.12 was not found. Install Python >=3.12 and rerun this script." >&2
  return 1
}

need_command git

if [[ -z "$checkout_dir" ]]; then
  checkout_dir="$(repo_name_from_url "$repo_url")"
fi

if [[ -z "$checkout_dir" ]]; then
  echo "Could not derive checkout directory from --repo-url. Pass --checkout-dir." >&2
  exit 1
fi

mkdir -p "$install_root"
install_root="$(cd "$install_root" && pwd)"
project_dir="$install_root/$checkout_dir"

if [[ -e "$project_dir" ]]; then
  if [[ ! -d "$project_dir/.git" ]]; then
    echo "Checkout path exists but is not a Git repository: $project_dir" >&2
    exit 1
  fi
  step "Using existing checkout: $project_dir"
  if [[ "$update" -eq 1 ]]; then
    git -C "$project_dir" pull --ff-only
  fi
else
  step "Cloning repository"
  git clone "$repo_url" "$project_dir"
fi

python_cmd="$(find_python)"
venv_dir="$project_dir/.venv"

if [[ ! -x "$venv_dir/bin/python" && ! -x "$venv_dir/Scripts/python.exe" ]]; then
  step "Creating virtual environment"
  "$python_cmd" -m venv "$venv_dir"
fi

if [[ -x "$venv_dir/bin/python" ]]; then
  venv_python="$venv_dir/bin/python"
  cli="$venv_dir/bin/career-ai-agent"
elif [[ -x "$venv_dir/Scripts/python.exe" ]]; then
  venv_python="$venv_dir/Scripts/python.exe"
  cli="$venv_dir/Scripts/career-ai-agent.exe"
else
  echo "Virtual environment Python was not created under $venv_dir" >&2
  exit 1
fi

step "Installing package"
"$venv_python" -m pip install --upgrade pip
(cd "$project_dir" && "$venv_python" -m pip install -e .)

if [[ ! -x "$cli" ]]; then
  echo "career-ai-agent executable was not created: $cli" >&2
  exit 1
fi

step "Running doctor"
"$cli" doctor

step "Installing host Skill adapters"
"$cli" init --workspace "$project_dir" --agent "$agent"

if [[ "$skip_eval" -eq 0 ]]; then
  step "Running eval"
  "$cli" eval --case-dir "$project_dir/evals/career_cases" --prompt-dir "$project_dir/prompts"

  step "Running eval-matrix"
  "$cli" eval-matrix --case-dir "$project_dir/evals/career_cases" --prompt-dir "$project_dir/prompts"
fi

step "Installed"
printf 'Project: %s\n' "$project_dir"
printf 'CLI: %s\n' "$cli"
printf 'Codex/OpenCode Skill: %s\n' "$project_dir/.agents/skills/career-resume-tailor"
printf 'Claude Skill: %s\n' "$project_dir/.claude/plugins/career-resume-tailor"
