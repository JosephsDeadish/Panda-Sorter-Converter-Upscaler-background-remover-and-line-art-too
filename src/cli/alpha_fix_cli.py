"""
CLI Tool for Alpha Color Detection and Correction
Author: Dead On The Inside / JosephsDeadish
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List
import json
import os

# Fix Unicode encoding issues on Windows
# This prevents UnicodeEncodeError when printing emojis to console
if sys.platform == 'win32':
    import codecs
    # Reconfigure stdout and stderr to use UTF-8 encoding
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    # Also set environment variable for child processes
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from ..preprocessing.alpha_correction import AlphaCorrector, AlphaCorrectionPresets
from ..config import APP_NAME, APP_VERSION

logger = logging.getLogger(__name__)


class AlphaFixCLI:
    """Command-line interface for alpha correction tool."""
    
    def __init__(self):
        """Initialize alpha fix CLI."""
        self.parser = self._create_parser()
        self.corrector = AlphaCorrector()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for alpha fix tool."""
        parser = argparse.ArgumentParser(
            prog=f'{APP_NAME} Alpha Fix',
            description='Automatically detect and correct alpha colors in textures',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=f"""
Examples:
  # Fix single image with PS2 binary preset
  python -m src.cli.alpha_fix_cli image.png --preset ps2_binary

  # Fix all images in directory
  python -m src.cli.alpha_fix_cli input_dir/ --output output_dir/ --preset ps2_three_level

  # Analyze alpha colors without modification
  python -m src.cli.alpha_fix_cli image.png --analyze-only

  # Fix with custom thresholds
  python -m src.cli.alpha_fix_cli image.png --custom 0,127,0 128,255,255

  # List available presets
  python -m src.cli.alpha_fix_cli --list-presets

Available Presets:
  ps2_binary        - Binary alpha (0 or 255) for PS2 textures
  ps2_three_level   - Three levels (0, 128, 255) for PS2
  ps2_ui            - Sharp cutoff for PS2 UI elements
  ps2_smooth        - Smooth gradients normalized to PS2 values
  generic_binary    - Simple binary alpha
  clean_edges       - Remove semi-transparent edge fringing

Version: {APP_VERSION}
"""
        )
        
        # Input/Output
        parser.add_argument(
            'input',
            type=str,
            nargs='?',
            help='Input image file or directory'
        )
        
        parser.add_argument(
            '--output', '-o',
            type=str,
            help='Output file or directory (default: add _corrected suffix)'
        )
        
        # Correction options
        parser.add_argument(
            '--preset', '-p',
            type=str,
            default='ps2_binary',
            choices=AlphaCorrectionPresets.list_presets(),
            help='Correction preset (default: ps2_binary)'
        )
        
        parser.add_argument(
            '--custom', '-c',
            type=str,
            nargs='+',
            metavar='MIN,MAX,TARGET',
            help='Custom thresholds as "min,max,target" (can specify multiple)'
        )
        
        parser.add_argument(
            '--preserve-gradients',
            action='store_true',
            help='Preserve smooth alpha gradients (only snap extremes)'
        )
        
        # Processing options
        parser.add_argument(
            '--recursive', '-r',
            action='store_true',
            help='Process directories recursively'
        )
        
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite input files'
        )
        
        parser.add_argument(
            '--no-backup',
            action='store_true',
            help='Do not create backup when overwriting'
        )
        
        # Analysis options
        parser.add_argument(
            '--analyze-only',
            action='store_true',
            help='Only analyze alpha colors, do not modify'
        )
        
        parser.add_argument(
            '--list-presets',
            action='store_true',
            help='List all available presets and exit'
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
            '--report',
            type=str,
            help='Save detailed report to JSON file'
        )
        
        return parser
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run alpha fix CLI.
        
        Args:
            args: Command line arguments (uses sys.argv if None)
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            parsed_args = self.parser.parse_args(args)
            
            # Setup logging
            self._setup_logging(parsed_args)
            
            # List presets and exit
            if parsed_args.list_presets:
                self._list_presets()
                return 0
            
            # Validate input (required if not listing presets)
            if not parsed_args.input:
                logger.error("Input path is required (unless using --list-presets)")
                self.parser.print_help()
                return 1
            
            input_path = Path(parsed_args.input)
            if not input_path.exists():
                logger.error(f"Input path does not exist: {input_path}")
                return 1
            
            # Process
            if input_path.is_file():
                return self._process_single_file(parsed_args, input_path)
            elif input_path.is_dir():
                return self._process_directory(parsed_args, input_path)
            else:
                logger.error(f"Invalid input path: {input_path}")
                return 1
                
        except KeyboardInterrupt:
            logger.warning("\nProcessing interrupted by user")
            return 130
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return 1
    
    def _setup_logging(self, args: argparse.Namespace) -> None:
        """Configure logging based on CLI arguments."""
        level = logging.INFO
        
        if args.verbose:
            level = logging.DEBUG
        elif args.quiet:
            level = logging.ERROR
        
        logging.basicConfig(
            level=level,
            format='%(levelname)s: %(message)s'
        )
    
    def _list_presets(self) -> None:
        """List all available presets with descriptions."""
        print("\nAvailable Alpha Correction Presets:\n")
        print("=" * 70)
        
        presets = {
            'ps2_binary': AlphaCorrectionPresets.PS2_BINARY,
            'ps2_three_level': AlphaCorrectionPresets.PS2_THREE_LEVEL,
            'ps2_ui': AlphaCorrectionPresets.PS2_UI,
            'ps2_smooth': AlphaCorrectionPresets.PS2_SMOOTH,
            'generic_binary': AlphaCorrectionPresets.GENERIC_BINARY,
            'clean_edges': AlphaCorrectionPresets.CLEAN_EDGES,
        }
        
        for name, preset in presets.items():
            print(f"\n{name}")
            print(f"  {preset['description']}")
            print(f"  Thresholds: {preset['thresholds']}")
        
        print("\n" + "=" * 70)
    
    def _process_single_file(
        self,
        args: argparse.Namespace,
        input_path: Path
    ) -> int:
        """Process a single image file."""
        logger.info(f"Processing: {input_path}")
        
        # Analyze only mode
        if args.analyze_only:
            return self._analyze_file(input_path)
        
        # Get preset or custom thresholds
        preset = args.preset
        if args.custom:
            # Parse custom thresholds
            try:
                thresholds = []
                for threshold_str in args.custom:
                    parts = threshold_str.split(',')
                    if len(parts) != 3:
                        logger.error(f"Invalid threshold format: {threshold_str}")
                        logger.error("Expected format: MIN,MAX,TARGET")
                        return 1
                    min_val = int(parts[0])
                    max_val = int(parts[1])
                    target = None if parts[2].lower() == 'none' else int(parts[2])
                    thresholds.append((min_val, max_val, target))
                
                # Create custom preset
                preset = {
                    'name': 'Custom',
                    'thresholds': thresholds,
                    'mode': 'threshold'
                }
            except ValueError as e:
                logger.error(f"Error parsing custom thresholds: {e}")
                return 1
        
        # Determine output path
        output_path = None
        if args.output:
            output_path = Path(args.output)
        
        # Process image
        result = self.corrector.process_image(
            input_path,
            output_path=output_path,
            preset=preset,
            overwrite=args.overwrite,
            backup=not args.no_backup
        )
        
        # Display results
        if not args.quiet:
            self._display_result(result)
        
        # Save report if requested
        if args.report:
            self._save_report([result], Path(args.report))
        
        return 0 if result['success'] else 1
    
    def _process_directory(
        self,
        args: argparse.Namespace,
        input_dir: Path
    ) -> int:
        """Process all images in a directory."""
        # Find image files
        if args.recursive:
            pattern = '**/*'
        else:
            pattern = '*'
        
        image_extensions = {'.png', '.tga', '.bmp', '.tif', '.tiff', '.webp'}
        image_paths = []
        
        for ext in image_extensions:
            image_paths.extend(input_dir.glob(f"{pattern}{ext}"))
            image_paths.extend(input_dir.glob(f"{pattern}{ext.upper()}"))
        
        if not image_paths:
            logger.warning(f"No images found in {input_dir}")
            return 1
        
        logger.info(f"Found {len(image_paths)} images")
        
        # Analyze only mode
        if args.analyze_only:
            return self._analyze_batch(image_paths)
        
        # Get preset
        preset = args.preset
        if args.custom:
            try:
                thresholds = []
                for threshold_str in args.custom:
                    parts = threshold_str.split(',')
                    min_val = int(parts[0])
                    max_val = int(parts[1])
                    target = None if parts[2].lower() == 'none' else int(parts[2])
                    thresholds.append((min_val, max_val, target))
                preset = {'thresholds': thresholds, 'mode': 'threshold'}
            except ValueError as e:
                logger.error(f"Error parsing custom thresholds: {e}")
                return 1
        
        # Determine output directory
        output_dir = None
        if args.output:
            output_dir = Path(args.output)
        
        # Progress callback
        def progress(current, total):
            if not args.quiet and total > 0:
                percentage = (100 * current // total) if total > 0 else 0
                print(f"\rProgress: {current}/{total} ({percentage}%)", end='')
        
        # Process batch
        results = self.corrector.process_batch(
            image_paths,
            output_dir=output_dir,
            preset=preset,
            preserve_structure=args.recursive,
            overwrite=args.overwrite,
            backup=not args.no_backup,
            progress_callback=progress if not args.quiet else None
        )
        
        if not args.quiet:
            print()  # New line after progress
        
        # Display summary
        if not args.quiet:
            self._display_batch_summary(results)
        
        # Save report if requested
        if args.report:
            self._save_report(results, Path(args.report))
        
        # Return success if at least one image was processed successfully
        success_count = sum(1 for r in results if r['success'])
        return 0 if success_count > 0 else 1
    
    def _analyze_file(self, image_path: Path) -> int:
        """Analyze alpha colors in a single file."""
        try:
            from PIL import Image
            import numpy as np
            
            img = Image.open(image_path)
            if img.mode != 'RGBA':
                print(f"\n{image_path.name}: No alpha channel")
                return 0
            
            img_array = np.array(img)
            detection = self.corrector.detect_alpha_colors(img_array)
            
            print(f"\n=== Alpha Analysis: {image_path.name} ===")
            print(f"Unique alpha values: {detection['unique_values']}")
            print(f"Alpha range: {detection['alpha_min']} - {detection['alpha_max']}")
            print(f"Alpha mean: {detection['alpha_mean']:.1f}")
            print(f"Alpha median: {detection['alpha_median']:.1f}")
            print(f"\nPixel counts:")
            print(f"  Transparent (0): {detection['transparent_pixels']:,} ({detection['transparency_ratio']:.1%})")
            print(f"  Semi-transparent: {detection['semi_transparent_pixels']:,} ({detection['semi_transparency_ratio']:.1%})")
            print(f"  Opaque (255): {detection['opaque_pixels']:,} ({detection['opacity_ratio']:.1%})")
            print(f"\nDetected patterns: {', '.join(detection['patterns']) if detection['patterns'] else 'None'}")
            print(f"Is binary: {detection['is_binary']}")
            
            if detection['dominant_values']:
                print(f"\nDominant alpha values:")
                for value, count in detection['dominant_values'][:5]:
                    percentage = 100 * count / (img_array.shape[0] * img_array.shape[1])
                    print(f"  {value}: {count:,} pixels ({percentage:.1f}%)")
            
            print()
            return 0
            
        except Exception as e:
            logger.error(f"Error analyzing {image_path}: {e}")
            return 1
    
    def _analyze_batch(self, image_paths: List[Path]) -> int:
        """Analyze alpha colors in multiple files."""
        from PIL import Image
        import numpy as np
        
        print(f"\nAnalyzing {len(image_paths)} images...\n")
        
        for idx, img_path in enumerate(image_paths):
            try:
                img = Image.open(img_path)
                if img.mode != 'RGBA':
                    print(f"[{idx+1}/{len(image_paths)}] {img_path.name}: No alpha")
                    continue
                
                img_array = np.array(img)
                detection = self.corrector.detect_alpha_colors(img_array)
                
                patterns = ', '.join(detection['patterns']) if detection['patterns'] else 'none'
                print(f"[{idx+1}/{len(image_paths)}] {img_path.name}:")
                print(f"  Values: {detection['unique_values']}, "
                      f"Range: {detection['alpha_min']}-{detection['alpha_max']}, "
                      f"Patterns: {patterns}")
                
            except Exception as e:
                logger.error(f"Error analyzing {img_path}: {e}")
        
        return 0
    
    def _display_result(self, result: dict) -> None:
        """Display processing result for a single file."""
        if not result['success']:
            print(f"\n❌ Failed: {result.get('reason', result.get('error', 'Unknown error'))}")
            return
        
        if not result.get('modified'):
            print(f"\n✓ No changes needed: {result.get('reason', '')}")
            return
        
        print(f"\n✓ Successfully corrected alpha channel")
        if 'output_path' in result:
            print(f"  Output: {result['output_path']}")
        
        if 'correction' in result:
            stats = result['correction']
            print(f"  Modified pixels: {stats['pixels_changed']:,} / {stats['total_pixels']:,} "
                  f"({stats['modification_ratio']:.1%})")
    
    def _display_batch_summary(self, results: List[dict]) -> None:
        """Display summary of batch processing."""
        total = len(results)
        successful = sum(1 for r in results if r['success'])
        modified = sum(1 for r in results if r.get('modified'))
        failed = total - successful
        
        print("\n" + "=" * 60)
        print("Batch Processing Summary")
        print("=" * 60)
        print(f"Total images: {total}")
        print(f"Successfully processed: {successful}")
        print(f"Modified: {modified}")
        print(f"Unchanged: {successful - modified}")
        print(f"Failed: {failed}")
        
        # Display corrector stats
        stats = self.corrector.get_stats()
        if stats['pixels_modified'] > 0:
            print(f"\nTotal pixels modified: {stats['pixels_modified']:,}")
        
        print("=" * 60)
    
    def _save_report(self, results: List[dict], report_path: Path) -> None:
        """Save detailed processing report to JSON file."""
        try:
            report = {
                'total': len(results),
                'successful': sum(1 for r in results if r['success']),
                'modified': sum(1 for r in results if r.get('modified')),
                'failed': sum(1 for r in results if not r['success']),
                'stats': self.corrector.get_stats(),
                'results': results
            }
            
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Report saved to: {report_path}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")


def main():
    """Main entry point for alpha fix CLI."""
    cli = AlphaFixCLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main()
