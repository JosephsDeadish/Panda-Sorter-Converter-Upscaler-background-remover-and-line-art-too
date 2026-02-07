"""
Statistics Tracking System
Provides real-time metrics, ETA calculations, and comprehensive reporting
Author: Dead On The Inside / JosephsDeadish
"""

import json
import csv
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class StatisticsTracker:
    """
    Real-time statistics tracker for texture processing operations.
    
    Features:
    - Live processing metrics
    - Smart ETA estimation with moving average
    - Category-based tracking
    - Error logging and recovery stats
    - Historical data persistence
    - Multi-format reporting (JSON, CSV, HTML)
    """
    
    def __init__(self, session_name: Optional[str] = None):
        """
        Initialize statistics tracker.
        
        Args:
            session_name: Optional name for this processing session
        """
        self.session_name = session_name or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = time.time()
        self.last_update_time = self.start_time
        
        # Core metrics
        self.total_files = 0
        self.processed_files = 0
        self.skipped_files = 0
        self.error_count = 0
        self.success_count = 0
        
        # Category tracking
        self.category_counts: Dict[str, int] = defaultdict(int)
        self.category_sizes: Dict[str, int] = defaultdict(int)
        
        # Error tracking
        self.errors: List[Dict[str, Any]] = []
        self.error_types: Dict[str, int] = defaultdict(int)
        
        # Performance tracking
        self.processing_times: deque = deque(maxlen=100)  # Last 100 processing times
        self.throughput_history: deque = deque(maxlen=60)  # Last 60 seconds
        
        # File size tracking
        self.total_bytes_processed = 0
        self.average_file_size = 0
        
        # Historical data
        self.history: List[Dict[str, Any]] = []
        self.checkpoints: List[Dict[str, Any]] = []
        
        logger.info(f"Statistics tracker initialized for session: {self.session_name}")
    
    def set_total_files(self, count: int) -> None:
        """
        Set the total number of files to process.
        
        Args:
            count: Total file count
        """
        self.total_files = count
        logger.debug(f"Total files set to: {count}")
    
    def record_file_processed(
        self,
        category: str,
        file_size: int,
        processing_time: float,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """
        Record a processed file with all metrics.
        
        Args:
            category: Category the file was sorted into
            file_size: Size of the file in bytes
            processing_time: Time taken to process in seconds
            success: Whether processing succeeded
            error: Error message if failed
        """
        self.processed_files += 1
        
        if success:
            self.success_count += 1
            self.category_counts[category] += 1
            self.category_sizes[category] += file_size
            self.total_bytes_processed += file_size
        else:
            self.error_count += 1
            if error:
                self.errors.append({
                    'timestamp': datetime.now().isoformat(),
                    'category': category,
                    'error': error,
                    'file_size': file_size
                })
                self.error_types[error] += 1
        
        # Update performance metrics
        self.processing_times.append(processing_time)
        self.last_update_time = time.time()
        
        # Update average file size
        if self.success_count > 0:
            self.average_file_size = self.total_bytes_processed // self.success_count
    
    def record_skipped(self) -> None:
        """Record a file that was skipped."""
        self.skipped_files += 1
        self.processed_files += 1
    
    def record_error(self, error_type: str, details: str, context: Optional[Dict] = None) -> None:
        """
        Record an error with context.
        
        Args:
            error_type: Type/category of error
            details: Detailed error message
            context: Additional context information
        """
        self.error_count += 1
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'details': details,
            'context': context or {}
        }
        self.errors.append(error_entry)
        self.error_types[error_type] += 1
        logger.error(f"Error recorded: {error_type} - {details}")
    
    def calculate_eta(self) -> Tuple[Optional[timedelta], float]:
        """
        Calculate estimated time to completion using smart estimation.
        
        Returns:
            Tuple of (ETA timedelta, current processing rate)
        """
        if self.processed_files == 0 or self.total_files == 0:
            return None, 0.0
        
        remaining = self.total_files - self.processed_files
        if remaining <= 0:
            return timedelta(0), 0.0
        
        # Calculate rate using moving average of recent processing times
        if len(self.processing_times) > 0:
            avg_time_per_file = sum(self.processing_times) / len(self.processing_times)
            rate = 1.0 / avg_time_per_file if avg_time_per_file > 0 else 0.0
        else:
            elapsed = time.time() - self.start_time
            rate = self.processed_files / elapsed if elapsed > 0 else 0.0
        
        if rate > 0:
            eta_seconds = remaining / rate
            return timedelta(seconds=int(eta_seconds)), rate
        
        return None, 0.0
    
    def get_progress_percentage(self) -> float:
        """
        Get current progress as percentage.
        
        Returns:
            Progress percentage (0-100)
        """
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100
    
    def get_throughput(self) -> Dict[str, float]:
        """
        Calculate current throughput metrics.
        
        Returns:
            Dictionary with files/sec and MB/sec
        """
        elapsed = time.time() - self.start_time
        
        if elapsed == 0:
            return {'files_per_second': 0.0, 'mb_per_second': 0.0}
        
        files_per_second = self.processed_files / elapsed
        mb_per_second = (self.total_bytes_processed / (1024 * 1024)) / elapsed
        
        return {
            'files_per_second': round(files_per_second, 2),
            'mb_per_second': round(mb_per_second, 2)
        }
    
    def create_checkpoint(self, label: Optional[str] = None) -> None:
        """
        Create a checkpoint of current statistics.
        
        Args:
            label: Optional label for this checkpoint
        """
        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'label': label or f"Checkpoint {len(self.checkpoints) + 1}",
            'processed': self.processed_files,
            'success': self.success_count,
            'errors': self.error_count,
            'elapsed': time.time() - self.start_time
        }
        self.checkpoints.append(checkpoint)
        logger.info(f"Checkpoint created: {checkpoint['label']}")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics summary.
        
        Returns:
            Dictionary containing all statistics
        """
        elapsed = time.time() - self.start_time
        eta, rate = self.calculate_eta()
        throughput = self.get_throughput()
        
        return {
            'session': {
                'name': self.session_name,
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'elapsed_seconds': round(elapsed, 2),
                'elapsed_formatted': str(timedelta(seconds=int(elapsed)))
            },
            'progress': {
                'total_files': self.total_files,
                'processed': self.processed_files,
                'success': self.success_count,
                'skipped': self.skipped_files,
                'errors': self.error_count,
                'percentage': round(self.get_progress_percentage(), 2),
                'remaining': self.total_files - self.processed_files
            },
            'performance': {
                'files_per_second': throughput['files_per_second'],
                'mb_per_second': throughput['mb_per_second'],
                'avg_processing_time': round(
                    sum(self.processing_times) / len(self.processing_times), 4
                ) if self.processing_times else 0.0,
                'eta_seconds': eta.total_seconds() if eta else None,
                'eta_formatted': str(eta) if eta else 'N/A'
            },
            'categories': {
                category: {
                    'count': count,
                    'size_bytes': self.category_sizes[category],
                    'size_mb': round(self.category_sizes[category] / (1024 * 1024), 2),
                    'percentage': round((count / self.success_count * 100), 2) if self.success_count > 0 else 0
                }
                for category, count in sorted(
                    self.category_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            },
            'data': {
                'total_bytes': self.total_bytes_processed,
                'total_mb': round(self.total_bytes_processed / (1024 * 1024), 2),
                'total_gb': round(self.total_bytes_processed / (1024 * 1024 * 1024), 3),
                'average_file_size_kb': round(self.average_file_size / 1024, 2)
            },
            'errors': {
                'total': self.error_count,
                'by_type': dict(self.error_types),
                'recent': self.errors[-10:] if self.errors else []
            }
        }
    
    def export_json(self, output_path: Path) -> None:
        """
        Export statistics to JSON format.
        
        Args:
            output_path: Path to save JSON file
        """
        try:
            summary = self.get_summary()
            summary['checkpoints'] = self.checkpoints
            summary['all_errors'] = self.errors
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Statistics exported to JSON: {output_path}")
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            raise
    
    def export_csv(self, output_path: Path) -> None:
        """
        Export statistics to CSV format.
        
        Args:
            output_path: Path to save CSV file
        """
        try:
            summary = self.get_summary()
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['PS2 Texture Sorter - Statistics Report'])
                writer.writerow(['Session', summary['session']['name']])
                writer.writerow(['Generated', datetime.now().isoformat()])
                writer.writerow([])
                
                # Progress section
                writer.writerow(['Progress'])
                writer.writerow(['Metric', 'Value'])
                for key, value in summary['progress'].items():
                    writer.writerow([key.replace('_', ' ').title(), value])
                writer.writerow([])
                
                # Performance section
                writer.writerow(['Performance'])
                writer.writerow(['Metric', 'Value'])
                for key, value in summary['performance'].items():
                    writer.writerow([key.replace('_', ' ').title(), value])
                writer.writerow([])
                
                # Categories section
                writer.writerow(['Categories'])
                writer.writerow(['Category', 'Count', 'Size (MB)', 'Percentage'])
                for category, data in summary['categories'].items():
                    writer.writerow([
                        category,
                        data['count'],
                        data['size_mb'],
                        f"{data['percentage']}%"
                    ])
                writer.writerow([])
                
                # Errors section
                if summary['errors']['total'] > 0:
                    writer.writerow(['Errors'])
                    writer.writerow(['Type', 'Count'])
                    for error_type, count in summary['errors']['by_type'].items():
                        writer.writerow([error_type, count])
            
            logger.info(f"Statistics exported to CSV: {output_path}")
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise
    
    def export_html(self, output_path: Path) -> None:
        """
        Export statistics to HTML format with styling.
        
        Args:
            output_path: Path to save HTML file
        """
        try:
            summary = self.get_summary()
            
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PS2 Texture Sorter - Statistics Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
            color: #e0e0e0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #252525;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        h1 {{
            color: #00ff88;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 0 2px 4px rgba(0, 255, 136, 0.3);
        }}
        h2 {{
            color: #00ccff;
            margin-top: 30px;
            margin-bottom: 15px;
            border-bottom: 2px solid #00ccff;
            padding-bottom: 8px;
        }}
        .meta {{
            color: #888;
            margin-bottom: 30px;
            font-size: 0.9em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #2d2d2d;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #00ff88;
        }}
        .stat-card.error {{
            border-left-color: #ff4444;
        }}
        .stat-card.warning {{
            border-left-color: #ffaa00;
        }}
        .stat-label {{
            color: #888;
            font-size: 0.85em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        .stat-value {{
            color: #fff;
            font-size: 2em;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #333;
        }}
        th {{
            background: #2d2d2d;
            color: #00ccff;
            font-weight: 600;
        }}
        tr:hover {{
            background: #2a2a2a;
        }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #1a1a1a;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #00ff88 0%, #00ccff 100%);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #000;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 PS2 Texture Sorter</h1>
        <div class="meta">
            <strong>Session:</strong> {summary['session']['name']}<br>
            <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>Duration:</strong> {summary['session']['elapsed_formatted']}
        </div>
        
        <h2>📊 Progress Overview</h2>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {summary['progress']['percentage']}%">
                {summary['progress']['percentage']:.1f}%
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Files</div>
                <div class="stat-value">{summary['progress']['total_files']:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Processed</div>
                <div class="stat-value">{summary['progress']['processed']:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Success</div>
                <div class="stat-value">{summary['progress']['success']:,}</div>
            </div>
            <div class="stat-card error">
                <div class="stat-label">Errors</div>
                <div class="stat-value">{summary['progress']['errors']:,}</div>
            </div>
        </div>
        
        <h2>⚡ Performance Metrics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Files/Second</div>
                <div class="stat-value">{summary['performance']['files_per_second']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">MB/Second</div>
                <div class="stat-value">{summary['performance']['mb_per_second']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">ETA</div>
                <div class="stat-value" style="font-size: 1.5em">{summary['performance']['eta_formatted']}</div>
            </div>
        </div>
        
        <h2>📁 Categories</h2>
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Files</th>
                    <th>Size (MB)</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody>
"""
            
            for category, data in summary['categories'].items():
                html += f"""                <tr>
                    <td>{category}</td>
                    <td>{data['count']:,}</td>
                    <td>{data['size_mb']:.2f}</td>
                    <td>{data['percentage']:.1f}%</td>
                </tr>
"""
            
            html += f"""            </tbody>
        </table>
        
        <h2>💾 Data Summary</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Processed</div>
                <div class="stat-value">{summary['data']['total_gb']:.2f} GB</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Average File Size</div>
                <div class="stat-value">{summary['data']['average_file_size_kb']:.0f} KB</div>
            </div>
        </div>
"""
            
            if summary['errors']['total'] > 0:
                html += f"""
        <h2>⚠️ Errors</h2>
        <table>
            <thead>
                <tr>
                    <th>Error Type</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
"""
                for error_type, count in summary['errors']['by_type'].items():
                    html += f"""                <tr>
                    <td>{error_type}</td>
                    <td>{count}</td>
                </tr>
"""
                html += """            </tbody>
        </table>
"""
            
            html += """    </div>
</body>
</html>
"""
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            logger.info(f"Statistics exported to HTML: {output_path}")
        except Exception as e:
            logger.error(f"Failed to export HTML: {e}")
            raise
    
    def __str__(self) -> str:
        """String representation of current statistics."""
        eta, rate = self.calculate_eta()
        return (
            f"StatisticsTracker(session={self.session_name}, "
            f"progress={self.processed_files}/{self.total_files}, "
            f"success={self.success_count}, errors={self.error_count}, "
            f"eta={eta})"
        )
