"""
setup_models.py — Auto-download all required AI models.

Run this script once after installing requirements:
    python setup_models.py

It is also invoked by the CI/CD build workflow so models are bundled
inside the EXE and the user never has to manually click "Download".

The script is non-interactive and exit-code safe:
  • Exit 0 — all models present (or downloaded successfully)
  • Exit 1 — one or more models could not be downloaded (app still works, just without that model)
"""

from __future__ import annotations

import sys
import argparse
import logging
from pathlib import Path

# Allow both "python setup_models.py" (repo root) and import from main.py
_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT / 'src'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger('setup_models')

_parser = argparse.ArgumentParser(description='Download AI models for Game Texture Sorter')
_parser.add_argument('--quiet', '-q', action='store_true', help='Suppress progress output')
_parser.add_argument(
    '--output-dir', '-o',
    type=str,
    default=None,
    help='Directory to save downloaded .pth/.onnx files (overrides config.get_data_dir())',
)
_args, _unknown = _parser.parse_known_args()
_QUIET = _args.quiet
_OUTPUT_DIR = Path(_args.output_dir) if _args.output_dir else None


def _progress(model_name: str, downloaded: int, total: int) -> None:
    if _QUIET:
        return
    if total > 0:
        pct = int(downloaded / total * 100)
        bar = '█' * (pct // 5) + '░' * (20 - pct // 5)
        mb_dl = downloaded / 1_048_576
        mb_total = total / 1_048_576
        print(f'\r  {model_name:35s}  [{bar}] {pct:3d}%  {mb_dl:.1f}/{mb_total:.1f} MB',
              end='', flush=True)
    else:
        mb_dl = downloaded / 1_048_576
        print(f'\r  {model_name:35s}  {mb_dl:.1f} MB downloaded…', end='', flush=True)


def main() -> int:
    """Download all required models.  Returns exit-code (0=success, 1=partial failure)."""
    try:
        from upscaler.model_manager import AIModelManager
    except ImportError:
        try:
            sys.path.insert(0, str(_ROOT))
            from src.upscaler.model_manager import AIModelManager  # type: ignore[no-redef]
        except ImportError as exc:
            logger.error(f'Cannot import AIModelManager: {exc}')
            return 1

    mgr = AIModelManager(models_dir=_OUTPUT_DIR)
    required = mgr.get_required_models()

    if not required:
        logger.info('No downloadable models defined.')
        return 0

    logger.info(f'Checking {len(required)} required model(s)…')

    already_installed = [m for m in required
                         if mgr.get_model_status(m).value == 'installed']
    to_download = [m for m in required if m not in already_installed]

    if already_installed and not _QUIET:
        logger.info(f'  Already installed: {", ".join(already_installed)}')

    if not to_download:
        logger.info('✅  All required models already installed.')
        return 0

    logger.info(f'  Need to download: {", ".join(to_download)}')

    failures: list[str] = []
    for model_name in to_download:
        info = mgr.MODELS.get(model_name, {})
        size_mb = info.get('size_mb', 0)
        if not _QUIET:
            print(f'\n⬇  {model_name}  ({size_mb} MB)')
        try:
            def _cb(dl: int, total: int, captured_name: str = model_name) -> None:
                _progress(captured_name, dl, total)

            ok = mgr.download_model(model_name, progress_callback=_cb)
            if not _QUIET:
                print()  # newline after progress bar
            if ok:
                logger.info(f'  ✅  {model_name} downloaded successfully')
            else:
                logger.warning(f'  ⚠️   {model_name} skipped (auto_download/native)')
        except Exception as exc:
            if not _QUIET:
                print()
            logger.error(f'  ❌  {model_name} failed: {exc}')
            failures.append(model_name)

    if failures:
        logger.warning(
            f'\n{len(failures)} model(s) could not be downloaded: {", ".join(failures)}\n'
            'The application will still work; affected features will fall back to '
            'CPU-based processing or be temporarily disabled.'
        )
        return 1

    logger.info('\n✅  All required models downloaded successfully.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
