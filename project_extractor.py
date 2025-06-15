#!/usr/bin/env python3
"""
Project Files Extractor
Extract all project files to a single text file with headers.
Excludes development directories similar to list_project_files.sh
"""

import logging
import sys
import re
import fnmatch
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict


# Configure simple logging for utility script
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Safety limits for file processing
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per file
MAX_TOTAL_SIZE = 100 * 1024 * 1024  # 100MB total output


@dataclass
class FileInfo:
    """Information about a file."""
    path: Path
    relative_path: Path
    size: int
    size_fmt: str
    modified: str
    stat_result: object  # os.stat_result


@dataclass
class ExtractorConfig:
    """Configuration for the extractor."""
    exclude_dirs: set[str] = field(default_factory=lambda: {
        ".venv", ".benchmarks", ".cursor", ".pytest_cache", "build",
        ".git", "node_modules", ".mypy_cache", ".ruff_cache", "logs", "__pycache__"
    })
    exclude_extensions: set[str] = field(default_factory=lambda: {
        ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bin",
        ".jpg", ".jpeg", ".png", ".gif", ".ico", ".svg", ".pdf",
        ".zip", ".tar", ".gz", ".bz2"
    })
    exclude_patterns: set[str] = field(default_factory=lambda: {
        "*.pem", "*.p12", "*.jks", "*.pfx", "*.crt", "*.cer",  # Certificate files
        "secrets.*", "credentials.*", "*.credentials",
        "uv.lock", "package-lock.json", "yarn.lock", "Pipfile.lock", "poetry.lock"
    })
    env_patterns: set[str] = field(default_factory=lambda: {
        ".env", ".env.*"  # Separate env handling to preserve .env.example
    })
    sensitive_prefixes: set[str] = field(default_factory=lambda: {
        "password", "secret", "key", "token", "api_key", "auth", "credential"
    })
    redactable_extensions: set[str] = field(default_factory=lambda: {
        ".env", ".toml", ".ini", ".conf", ".config", ".credentials", ".yml", ".yaml"
    })
    max_file_size: int = MAX_FILE_SIZE
    max_total_size: int = MAX_TOTAL_SIZE
    include_toc: bool = True
    collapse_large_files: bool = False
    collapse_threshold: int = 50  # lines
    skip_dotfiles: bool = False


class ProjectExtractor:
    """Extract project files to a consolidated text file."""
    
    def __init__(self, root_dir: str = ".", output_file: str = "project_files.txt", 
                 config: ExtractorConfig | None = None):
        """Initialize the extractor.
        
        Args:
            root_dir: Root directory to scan (default: current directory)
            output_file: Output file name (default: project_files.txt)
            config: Extractor configuration (default: ExtractorConfig())
        """
        self.root_dir = Path(root_dir).resolve()
        self.output_file = Path(output_file).resolve()
        self.config = config or ExtractorConfig()
        
        # Get the script file path to exclude it
        self.script_file = Path(__file__).resolve() if __file__ else None
        
    def validate_path_safety(self, path: Path) -> bool:
        """Prevent path traversal attacks.
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is safe (within root directory)
        """
        try:
            # Ensure path doesn't escape root directory
            path.resolve().relative_to(self.root_dir.resolve())
            return True
        except ValueError:
            logger.warning(f"Blocked path traversal attempt: {path}")
            return False
        
    def should_exclude_path(self, path: Path) -> bool:
        """Check if a path should be excluded.
        
        Args:
            path: Path to check
            
        Returns:
            True if path should be excluded
        """
        # Security check first
        if not self.validate_path_safety(path):
            return True
        
        # Exclude the script file itself
        if self.script_file and path.resolve() == self.script_file:
            logger.debug(f"Excluding script file: {path}")
            return True
            
        # Exclude the output file being created
        if path.resolve() == self.output_file:
            logger.debug(f"Excluding output file: {path}")
            return True
            
        # Exclude files that look like previous extracts
        if self._looks_like_extract_file(path):
            logger.debug(f"Excluding potential extract file: {path}")
            return True
        
        # Check sensitive file patterns (env files, keys, etc.)
        filename = path.name.lower()
        
        # Handle .env files with special logic to preserve .env.example
        for env_pattern in self.config.env_patterns:
            if fnmatch.fnmatch(filename, env_pattern.lower()):
                # Preserve .env.example and .env.template files
                if not any(preserve in filename for preserve in ['.example', '.template', '.sample']):
                    logger.debug(f"Excluding env file: {path}")
                    return True
        
        # Check other sensitive patterns
        for pattern in self.config.exclude_patterns:
            if fnmatch.fnmatch(filename, pattern.lower()):
                logger.debug(f"Excluding sensitive file: {path}")
                return True
        
        # Skip dotfiles if configured
        if self.config.skip_dotfiles and filename.startswith('.') and filename not in {'.gitignore', '.gitattributes'}:
            logger.debug(f"Excluding dotfile: {path}")
            return True
            
        # Check if any part of the path contains excluded directories
        for part in path.parts:
            if part in self.config.exclude_dirs:
                return True
                
        # Check file extension
        if path.suffix.lower() in self.config.exclude_extensions:
            return True
            
        return False
    
    def _looks_like_extract_file(self, path: Path) -> bool:
        """Check if a file looks like a previous extract file.
        
        Args:
            path: Path to check
            
        Returns:
            True if file appears to be an extract file
        """
        filename = path.name.lower()
        
        # Common extract file patterns
        extract_patterns = [
            'project_files.txt',
            'project_extract.txt',
            'codebase.txt',
            'source_files.txt',
            'code_extract.txt',
            'extracted_files.txt'
        ]
        
        # Check exact matches
        if filename in extract_patterns:
            return True
            
        # Check patterns with suffixes (project_files_2024.txt, etc.)
        for pattern in ['project_files', 'project_extract', 'codebase', 'code_extract']:
            if filename.startswith(pattern) and filename.endswith('.txt'):
                return True
                
        # Check if file is very large (likely an extract)
        try:
            if path.stat().st_size > 50 * 1024 * 1024:  # 50MB+
                # Check if it starts with our header pattern
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    first_line = f.readline().strip()
                    if first_line == "PROJECT FILES EXTRACTION":
                        return True
        except (IOError, OSError):
            pass
            
        return False
    
    def is_text_file(self, file_path: Path, stat_result: object = None) -> bool:
        """Check if a file is likely a text file.
        
        Args:
            file_path: Path to the file
            stat_result: Pre-computed stat result to avoid re-calling stat()
            
        Returns:
            True if file appears to be text
        """
        try:
            # Use provided stat result or compute it
            if stat_result is None:
                stat_result = file_path.stat()
            
            file_size = stat_result.st_size
            
            # Check file size first
            if file_size > self.config.max_file_size:
                logger.warning(f"File too large, skipping: {file_path} ({file_size} bytes)")
                return False
                
            # Empty files are considered text
            if file_size == 0:
                return True
                
            # Read first 1024 bytes to check for binary content
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                
            # Check for null bytes (strong indicator of binary)
            if b'\x00' in chunk:
                return False
                
            # Try to decode as UTF-8
            try:
                chunk.decode('utf-8')
                return True
            except UnicodeDecodeError:
                # Try other common encodings
                for encoding in ['latin-1', 'cp1252']:
                    try:
                        chunk.decode(encoding)
                        return True
                    except UnicodeDecodeError:
                        continue
                return False
                
        except (IOError, OSError) as e:
            logger.warning(f"Cannot access file {file_path}: {e}")
            return False
    
    def get_file_info(self, file_path: Path, stat_result: object = None) -> FileInfo:
        """Get file information with cached stat result.
        
        Args:
            file_path: Path to the file
            stat_result: Pre-computed stat result to avoid re-calling stat()
            
        Returns:
            FileInfo object with file metadata
        """
        try:
            # Use provided stat result or compute it
            if stat_result is None:
                stat_result = file_path.stat()
                
            size = stat_result.st_size
            modified = datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.utc).strftime('%Y-%m-%d')
            
            # Format size
            if size > 1048576:  # > 1MB
                size_fmt = f"{size/1048576:.1f}M"
            elif size > 1024:  # > 1KB
                size_fmt = f"{size/1024:.1f}K"
            else:
                size_fmt = f"{size}B"
                
            return FileInfo(
                path=file_path,
                relative_path=file_path.relative_to(self.root_dir),
                size=size,
                size_fmt=size_fmt,
                modified=modified,
                stat_result=stat_result
            )
        except (OSError, ValueError) as e:
            logger.warning(f"Cannot get file info for {file_path}: {e}")
            return FileInfo(
                path=file_path,
                relative_path=file_path.relative_to(self.root_dir),
                size=0,
                size_fmt='0B',
                modified='unknown',
                stat_result=None
            )
    
    def collect_files(self) -> list[FileInfo]:
        """Collect all files to process with cached stat results.
        
        Returns:
            List of FileInfo objects for files to extract
        """
        files = []
        total_size = 0
        
        # Use rglob with symlink safety
        try:
            for file_path in self.root_dir.rglob('*', case_sensitive=True):
                if not file_path.is_file():
                    continue
                    
                # Handle symlinks safely
                if file_path.is_symlink():
                    try:
                        # Check if symlink target is within root directory
                        resolved = file_path.resolve()
                        resolved.relative_to(self.root_dir.resolve())
                    except (ValueError, OSError):
                        logger.debug(f"Skipping symlink outside root: {file_path}")
                        continue
                
                if self.should_exclude_path(file_path):
                    continue
                
                # Get stat result once and reuse it
                try:
                    stat_result = file_path.stat()
                except (IOError, OSError) as e:
                    logger.warning(f"Cannot stat file {file_path}: {e}")
                    continue
                
                if self.is_text_file(file_path, stat_result):
                    file_size = stat_result.st_size
                    
                    # Check total size limit
                    if total_size + file_size > self.config.max_total_size:
                        logger.warning(f"Total size limit reached. Remaining files will be skipped.")
                        break
                    
                    file_info = self.get_file_info(file_path, stat_result)
                    files.append(file_info)
                    total_size += file_size
                else:
                    logger.debug(f"Skipping binary file: {file_path.relative_to(self.root_dir)}")
        
        except KeyboardInterrupt:
            logger.error("File collection interrupted by user")
            raise
        
        return sorted(files, key=lambda f: f.relative_path)
    
    def read_file_content(self, file_path: Path) -> str:
        """Read file content safely with optional redaction and folding.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File content as string, potentially redacted or collapsed
        """
        try:
            # Double-check file size (should already be validated)
            file_size = file_path.stat().st_size
            if file_size > self.config.max_file_size:
                return f"File too large ({file_size} bytes) - skipped for safety"
                
            # Try multiple encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
                except (IOError, OSError) as e:
                    return f"Error reading file: {e}"
            
            if content is None:
                return "Unable to decode file content with common encodings"
            
            # Redact sensitive content if this looks like a config file
            if self._is_sensitive_file(file_path):
                content = self._redact_sensitive_content(content)
            
            # Collapse large files if configured
            if self.config.collapse_large_files:
                content = self._collapse_large_content(content, file_path)
            
            # Ensure consistent newlines (single newline at end)
            content = content.rstrip() + '\n'
            
            return content
            
        except (IOError, OSError) as e:
            logger.error(f"File access error for {file_path}: {e}")
            return f"Error accessing file: {e}"
    
    def _is_sensitive_file(self, file_path: Path) -> bool:
        """Check if file might contain sensitive information."""
        filename = file_path.name.lower()
        extension = file_path.suffix.lower()
        
        # Only redact files with extensions that commonly contain key-value configs
        if extension not in self.config.redactable_extensions:
            return False
        
        # Check for sensitive file patterns or naming
        sensitive_indicators = ['env', 'secret', 'credential', 'key', 'password', 'auth']
        return any(indicator in filename for indicator in sensitive_indicators)
    
    def _redact_sensitive_content(self, content: str) -> str:
        """Redact sensitive key-value pairs from content."""
        lines = content.split('\n')
        redacted_lines = []
        redacted_count = 0
        
        # Create regex pattern for sensitive keys
        prefixes = '|'.join(re.escape(prefix) for prefix in self.config.sensitive_prefixes)
        pattern = re.compile(rf'^(\s*(?:{prefixes})[^=]*)\s*=.*$', re.IGNORECASE)
        
        for line in lines:
            # Skip comments and empty lines
            stripped = line.strip()
            if not stripped or stripped.startswith('#') or stripped.startswith(';'):
                redacted_lines.append(line)
                continue
            
            # Check for key=value patterns with sensitive keys
            match = pattern.match(line)
            if match:
                key_part = match.group(1)
                redacted_lines.append(f"{key_part}=***REDACTED***")
                redacted_count += 1
            else:
                redacted_lines.append(line)
        
        if redacted_count > 0:
            logger.info(f"Redacted {redacted_count} sensitive values")
        
        return '\n'.join(redacted_lines)
    
    def _collapse_large_content(self, content: str, file_path: Path) -> str:
        """Collapse large files to show only beginning."""
        lines = content.split('\n')
        
        if len(lines) <= self.config.collapse_threshold:
            return content
        
        # For markdown files, try to preserve structure
        if file_path.suffix.lower() == '.md':
            return self._collapse_markdown(lines, file_path)
        
        # For other files, show first N lines
        visible_lines = lines[:self.config.collapse_threshold]
        remaining = len(lines) - self.config.collapse_threshold
        
        collapse_notice = f"\n... [{remaining} more lines collapsed for brevity] ..."
        return '\n'.join(visible_lines) + collapse_notice
    
    def _collapse_markdown(self, lines: list[str], file_path: Path) -> str:
        """Intelligently collapse markdown files."""
        result_lines = []
        header_lines = []
        
        # Extract headers and first few paragraphs
        in_content = False
        content_lines = 0
        
        for line in lines:
            if line.startswith('#'):
                # Always include headers
                result_lines.append(line)
                header_lines.append(line)
                in_content = False
            elif line.strip() == '':
                result_lines.append(line)
            elif not in_content:
                # Include first paragraph after each header
                result_lines.append(line)
                in_content = True
                content_lines += 1
            elif content_lines < 3:
                result_lines.append(line)
                content_lines += 1
            else:
                # Start collapsing
                break
        
        if len(lines) > len(result_lines):
            remaining = len(lines) - len(result_lines)
            result_lines.append(f"\n... [Document continues with {remaining} more lines] ...")
            result_lines.append(f"Headers found: {len(header_lines)}")
            result_lines.append("[Use --no-collapse-large to see full content]")
            
        return '\n'.join(result_lines)
    
    def generate_table_of_contents(self, files: list[FileInfo]) -> str:
        """Generate a table of contents for the extracted files."""
        if not self.config.include_toc:
            return ""
        
        toc_lines = [
            "TABLE OF CONTENTS",
            "=" * 50,
            "",
            f"Total files: {len(files)}",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
        ]
        
        # Group files by directory for better organization
        dirs = defaultdict(list)
        
        for i, file_info in enumerate(files, 1):
            parent = str(file_info.relative_path.parent)
            if parent == '.':
                parent = '(root)'
            dirs[parent].append((i, file_info))
        
        # Generate organized TOC with per-directory numbering
        for directory in sorted(dirs.keys()):
            if directory != '(root)':
                toc_lines.append(f"\n📁 {directory}/")
            
            for local_num, (_, file_info) in enumerate(dirs[directory], 1):
                indent = "  " if directory != '(root)' else ""
                toc_lines.append(
                    f"{indent}{local_num:2d}. {file_info.relative_path.name} "
                    f"({file_info.size_fmt})"
                )
        
        toc_lines.extend(["", "=" * 50, ""])
        return '\n'.join(toc_lines)
    
    def create_file_header(self, file_info: FileInfo) -> str:
        """Create a header for a file section.
        
        Args:
            file_info: FileInfo object with file metadata
            
        Returns:
            Formatted header string
        """
        separator = "=" * 80
        path = str(file_info.relative_path)
        size = file_info.size_fmt
        modified = file_info.modified
        
        header = f"\n{separator}\n"
        header += f"FILE: {path}\n"
        header += f"SIZE: {size} | MODIFIED: {modified}"
        
        # Add collapse indicator if file would be collapsed
        if (self.config.collapse_large_files and 
            self._would_be_collapsed(file_info.path)):
            header += " | [COLLAPSED]"
        
        header += f"\n{separator}\n\n"
        return header
    
    def _would_be_collapsed(self, file_path: Path) -> bool:
        """Check if a file would be collapsed based on size."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = sum(1 for _ in f)
            return line_count > self.config.collapse_threshold
        except (IOError, OSError):
            return False
    
    def extract_files(self) -> None:
        """Extract all files to the output file."""
        logger.info(f"🔍 Scanning project directory: {self.root_dir}")
        
        try:
            files = self.collect_files()
        except KeyboardInterrupt:
            logger.error("Operation cancelled by user")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error collecting files: {e}")
            sys.exit(1)
        
        if not files:
            logger.warning("❌ No files found to extract")
            return
        
        logger.info(f"📝 Found {len(files)} text files to extract")
        logger.info(f"💾 Writing to: {self.output_file}")
        
        try:
            with open(self.output_file, 'w', encoding='utf-8') as output:
                # Write project header with UTC timestamp
                timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                project_header = f"""PROJECT FILES EXTRACTION
{'=' * 50}
Root Directory: {self.root_dir}
Extraction Date: {timestamp}
Total Files: {len(files)}
Max File Size: {self.config.max_file_size // (1024*1024)}MB
{'=' * 50}

This file contains the complete source code and documentation
for the project, with each file clearly marked with headers.

EXCLUDED DIRECTORIES: {', '.join(sorted(self.config.exclude_dirs))}
EXCLUDED EXTENSIONS: {', '.join(sorted(self.config.exclude_extensions))}
EXCLUDED PATTERNS: {', '.join(sorted(self.config.exclude_patterns))}
ENV PATTERNS: {', '.join(sorted(self.config.env_patterns))} (preserves .example/.template)
EXCLUDED FILES: Script itself, output file, previous extracts

"""
                output.write(project_header)
                
                # Add table of contents if enabled
                toc = self.generate_table_of_contents(files)
                if toc:
                    output.write(toc)
                    output.write("\n")
                
                # Process each file
                for i, file_info in enumerate(files, 1):
                    try:
                        logger.info(f"  [{i:3d}/{len(files)}] {file_info.relative_path} ({file_info.size_fmt})")
                        
                        # Write file header
                        header = self.create_file_header(file_info)
                        output.write(header)
                        
                        # Write file content
                        content = self.read_file_content(file_info.path)
                        output.write(content)
                        
                        # Add spacing between files
                        output.write("\n\n")
                        
                    except KeyboardInterrupt:
                        logger.error("Operation cancelled by user")
                        sys.exit(1)
                    except Exception as e:
                        logger.error(f"Error processing {file_info.path}: {e}")
                        continue
        
        except (IOError, OSError) as e:
            logger.error(f"❌ Error writing output file: {e}")
            sys.exit(1)
        
        logger.info(f"✅ Extraction complete! Output saved to: {self.output_file}")
        
        # Show output file size
        try:
            output_size = self.output_file.stat().st_size
            if output_size > 1048576:  # > 1MB
                size_fmt = f"{output_size/1048576:.1f}M"
            elif output_size > 1024:  # > 1KB
                size_fmt = f"{output_size/1024:.1f}K"
            else:
                size_fmt = f"{output_size}B"
            logger.info(f"📊 Output file size: {size_fmt}")
        except OSError:
            logger.warning("Could not determine output file size")


def main() -> None:
    """Main function to run the extractor."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract all project files to a single text file with headers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Extract current directory
  %(prog)s -r /path/to/project                # Extract specific directory
  %(prog)s -o my_export.txt                   # Custom output filename
  %(prog)s --exclude-pattern "*.log"          # Additional exclusions
  %(prog)s --skip-dotfiles --collapse-large   # Security & readability options
  %(prog)s --no-toc -v                        # No table of contents, verbose
        """
    )
    parser.add_argument(
        "--root", "-r",
        default=".",
        help="Root directory to scan (default: current directory)"
    )
    parser.add_argument(
        "--output", "-o",
        default="project_files.txt",
        help="Output file name (default: project_files.txt)"
    )
    parser.add_argument(
        "--exclude-pattern",
        action="append",
        dest="exclude_patterns",
        help="Additional file patterns to exclude (can be used multiple times)"
    )
    parser.add_argument(
        "--skip-dotfiles",
        action="store_true",
        help="Skip dotfiles (except .gitignore and .gitattributes)"
    )
    parser.add_argument(
        "--collapse-large",
        action="store_true", 
        help="Collapse large files to show only beginnings"
    )
    parser.add_argument(
        "--collapse-threshold",
        type=int,
        default=50,
        help="Line threshold for collapsing large files (default: 50, minimum: 5)"
    )
    parser.add_argument(
        "--no-toc",
        action="store_true",
        help="Skip generating table of contents"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output (debug level logging)"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Validate arguments
    root_path = Path(args.root)
    if not root_path.exists():
        logger.error(f"Root directory does not exist: {args.root}")
        sys.exit(1)
    
    if not root_path.is_dir():
        logger.error(f"Root path is not a directory: {args.root}")
        sys.exit(1)
    
    # Create configuration with CLI overrides
    config = ExtractorConfig()
    
    # Add additional exclude patterns from CLI
    if args.exclude_patterns:
        config.exclude_patterns.update(args.exclude_patterns)
        logger.info(f"Added exclusion patterns: {args.exclude_patterns}")
    
    # Apply CLI flags with validation
    config.skip_dotfiles = args.skip_dotfiles
    config.collapse_large_files = args.collapse_large
    config.collapse_threshold = max(5, args.collapse_threshold)  # Minimum threshold
    config.include_toc = not args.no_toc
    
    if args.collapse_threshold < 5:
        logger.warning(f"Collapse threshold adjusted to minimum value: 5 (was {args.collapse_threshold})")
    
    # Create and run extractor
    try:
        extractor = ProjectExtractor(args.root, args.output, config)
        extractor.extract_files()
    except KeyboardInterrupt:
        logger.error("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()