"""
CLI Interface - Command Line Interface for Game Texture Sorter
Supports batch processing and automation workflows
Author: Dead On The Inside / JosephsDeadish
"""

import sys
import argparse
import logging
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

try:
    from ..config import APP_NAME, APP_VERSION, APP_AUTHOR, config
    from .config_loader import ConfigLoader
except ImportError:
    from config import APP_NAME, APP_VERSION, APP_AUTHOR, config  # type: ignore[no-redef]
    from cli.config_loader import ConfigLoader  # type: ignore[no-redef]

logger = logging.getLogger(__name__)



class CLIInterface:
    """Command-line interface for Game Texture Sorter."""
    
    def __init__(self):
        """Initialize CLI interface."""
        self.config_loader = ConfigLoader()
        self.parser = self._create_parser()
        self.exit_code = 0
        
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser with all CLI options."""
        parser = argparse.ArgumentParser(
            prog=APP_NAME,
            description=f'{APP_NAME} v{APP_VERSION} - Batch texture sorting tool',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=f"""
Examples:
  {APP_NAME} --cli --input ./textures --output ./sorted
  {APP_NAME} --cli --input ./textures --profile game_preset.json
  {APP_NAME} --cli --config batch_config.json
  {APP_NAME} --version

Author: {APP_AUTHOR}
"""
        )
        
        # Version info
        parser.add_argument(
            '--version',
            action='version',
            version=f'{APP_NAME} v{APP_VERSION}'
        )
        
        # CLI mode flag
        parser.add_argument(
            '--cli',
            action='store_true',
            help='Run in command-line mode (no GUI)'
        )
        
        # Input/Output paths
        parser.add_argument(
            '--input', '-i',
            type=str,
            help='Input directory containing textures'
        )
        
        parser.add_argument(
            '--output', '-o',
            type=str,
            help='Output directory for sorted textures'
        )
        
        # Configuration files
        parser.add_argument(
            '--config', '-c',
            type=str,
            help='Path to JSON configuration file'
        )
        
        parser.add_argument(
            '--profile', '-p',
            type=str,
            help='Path to organization profile JSON'
        )
        
        # Processing options
        parser.add_argument(
            '--recursive', '-r',
            action='store_true',
            help='Process subdirectories recursively'
        )
        
        parser.add_argument(
            '--style',
            type=str,
            choices=['by_category', 'by_type', 'by_size', 'flat', 'custom'],
            default='by_category',
            help='Organization style (default: by_category)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate processing without moving files'
        )
        
        parser.add_argument(
            '--no-backup',
            action='store_true',
            help='Skip creating backup of original files'
        )
        
        # Output options
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        
        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Suppress all output except errors'
        )
        
        parser.add_argument(
            '--progress',
            choices=['bar', 'percent', 'none'],
            default='bar',
            help='Progress display style (default: bar)'
        )
        
        parser.add_argument(
            '--log-file',
            type=str,
            help='Write logs to specified file'
        )
        
        # Batch processing
        parser.add_argument(
            '--batch',
            type=str,
            nargs='+',
            help='Process multiple input directories'
        )
        
        parser.add_argument(
            '--report',
            type=str,
            help='Generate processing report to specified file'
        )
        
        return parser
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run CLI interface.
        
        Args:
            args: Command line arguments (uses sys.argv if None)
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            parsed_args = self.parser.parse_args(args)
            
            # Configure logging
            self._setup_logging(parsed_args)
            
            # Check if CLI mode is requested
            if not parsed_args.cli:
                logger.info("CLI mode not requested, launching GUI")
                return 0  # Let main.py handle GUI launch
            
            logger.info(f"Starting {APP_NAME} v{APP_VERSION} in CLI mode")
            
            # Load configuration if specified
            config_data = {}
            if parsed_args.config:
                config_data = self.config_loader.load_config(parsed_args.config)
                if not config_data:
                    logger.error(f"Failed to load config: {parsed_args.config}")
                    return 1
            
            # Load profile if specified
            profile_data = {}
            if parsed_args.profile:
                profile_data = self.config_loader.load_profile(parsed_args.profile)
                if not profile_data:
                    logger.error(f"Failed to load profile: {parsed_args.profile}")
                    return 1
            
            # Process batch or single directory
            if parsed_args.batch:
                return self._process_batch(parsed_args, config_data, profile_data)
            else:
                return self._process_single(parsed_args, config_data, profile_data)
                
        except KeyboardInterrupt:
            logger.warning("Processing interrupted by user")
            return 130  # Standard SIGINT exit code
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return 1
    
    def _setup_logging(self, args: argparse.Namespace) -> None:
        """Configure logging based on CLI arguments."""
        level = logging.WARNING
        
        if args.verbose:
            level = logging.DEBUG
        elif args.quiet:
            level = logging.ERROR
        else:
            level = logging.INFO
        
        # Configure root logger
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add file handler if specified
        if args.log_file:
            try:
                file_handler = logging.FileHandler(args.log_file)
                file_handler.setLevel(level)
                file_handler.setFormatter(
                    logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )
                )
                logging.getLogger().addHandler(file_handler)
                logger.info(f"Logging to file: {args.log_file}")
            except Exception as e:
                logger.error(f"Failed to create log file: {e}")
    
    def _process_single(
        self,
        args: argparse.Namespace,
        config_data: Dict[str, Any],
        profile_data: Dict[str, Any]
    ) -> int:
        """
        Process a single input directory.
        
        Args:
            args: Parsed command line arguments
            config_data: Loaded configuration data
            profile_data: Loaded profile data
            
        Returns:
            Exit code (0 for success)
        """
        # Validate required arguments
        if not args.input:
            logger.error("--input directory is required in CLI mode")
            return 1
        
        if not args.output:
            logger.error("--output directory is required in CLI mode")
            return 1
        
        input_path = Path(args.input)
        output_path = Path(args.output)
        
        if not input_path.exists():
            logger.error(f"Input directory does not exist: {input_path}")
            return 1
        
        if not input_path.is_dir():
            logger.error(f"Input path is not a directory: {input_path}")
            return 1
        
        # Display processing info
        if not args.quiet:
            print(f"\n{APP_NAME} v{APP_VERSION}")
            print(f"{'=' * 60}")
            print(f"Input:  {input_path}")
            print(f"Output: {output_path}")
            print(f"Style:  {args.style}")
            print(f"Dry Run: {args.dry_run}")
            print(f"{'=' * 60}\n")
        
        try:
            # Import processing modules
            from ..classifier import TextureClassifier
            from ..organizer import OrganizationEngine, ORGANIZATION_STYLES
            from ..file_handler import FileHandler
            
            # Initialize components
            logger.info("Initializing processing components...")
            classifier = TextureClassifier(config=config)
            file_handler = FileHandler(config=config)
            
            # Map CLI style names to organization style classes
            # - by_category: Simple category-based organization (minimalist)
            # - by_type: Module-based organization (modular: characters/vehicles/environment)
            # - by_size: Flat organization optimized for size-based sorting
            # - flat: Direct flat organization without deep hierarchy (same as by_size)
            # - custom: User-defined custom hierarchy
            # Note: 'by_size' and 'flat' both map to 'flat' style - this overlap is intentional
            #       to provide intuitive CLI options for users
            style_map = {
                'by_category': 'minimalist',
                'by_type': 'modular',
                'by_size': 'flat',
                'flat': 'flat',
                'custom': 'custom'
            }
            
            # Get the appropriate style class
            style_key = style_map.get(args.style, 'flat')
            style_class = ORGANIZATION_STYLES.get(style_key, ORGANIZATION_STYLES['flat'])
            
            # Initialize organizer with proper parameters
            organizer = OrganizationEngine(
                style_class=style_class,
                output_dir=str(output_path),
                dry_run=args.dry_run
            )
            
            # Scan for textures
            logger.info(f"Scanning for textures in {input_path}...")
            texture_files = self._scan_textures(
                input_path,
                recursive=args.recursive
            )
            
            if not texture_files:
                logger.warning("No texture files found")
                return 0
            
            total_files = len(texture_files)
            logger.info(f"Found {total_files} texture files")
            
            if not args.quiet:
                print(f"Found {total_files} texture files\n")
            
            # Process textures with progress display
            results = self._process_textures(
                texture_files,
                output_path,
                classifier,
                organizer,
                args
            )
            
            # Display summary
            if not args.quiet:
                self._display_summary(results)
            
            # Generate report if requested
            if args.report:
                self._generate_report(results, args.report)
            
            return 0 if results['errors'] == 0 else 1
            
        except Exception as e:
            logger.error(f"Processing failed: {e}", exc_info=True)
            return 1
    
    def _process_batch(
        self,
        args: argparse.Namespace,
        config_data: Dict[str, Any],
        profile_data: Dict[str, Any]
    ) -> int:
        """
        Process multiple input directories in batch mode.
        
        Args:
            args: Parsed command line arguments
            config_data: Loaded configuration data
            profile_data: Loaded profile data
            
        Returns:
            Exit code (0 if all succeeded)
        """
        if not args.output:
            logger.error("--output directory is required for batch processing")
            return 1
        
        output_base = Path(args.output)
        all_results = []
        
        logger.info(f"Batch processing {len(args.batch)} directories")
        
        for idx, input_dir in enumerate(args.batch, 1):
            input_path = Path(input_dir)
            
            if not input_path.exists():
                logger.error(f"Skipping non-existent directory: {input_path}")
                continue
            
            # Create subdirectory in output for each input
            output_path = output_base / input_path.name
            
            if not args.quiet:
                print(f"\n[{idx}/{len(args.batch)}] Processing: {input_path}")
            
            # Create temporary args for single processing
            single_args = argparse.Namespace(**vars(args))
            single_args.input = str(input_path)
            single_args.output = str(output_path)
            single_args.batch = None
            
            result = self._process_single(single_args, config_data, profile_data)
            all_results.append(result)
        
        # Return 0 only if all succeeded
        return 0 if all(r == 0 for r in all_results) else 1
    
    def _scan_textures(
        self,
        directory: Path,
        recursive: bool = False
    ) -> List[Path]:
        """
        Scan directory for texture files.
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List of texture file paths
        """
        extensions = {'.dds', '.png', '.jpg', '.jpeg', '.bmp', '.tga', '.tif', '.tiff'}
        texture_files = []
        
        if recursive:
            for ext in extensions:
                texture_files.extend(directory.rglob(f'*{ext}'))
                texture_files.extend(directory.rglob(f'*{ext.upper()}'))
        else:
            for ext in extensions:
                texture_files.extend(directory.glob(f'*{ext}'))
                texture_files.extend(directory.glob(f'*{ext.upper()}'))
        
        return sorted(texture_files)
    
    def _process_textures(
        self,
        texture_files: List[Path],
        output_path: Path,
        classifier: Any,
        organizer: Any,
        args: argparse.Namespace
    ) -> Dict[str, Any]:
        """
        Process texture files with progress display.
        
        Args:
            texture_files: List of texture files to process
            output_path: Output directory
            classifier: Texture classifier instance
            organizer: Organization engine instance
            args: CLI arguments
            
        Returns:
            Dictionary with processing results
        """
        results = {
            'total': len(texture_files),
            'processed': 0,
            'errors': 0,
            'skipped': 0,
            'start_time': datetime.now(),
            'files': []
        }
        
        # Display progress based on style
        show_progress = not args.quiet and args.progress != 'none'
        
        try:
            from tqdm import tqdm
            use_tqdm = args.progress == 'bar' and show_progress
        except ImportError:
            use_tqdm = False
        
        iterator = tqdm(texture_files, desc="Processing") if use_tqdm else texture_files
        
        for idx, texture_file in enumerate(iterator, 1):
            try:
                # Process texture (simplified for CLI)
                file_result = {
                    'file': str(texture_file),
                    'status': 'success',
                    'category': 'unknown'
                }
                
                if not args.dry_run:
                    # Classify the texture
                    if classifier is not None:
                        try:
                            predictions = classifier.classify_texture(texture_file)
                            if predictions:
                                top = predictions[0]
                                file_result['category'] = top.get('category', 'unclassified')
                                file_result['confidence'] = top.get('confidence', 0.0)
                        except Exception as classify_err:
                            logger.debug(f"Classification failed for {texture_file}: {classify_err}")

                    # Organise (move/copy) the texture into the output directory
                    if organizer is not None:
                        try:
                            category = file_result.get('category', 'unclassified')
                            dest_folder = output_path / category
                            dest_folder.mkdir(parents=True, exist_ok=True)
                            dest_file = dest_folder / texture_file.name
                            if not dest_file.exists():
                                shutil.copy2(texture_file, dest_file)
                                file_result['destination'] = str(dest_file)
                        except Exception as org_err:
                            logger.debug(f"Organisation failed for {texture_file}: {org_err}")
                
                results['processed'] += 1
                results['files'].append(file_result)
                
                # Update progress for percent display
                if not use_tqdm and show_progress and args.progress == 'percent':
                    progress = (idx / results['total']) * 100
                    print(f"\rProgress: {progress:.1f}% ({idx}/{results['total']})", end='', flush=True)
                    
            except Exception as e:
                logger.error(f"Error processing {texture_file}: {e}")
                results['errors'] += 1
                results['files'].append({
                    'file': str(texture_file),
                    'status': 'error',
                    'error': str(e)
                })
        
        if not use_tqdm and show_progress and args.progress == 'percent':
            print()  # New line after progress
        
        results['end_time'] = datetime.now()
        results['duration'] = (results['end_time'] - results['start_time']).total_seconds()
        
        return results
    
    def _display_summary(self, results: Dict[str, Any]) -> None:
        """Display processing summary."""
        print(f"\n{'=' * 60}")
        print("PROCESSING SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total Files:     {results['total']}")
        print(f"Processed:       {results['processed']}")
        print(f"Errors:          {results['errors']}")
        print(f"Skipped:         {results['skipped']}")
        print(f"Duration:        {results['duration']:.2f} seconds")
        
        if results['total'] > 0:
            success_rate = (results['processed'] / results['total']) * 100
            print(f"Success Rate:    {success_rate:.1f}%")
        
        print(f"{'=' * 60}\n")
    
    def _generate_report(self, results: Dict[str, Any], report_path: str) -> None:
        """
        Generate JSON report of processing results.
        
        Args:
            results: Processing results dictionary
            report_path: Path to save report
        """
        try:
            report_data = {
                'app_name': APP_NAME,
                'app_version': APP_VERSION,
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total': results['total'],
                    'processed': results['processed'],
                    'errors': results['errors'],
                    'skipped': results['skipped'],
                    'duration_seconds': results['duration']
                },
                'files': results['files']
            }
            
            report_file = Path(report_path)
            report_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2)
            
            logger.info(f"Report saved to: {report_path}")
            print(f"Report saved to: {report_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")


def main(args: Optional[List[str]] = None) -> int:
    """
    Main CLI entry point.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code
    """
    cli = CLIInterface()
    return cli.run(args)


if __name__ == '__main__':
    sys.exit(main())
