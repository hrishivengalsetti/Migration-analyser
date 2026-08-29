from pathlib import Path
from models import FileDiff, FileStatus

def analyze_file_diff(original_dir: Path, migrated_dir: Path) -> list[FileDiff]:
    diffs = []

    original_files = {
        p.relative_to(original_dir): p
        for p in original_dir.rglob("*.py")
        if not any(part.startswith('.') or part == '__pycache__' for part in p.parts)
    }

    migrated_files = {
        p.relative_to(migrated_dir): p
        for p in migrated_dir.rglob("*.py")
        if not any(part.startswith('.') or part == '__pycache__' for part in p.parts)
    }

    all_keys = set(original_files) | set(migrated_files)

    for rel_path in sorted(all_keys):
        if rel_path in original_files and rel_path not in migrated_files:
            # deleted
            diffs.append(FileDiff(
                file=str(rel_path),
                status=FileStatus.DELETED,
                original_content=original_files[rel_path].read_text(errors='replace'),
            ))
        elif rel_path not in original_files and rel_path in migrated_files:
            # added
            diffs.append(FileDiff(
                file=str(rel_path),
                status=FileStatus.ADDED,
                migrated_content=migrated_files[rel_path].read_text(errors='replace'),
            ))
        else:
            # both exist — compare
            orig_content = original_files[rel_path].read_text(errors='replace')
            migr_content = migrated_files[rel_path].read_text(errors='replace')
            if orig_content != migr_content:
                diffs.append(FileDiff(
                    file=str(rel_path),
                    status=FileStatus.MODIFIED,
                    original_content=orig_content,
                    migrated_content=migr_content,
                ))

    return diffs
