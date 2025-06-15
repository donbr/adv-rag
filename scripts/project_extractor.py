#!/usr/bin/env python3
"""
Project Files Extractor
Extracts a repository into a multi-file structure:
  - core_index.md: executive summary & file index (with Mermaid diagram)
  - metadata.json: enriched manifest (component + description)
  - files/: individual file content markdowns
Excludes development dirs and binary files.
"""
import logging
import sys
import fnmatch
import json
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Limits
MAX_FILE_SIZE    = 10 * 1024 * 1024   # 10MB per file
MAX_TOTAL_SIZE   = 100 * 1024 * 1024  # 100MB total

@dataclass
class FileInfo:
    path: Path
    relative_path: Path
    size: int
    size_fmt: str
    modified: str
    component: str
    description: str

@dataclass
class Config:
    exclude_dirs: set[str] = field(default_factory=lambda: {
        ".venv", ".git", "node_modules", "build", "logs", "__pycache__"
    })
    exclude_exts: set[str] = field(default_factory=lambda: {
        ".pyc", ".exe", ".dll", ".so", ".bin",
        ".jpg", ".png", ".pdf", ".zip"
    })
    exclude_patterns: set[str] = field(default_factory=lambda: {
        "*.lock", "*.pem", "secrets.*"
    })
    max_file_size: int = MAX_FILE_SIZE
    max_total_size: int = MAX_TOTAL_SIZE

class ProjectExtractor:
    def __init__(self, root: Path, out_dir: Path, config: Config):
        self.root      = root.resolve()
        self.out_dir   = out_dir.resolve()
        self.config    = config
        self.files_dir = self.out_dir / 'files'

    def collect(self) -> list[FileInfo]:
        files = []
        total = 0
        for f in self.root.rglob('*'):
            if not f.is_file(): continue
            if any(part in self.config.exclude_dirs for part in f.parts): continue
            if f.suffix.lower() in self.config.exclude_exts:      continue
            if any(fnmatch.fnmatch(f.name.lower(), p) for p in self.config.exclude_patterns): continue
            stat = f.stat()
            size = stat.st_size
            if size > self.config.max_file_size:
                logger.debug(f"Skipping large file {f}")
                continue
            chunk = f.read_bytes()[:1024]
            if b'\x00' in chunk:  # binary check
                continue
            rel = f.relative_to(self.root)
            comp = rel.parts[0] if len(rel.parts) > 1 else 'root'  # top-level component :contentReference[oaicite:3]{index=3}
            desc = self._extract_description(f)                   # first comment/docstring line :contentReference[oaicite:4]{index=4}
            files.append(FileInfo(
                path=f,
                relative_path=rel,
                size=size,
                size_fmt=self._fmt(size),
                modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime('%Y-%m-%d'),
                component=comp,
                description=desc
            ))
            total += size
            if total > self.config.max_total_size:
                logger.warning("Total size limit reached")
                break
        return sorted(files, key=lambda x: str(x.relative_path))

    def _fmt(self, size: int) -> str:
        if size > 1<<20: return f"{size/(1<<20):.1f}M"
        if size > 1<<10: return f"{size/(1<<10):.1f}K"
        return f"{size}B"

    def _extract_description(self, path: Path) -> str:
        text = path.read_text(encoding='utf-8', errors='ignore').splitlines()
        for line in text:
            s = line.strip()
            if s.startswith('"""') or s.startswith("#"):
                return s.strip('"""').lstrip('#').strip()
        return ""  # fallback if no comment found

    def _build_mermaid(self, files: list[FileInfo]) -> str:
        # Mermaid diagram of top-level components :contentReference[oaicite:5]{index=5} :contentReference[oaicite:6]{index=6}
        comps = sorted({fi.component for fi in files})
        lines = ["```mermaid", "graph LR", "  root((Root))"]
        for c in comps:
            if c == 'root': continue
            lines.append(f"  root --> {c}")
        lines.append("```")
        return "\n".join(lines)

    def write_core_index(self, files: list[FileInfo]):
        core = self.out_dir / 'core_index.md'
        with open(core, 'w', encoding='utf-8') as w:
            # Diagram first
            w.write(self._build_mermaid(files) + "\n\n")
            w.write(f"# Project Core Index\n")
            w.write(f"**Root Directory:** {self.root}\n")
            w.write(f"**Extraction Date:** {datetime.now(timezone.utc).isoformat()}\n\n")
            w.write("## Files Index\n")
            for i, fi in enumerate(files, 1):
                w.write(f"{i}. `{fi.relative_path}` ({fi.size_fmt}, {fi.component}) – {fi.description}\n")
        logger.info(f"Wrote core index to {core}")

    def write_metadata(self, files: list[FileInfo]):
        meta = self.out_dir / 'metadata.json'
        total_size = sum(fi.size for fi in files)
        data = {
            'root': str(self.root),
            'extraction_date': datetime.now(timezone.utc).isoformat(),
            'total_files': len(files),
            'total_size_bytes': total_size,
            'files': [
                {
                    'path': str(fi.relative_path),
                    'size_bytes': fi.size,
                    'component': fi.component,     # enriched tag
                    'description': fi.description, # one-line summary
                    'modified': fi.modified
                } for fi in files
            ]
        }
        with open(meta, 'w', encoding='utf-8') as w:
            json.dump(data, w, indent=2)
        logger.info(f"Wrote metadata to {meta}")

    def write_files(self, files: list[FileInfo]):
        for fi in files:
            out_path = self.files_dir / fi.relative_path.with_suffix('.md')
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as w:
                w.write(f"# FILE: {fi.relative_path}\n")
                w.write(f"*Size:* {fi.size_fmt}  *Component:* {fi.component}\n")
                w.write(f"*Description:* {fi.description}\n\n")
                # fenced code
                w.write("```\n")
                w.write(fi.path.read_text(encoding='utf-8', errors='ignore'))
                w.write("\n```\n")
        logger.info(f"Wrote individual files to {self.files_dir}")

    def run(self):
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)
        files = self.collect()
        if not files:
            logger.warning("No files found")
            return
        self.write_core_index(files)
        self.write_metadata(files)
        self.write_files(files)

def main():
    parser = argparse.ArgumentParser(description="Multi-file project extractor")
    parser.add_argument('root', nargs='?', default='.', help="Repository root")
    parser.add_argument('-o', '--output', default='extraction', help="Output directory")
    parser.add_argument('-v','--verbose', action='store_true', help="Verbose logging")
    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    cfg = Config()
    extractor = ProjectExtractor(Path(args.root), Path(args.output), cfg)
    try:
        extractor.run()
    except KeyboardInterrupt:
        logger.error("Cancelled")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback; traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
