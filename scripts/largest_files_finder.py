#!/usr/bin/env python3
"""
Largest Files Finder
Analyze and identify the largest files in a project directory.
Similar exclusion logic to project_extractor.py but focused on size analysis.
"""

import logging
import sys
import json
import csv
import fnmatch
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict
from typing import List, Dict, Tuple, Optional, Any


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Size constants
MB = 1024 * 1024
GB = 1024 * MB


@dataclass
class FileInfo:
    """Enhanced file information with size analysis."""
    path: Path
    relative_path: Path
    size: int
    size_fmt: str
    modified: str
    file_type: str
    extension: str
    stat_result: object
    size_category: str = field(init=False)
    
    def __post_init__(self):
        """Categorize file size."""
        if self.size >= GB:
            self.size_category = "huge"
        elif self.size >= 100 * MB:
            self.size_category = "very_large"
        elif self.size >= 10 * MB:
            self.size_category = "large"
        elif self.size >= MB:
            self.size_category = "medium"
        elif self.size >= 100 * 1024:
            self.size_category = "small"
        else:
            self.size_category = "tiny"


@dataclass
class DirectoryInfo:
    """Directory size information."""
    path: Path
    relative_path: Path
    total_size: int
    file_count: int
    largest_file: Optional[FileInfo] = None
    
    @property
    def size_fmt(self) -> str:
        """Human-readable size format."""
        return format_size(self.total_size)
    
    @property
    def avg_file_size(self) -> int:
        """Average file size in directory."""
        return self.total_size // self.file_count if self.file_count > 0 else 0


@dataclass
class AnalysisConfig:
    """Configuration for file analysis."""
    exclude_dirs: set[str] = field(default_factory=lambda: {
        ".venv", ".benchmarks", ".cursor", ".pytest_cache", "build",
        ".git", "node_modules", ".mypy_cache", ".ruff_cache", "logs", "__pycache__"
    })
    exclude_extensions: set[str] = field(default_factory=lambda: {
        ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bin"
    })
    exclude_patterns: set[str] = field(default_factory=lambda: {
        "*.pem", "*.p12", "*.jks", "*.pfx", "*.crt", "*.cer",
        "uv.lock", "package-lock.json", "yarn.lock", "Pipfile.lock", "poetry.lock"
    })
    env_patterns: set[str] = field(default_factory=lambda: {
        ".env", ".env.*"
    })
    
    # Analysis options
    include_binary: bool = False
    include_hidden: bool = False
    min_size_bytes: int = 0
    max_results: int = 100
    
    # Output options
    show_percentages: bool = True
    show_directory_breakdown: bool = True
    show_type_breakdown: bool = True
    
    # Size thresholds for categorization
    large_file_threshold: int = 10 * MB
    huge_file_threshold: int = 100 * MB


class LargestFilesFinder:
    """Analyze and find the largest files in a project."""
    
    def __init__(self, root_dir: str = ".", config: AnalysisConfig = None):
        """Initialize the finder.
        
        Args:
            root_dir: Root directory to scan
            config: Analysis configuration
        """
        self.root_dir = Path(root_dir).resolve()
        self.config = config or AnalysisConfig()
        
        # Get script file path to exclude it
        self.script_file = Path(__file__).resolve() if __file__ else None
        
    def validate_path_safety(self, path: Path) -> bool:
        """Prevent path traversal attacks."""
        try:
            path.resolve().relative_to(self.root_dir.resolve())
            return True
        except ValueError:
            logger.warning(f"Blocked path traversal attempt: {path}")
            return False
    
    def should_exclude_path(self, path: Path) -> bool:
        """Check if a path should be excluded."""
        if not self.validate_path_safety(path):
            return True
        
        # Exclude script file itself
        if self.script_file and path.resolve() == self.script_file:
            return True
        
        filename = path.name.lower()
        
        # Handle .env files
        for env_pattern in self.config.env_patterns:
            if fnmatch.fnmatch(filename, env_pattern.lower()):
                if not any(preserve in filename for preserve in ['.example', '.template', '.sample']):
                    return True
        
        # Check exclude patterns
        for pattern in self.config.exclude_patterns:
            if fnmatch.fnmatch(filename, pattern.lower()):
                return True
        
        # Skip hidden files if not included
        if not self.config.include_hidden and filename.startswith('.') and filename not in {'.gitignore', '.gitattributes'}:
            return True
        
        # Check excluded directories
        for part in path.parts:
            if part in self.config.exclude_dirs:
                return True
        
        # Check file extension
        if not self.config.include_binary and path.suffix.lower() in self.config.exclude_extensions:
            return True
        
        return False
    
    def get_file_type(self, file_path: Path) -> str:
        """Determine file type based on extension and content."""
        extension = file_path.suffix.lower()
        
        # Programming languages
        if extension in {'.py', '.pyx', '.pyi'}:
            return 'Python'
        elif extension in {'.js', '.mjs', '.jsx'}:
            return 'JavaScript'
        elif extension in {'.ts', '.tsx'}:
            return 'TypeScript'
        elif extension in {'.java', '.class'}:
            return 'Java'
        elif extension in {'.c', '.h'}:
            return 'C'
        elif extension in {'.cpp', '.cc', '.cxx', '.hpp'}:
            return 'C++'
        elif extension in {'.rs'}:
            return 'Rust'
        elif extension in {'.go'}:
            return 'Go'
        
        # Data formats
        elif extension in {'.json', '.jsonl'}:
            return 'JSON'
        elif extension in {'.xml'}:
            return 'XML'
        elif extension in {'.yaml', '.yml'}:
            return 'YAML'
        elif extension in {'.csv'}:
            return 'CSV'
        elif extension in {'.sql'}:
            return 'SQL'
        
        # Documentation
        elif extension in {'.md', '.markdown'}:
            return 'Markdown'
        elif extension in {'.txt', '.text'}:
            return 'Text'
        elif extension in {'.rst'}:
            return 'reStructuredText'
        elif extension in {'.html', '.htm'}:
            return 'HTML'
        
        # Config files
        elif extension in {'.toml'}:
            return 'TOML'
        elif extension in {'.ini', '.cfg', '.conf'}:
            return 'Config'
        elif extension in {'.env'}:
            return 'Environment'
        
        # Archives
        elif extension in {'.zip', '.tar', '.gz', '.bz2', '.xz', '.7z'}:
            return 'Archive'
        
        # Images
        elif extension in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico'}:
            return 'Image'
        
        # Binary/executables
        elif extension in {'.exe', '.dll', '.so', '.dylib', '.bin'}:
            return 'Binary'
        
        # Logs
        elif extension in {'.log', '.logs'}:
            return 'Log'
        
        elif extension == '':
            return 'No Extension'
        else:
            return f'Other ({extension})'
    
    def is_binary_file(self, file_path: Path) -> bool:
        """Check if file is binary."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
            return b'\x00' in chunk
        except (IOError, OSError):
            return True  # Assume binary if can't read
    
    def collect_files(self) -> List[FileInfo]:
        """Collect all files with their metadata."""
        files = []
        
        try:
            for file_path in self.root_dir.rglob('*'):
                if not file_path.is_file():
                    continue
                
                # Handle symlinks safely
                if file_path.is_symlink():
                    try:
                        resolved = file_path.resolve()
                        resolved.relative_to(self.root_dir.resolve())
                    except (ValueError, OSError):
                        continue
                
                if self.should_exclude_path(file_path):
                    continue
                
                # Get file stats
                try:
                    stat_result = file_path.stat()
                except (IOError, OSError) as e:
                    logger.warning(f"Cannot stat file {file_path}: {e}")
                    continue
                
                file_size = stat_result.st_size
                
                # Apply minimum size filter
                if file_size < self.config.min_size_bytes:
                    continue
                
                # Skip binary files if not included
                if not self.config.include_binary and self.is_binary_file(file_path):
                    continue
                
                # Create file info
                file_info = FileInfo(
                    path=file_path,
                    relative_path=file_path.relative_to(self.root_dir),
                    size=file_size,
                    size_fmt=format_size(file_size),
                    modified=datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.utc).strftime('%Y-%m-%d'),
                    file_type=self.get_file_type(file_path),
                    extension=file_path.suffix.lower(),
                    stat_result=stat_result
                )
                
                files.append(file_info)
        
        except KeyboardInterrupt:
            logger.error("File collection interrupted by user")
            raise
        
        return files
    
    def analyze_directories(self, files: List[FileInfo]) -> List[DirectoryInfo]:
        """Analyze directory sizes."""
        dir_stats = defaultdict(lambda: {'size': 0, 'count': 0, 'files': []})
        
        for file_info in files:
            parent = file_info.relative_path.parent
            dir_stats[parent]['size'] += file_info.size
            dir_stats[parent]['count'] += 1
            dir_stats[parent]['files'].append(file_info)
        
        directories = []
        for dir_path, stats in dir_stats.items():
            largest_file = max(stats['files'], key=lambda f: f.size) if stats['files'] else None
            
            dir_info = DirectoryInfo(
                path=self.root_dir / dir_path,
                relative_path=dir_path,
                total_size=stats['size'],
                file_count=stats['count'],
                largest_file=largest_file
            )
            directories.append(dir_info)
        
        return sorted(directories, key=lambda d: d.total_size, reverse=True)
    
    def analyze_by_type(self, files: List[FileInfo]) -> Dict[str, Dict[str, Any]]:
        """Analyze files by type."""
        type_stats = defaultdict(lambda: {'size': 0, 'count': 0, 'files': []})
        
        for file_info in files:
            file_type = file_info.file_type
            type_stats[file_type]['size'] += file_info.size
            type_stats[file_type]['count'] += 1
            type_stats[file_type]['files'].append(file_info)
        
        # Calculate percentages and largest files
        total_size = sum(stats['size'] for stats in type_stats.values())
        
        result = {}
        for file_type, stats in type_stats.items():
            largest_file = max(stats['files'], key=lambda f: f.size)
            result[file_type] = {
                'total_size': stats['size'],
                'size_fmt': format_size(stats['size']),
                'count': stats['count'],
                'percentage': (stats['size'] / total_size * 100) if total_size > 0 else 0,
                'avg_size': stats['size'] // stats['count'],
                'avg_size_fmt': format_size(stats['size'] // stats['count']),
                'largest_file': largest_file
            }
        
        return dict(sorted(result.items(), key=lambda x: x[1]['total_size'], reverse=True))
    
    def generate_report(self, files: List[FileInfo]) -> str:
        """Generate comprehensive analysis report."""
        if not files:
            return "No files found matching criteria."
        
        # Sort files by size
        files_by_size = sorted(files, key=lambda f: f.size, reverse=True)
        
        # Calculate totals
        total_size = sum(f.size for f in files)
        total_files = len(files)
        
        # Limit results
        top_files = files_by_size[:self.config.max_results]
        
        # Generate report sections
        report_lines = [
            "LARGEST FILES ANALYSIS",
            "=" * 80,
            f"Root Directory: {self.root_dir}",
            f"Analysis Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Total Files Analyzed: {total_files:,}",
            f"Total Size: {format_size(total_size)}",
            f"Average File Size: {format_size(total_size // total_files) if total_files > 0 else '0B'}",
            "",
        ]
        
        # File size distribution
        size_categories = defaultdict(int)
        for file_info in files:
            size_categories[file_info.size_category] += 1
        
        report_lines.extend([
            "FILE SIZE DISTRIBUTION:",
            "-" * 40,
        ])
        
        category_order = ["huge", "very_large", "large", "medium", "small", "tiny"]
        category_names = {
            "huge": f"Huge (≥{format_size(GB)})",
            "very_large": f"Very Large (≥{format_size(100 * MB)})",
            "large": f"Large (≥{format_size(10 * MB)})",
            "medium": f"Medium (≥{format_size(MB)})",
            "small": f"Small (≥{format_size(100 * 1024)})",
            "tiny": "Tiny (< 100KB)"
        }
        
        for category in category_order:
            count = size_categories[category]
            if count > 0:
                percentage = (count / total_files * 100) if total_files > 0 else 0
                report_lines.append(f"  {category_names[category]}: {count:,} files ({percentage:.1f}%)")
        
        report_lines.append("")
        
        # Top largest files
        report_lines.extend([
            f"TOP {len(top_files)} LARGEST FILES:",
            "-" * 80,
        ])
        
        for i, file_info in enumerate(top_files, 1):
            percentage = (file_info.size / total_size * 100) if total_size > 0 else 0
            report_lines.append(
                f"{i:3d}. {file_info.size_fmt:>8} ({percentage:5.1f}%) "
                f"{file_info.relative_path} [{file_info.file_type}]"
            )
        
        # Directory breakdown
        if self.config.show_directory_breakdown:
            directories = self.analyze_directories(files)
            top_dirs = directories[:20]  # Top 20 directories
            
            report_lines.extend([
                "",
                "TOP DIRECTORIES BY SIZE:",
                "-" * 80,
            ])
            
            for i, dir_info in enumerate(top_dirs, 1):
                percentage = (dir_info.total_size / total_size * 100) if total_size > 0 else 0
                dir_path = str(dir_info.relative_path) if str(dir_info.relative_path) != '.' else '(root)'
                report_lines.append(
                    f"{i:2d}. {dir_info.size_fmt:>8} ({percentage:5.1f}%) "
                    f"{dir_path} ({dir_info.file_count} files)"
                )
        
        # File type breakdown
        if self.config.show_type_breakdown:
            type_analysis = self.analyze_by_type(files)
            
            report_lines.extend([
                "",
                "FILE TYPES BY SIZE:",
                "-" * 80,
            ])
            
            for i, (file_type, stats) in enumerate(type_analysis.items(), 1):
                if i > 15:  # Limit to top 15 types
                    break
                report_lines.append(
                    f"{i:2d}. {stats['size_fmt']:>8} ({stats['percentage']:5.1f}%) "
                    f"{file_type} ({stats['count']} files, avg: {stats['avg_size_fmt']})"
                )
        
        return '\n'.join(report_lines)
    
    def export_csv(self, files: List[FileInfo], output_file: str) -> None:
        """Export results to CSV."""
        files_by_size = sorted(files, key=lambda f: f.size, reverse=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'Rank', 'Size_Bytes', 'Size_Formatted', 'Relative_Path', 
                'File_Type', 'Extension', 'Modified_Date', 'Size_Category'
            ])
            
            for i, file_info in enumerate(files_by_size, 1):
                writer.writerow([
                    i, file_info.size, file_info.size_fmt,
                    str(file_info.relative_path), file_info.file_type,
                    file_info.extension, file_info.modified, file_info.size_category
                ])
    
    def export_json(self, files: List[FileInfo], output_file: str) -> None:
        """Export results to JSON."""
        files_by_size = sorted(files, key=lambda f: f.size, reverse=True)
        
        data = {
            'analysis_date': datetime.now(timezone.utc).isoformat(),
            'root_directory': str(self.root_dir),
            'total_files': len(files),
            'total_size': sum(f.size for f in files),
            'files': []
        }
        
        for i, file_info in enumerate(files_by_size, 1):
            data['files'].append({
                'rank': i,
                'size_bytes': file_info.size,
                'size_formatted': file_info.size_fmt,
                'relative_path': str(file_info.relative_path),
                'file_type': file_info.file_type,
                'extension': file_info.extension,
                'modified_date': file_info.modified,
                'size_category': file_info.size_category
            })
        
        with open(output_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
    
    def analyze(self) -> Tuple[List[FileInfo], str]:
        """Run the analysis and return files and report."""
        logger.info(f"🔍 Scanning directory: {self.root_dir}")
        
        try:
            files = self.collect_files()
        except KeyboardInterrupt:
            logger.error("Operation cancelled by user")
            sys.exit(1)
        
        if not files:
            logger.warning("❌ No files found matching criteria")
            return [], "No files found matching criteria."
        
        logger.info(f"📊 Analyzing {len(files)} files...")
        report = self.generate_report(files)
        
        return files, report


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes >= GB:
        return f"{size_bytes / GB:.1f}G"
    elif size_bytes >= MB:
        return f"{size_bytes / MB:.1f}M"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f}K"
    else:
        return f"{size_bytes}B"


def main() -> None:
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Find and analyze the largest files in a project directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Analyze current directory
  %(prog)s -r /path/to/project                # Analyze specific directory
  %(prog)s --top 50                           # Show top 50 files
  %(prog)s --min-size 1M                      # Only files >= 1MB
  %(prog)s --include-binary --include-hidden  # Include all files
  %(prog)s --export-csv results.csv           # Export to CSV
  %(prog)s --export-json results.json         # Export to JSON
        """
    )
    
    parser.add_argument(
        "--root", "-r",
        default=".",
        help="Root directory to analyze (default: current directory)"
    )
    parser.add_argument(
        "--top", "-t",
        type=int,
        default=100,
        help="Number of largest files to show (default: 100)"
    )
    parser.add_argument(
        "--min-size",
        default="0",
        help="Minimum file size (e.g., 1M, 500K, 1G) - default: 0"
    )
    parser.add_argument(
        "--include-binary",
        action="store_true",
        help="Include binary files in analysis"
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files (dotfiles)"
    )
    parser.add_argument(
        "--no-directories",
        action="store_true",
        help="Skip directory breakdown"
    )
    parser.add_argument(
        "--no-types",
        action="store_true",
        help="Skip file type breakdown"
    )
    parser.add_argument(
        "--export-csv",
        help="Export results to CSV file"
    )
    parser.add_argument(
        "--export-json",
        help="Export results to JSON file"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Parse minimum size
    min_size_bytes = 0
    if args.min_size and args.min_size != "0":
        size_str = args.min_size.upper()
        multiplier = 1
        if size_str.endswith('K'):
            multiplier = 1024
            size_str = size_str[:-1]
        elif size_str.endswith('M'):
            multiplier = MB
            size_str = size_str[:-1]
        elif size_str.endswith('G'):
            multiplier = GB
            size_str = size_str[:-1]
        
        try:
            min_size_bytes = int(float(size_str) * multiplier)
        except ValueError:
            logger.error(f"Invalid size format: {args.min_size}")
            sys.exit(1)
    
    # Validate root directory
    root_path = Path(args.root)
    if not root_path.exists():
        logger.error(f"Directory does not exist: {args.root}")
        sys.exit(1)
    
    if not root_path.is_dir():
        logger.error(f"Path is not a directory: {args.root}")
        sys.exit(1)
    
    # Create configuration
    config = AnalysisConfig(
        include_binary=args.include_binary,
        include_hidden=args.include_hidden,
        min_size_bytes=min_size_bytes,
        max_results=args.top,
        show_directory_breakdown=not args.no_directories,
        show_type_breakdown=not args.no_types
    )
    
    # Run analysis
    try:
        finder = LargestFilesFinder(args.root, config)
        files, report = finder.analyze()
        
        # Print report
        print(report)
        
        # Export if requested
        if args.export_csv:
            finder.export_csv(files, args.export_csv)
            logger.info(f"📄 Results exported to CSV: {args.export_csv}")
        
        if args.export_json:
            finder.export_json(files, args.export_json)
            logger.info(f"📄 Results exported to JSON: {args.export_json}")
            
    except KeyboardInterrupt:
        logger.error("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 