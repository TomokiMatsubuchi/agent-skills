#!/usr/bin/env python3
"""Sync each skill in agent-skills/skills/ to each CLI as a symlink.

- Codex:  ~/.codex/skills/<skill>
- Claude: ~/.claude/skills/<skill>
- Grok:   ~/.grok/skills/<skill>
- Droid:  ~/.factory/skills/<skill>
- Anti-Gravity CLI:
    source:  ~/.gemini/antigravity-cli/plugins/agent-skills/skills/<skill>
    runtime: ~/.gemini/config/plugins/agent-skills/skills/<skill>
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


MASTER = Path(__file__).resolve().parent.parent
SKILLS_DIR = MASTER / "skills"

CLI_TARGETS = {
    "codex": Path.home() / ".codex" / "skills",
    "claude": Path.home() / ".claude" / "skills",
    "grok": Path.home() / ".grok" / "skills",
    "droid": Path.home() / ".factory" / "skills",
}

ANTIGRAVITY_PLUGIN_DIR = Path.home() / ".gemini" / "antigravity-cli" / "plugins" / "agent-skills"
ANTIGRAVITY_PLUGIN_SKILLS_DIR = ANTIGRAVITY_PLUGIN_DIR / "skills"

# Anti-Gravity CLI copies imported plugins into ~/.gemini/config/plugins at install
# time. We keep the runtime directory in sync with the source plugin directory
# so that skill edits are reflected without re-running `agy plugin install`.
ANTIGRAVITY_CONFIG_DIR = Path.home() / ".gemini" / "config" / "plugins" / "agent-skills"
ANTIGRAVITY_CONFIG_SKILLS_DIR = ANTIGRAVITY_CONFIG_DIR / "skills"


def discover_skills() -> list[Path]:
    if not SKILLS_DIR.is_dir():
        return []
    return [p for p in sorted(SKILLS_DIR.iterdir()) if p.is_dir() and (p / "SKILL.md").is_file()]


def skill_targets(skill_dir: Path) -> list[tuple[str, Path]]:
    """Return all (label, target SKILL.md path) pairs for a given source skill."""
    targets: list[tuple[str, Path]] = []
    name = skill_dir.name
    for cli, target_dir in CLI_TARGETS.items():
        targets.append((cli, target_dir / name / "SKILL.md"))
    targets.append(("antigravity-source", ANTIGRAVITY_PLUGIN_SKILLS_DIR / name / "SKILL.md"))
    targets.append(("antigravity-runtime", ANTIGRAVITY_CONFIG_SKILLS_DIR / name / "SKILL.md"))
    return targets


def is_skill_empty(path: Path) -> bool:
    """Return True if the file is missing or has no meaningful content."""
    if not path.exists():
        return True
    content = path.read_text(encoding="utf-8")
    return content.strip() == ""


def link_skill(skill_dir: Path, target_dir: Path, dry_run: bool, force: bool) -> None:
    target = target_dir / skill_dir.name
    source = skill_dir.resolve()

    if target.is_symlink():
        if target.resolve() == source:
            print(f"    OK (already linked): {target}")
            return
        print(f"    WARN: {target} points to {target.readlink()}")
        if not force:
            return
        if not dry_run:
            target.unlink()
    elif target.exists():
        print(f"    WARN: {target} exists (not a symlink); use --force to replace")
        if not force:
            return
        if not dry_run:
            shutil.rmtree(target) if target.is_dir() else target.unlink()

    print(f"    {'WOULD ' if dry_run else ''}LINK: {target} -> {source}")
    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
        target.symlink_to(source)


def setup_antigravity_plugin(dry_run: bool, plugin_dir: Path) -> None:
    manifest = plugin_dir / "plugin.json"
    if manifest.exists():
        return
    print(f"  {'WOULD ' if dry_run else ''}CREATE plugin.json: {manifest}")
    if not dry_run:
        plugin_dir.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({"name": "agent-skills"}, indent=2) + "\n", encoding="utf-8")


def sync_for_cli(cli: str, skill_dirs: list[Path], dry_run: bool, force: bool) -> None:
    target_dir = CLI_TARGETS[cli]
    if not target_dir.parent.exists():
        print(f"  {cli}: parent directory missing ({target_dir.parent}); skipping")
        return
    print(f"  {cli}: {target_dir}")
    for skill_dir in skill_dirs:
        link_skill(skill_dir, target_dir, dry_run, force)


def sync_antigravity(skill_dirs: list[Path], dry_run: bool, force: bool) -> None:
    # Source plugin directory (used by `agy plugin install` / import).
    print(f"  antigravity-source: {ANTIGRAVITY_PLUGIN_SKILLS_DIR}")
    setup_antigravity_plugin(dry_run, ANTIGRAVITY_PLUGIN_DIR)
    for skill_dir in skill_dirs:
        link_skill(skill_dir, ANTIGRAVITY_PLUGIN_SKILLS_DIR, dry_run, force)

    # Runtime plugin directory (where agy actually reads skills after import).
    if ANTIGRAVITY_CONFIG_DIR.parent.exists():
        print(f"  antigravity-runtime: {ANTIGRAVITY_CONFIG_SKILLS_DIR}")
        setup_antigravity_plugin(dry_run, ANTIGRAVITY_CONFIG_DIR)
        for skill_dir in skill_dirs:
            link_skill(skill_dir, ANTIGRAVITY_CONFIG_SKILLS_DIR, dry_run, force)
    else:
        print(f"  antigravity-runtime: {ANTIGRAVITY_CONFIG_DIR.parent} does not exist")
        print(f"    Run: agy plugin install {ANTIGRAVITY_PLUGIN_DIR}")


def verify_skills(skill_dirs: list[Path], strict: bool = False) -> bool:
    """Verify that source SKILL.md files and their targets are non-empty.

    If strict is False, missing targets are reported but not treated as failures
    (the user may simply not use every CLI). If strict is True, every expected
    target must exist and be non-empty.
    """
    ok = True
    print("Verifying skill files...")

    for skill_dir in skill_dirs:
        source = skill_dir / "SKILL.md"

        if is_skill_empty(source):
            print(f"  FAIL: source SKILL.md is empty: {source}")
            ok = False
            continue
        print(f"  source OK: {source} ({source.stat().st_size} bytes)")

        for label, target in skill_targets(skill_dir):
            if not target.exists():
                if strict:
                    print(f"    FAIL: target missing: {label} -> {target}")
                    ok = False
                else:
                    print(f"    SKIP: target missing: {label} -> {target}")
                continue

            if target.is_symlink() and not target.resolve().exists():
                print(f"    FAIL: broken symlink: {label} -> {target}")
                ok = False
                continue

            if is_skill_empty(target):
                print(f"    FAIL: target SKILL.md is empty: {label} -> {target}")
                ok = False
            else:
                print(f"    target OK: {label} -> {target} ({target.stat().st_size} bytes)")

    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Symlink agent-skills to each CLI's skill directory.")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run).")
    parser.add_argument("--force", action="store_true", help="Replace existing skills or symlinks.")
    parser.add_argument("--verify", action="store_true", help="Verify source and target SKILL.md files are non-empty.")
    parser.add_argument("--verify-strict", action="store_true", help="Like --verify, but fail if any expected target is missing.")
    parser.add_argument("--only", type=str, help="Comma-separated CLI list (codex,claude,grok,antigravity,droid).")
    args = parser.parse_args(argv)

    selected = args.only.split(",") if args.only else ["codex", "claude", "grok", "antigravity", "droid"]
    valid = {"codex", "claude", "grok", "antigravity", "droid"}
    unknown = set(selected) - valid
    if unknown:
        print(f"Unknown CLI(s): {', '.join(sorted(unknown))}", file=sys.stderr)
        return 1

    skill_dirs = discover_skills()
    if not skill_dirs:
        print(f"No skills found in {SKILLS_DIR}")
        return 0

    if args.verify or args.verify_strict:
        if not verify_skills(skill_dirs, strict=args.verify_strict):
            print("\nVerification FAILED.")
            return 1
        print("\nVerification OK.")
        return 0

    print(f"Skills dir: {SKILLS_DIR}")
    print(f"Skills: {len(skill_dirs)}")
    print(f"Mode: {'DRY-RUN' if not args.apply else 'APPLY'}")
    print()

    for cli in selected:
        if cli in CLI_TARGETS:
            sync_for_cli(cli, skill_dirs, not args.apply, args.force)
        elif cli == "antigravity":
            sync_antigravity(skill_dirs, not args.apply, args.force)

    print()
    if not args.apply:
        print("Dry-run complete. Use --apply to apply.")
    else:
        print("Sync complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
