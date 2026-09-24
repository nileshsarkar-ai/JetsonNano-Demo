#!/usr/bin/env python3
"""Open the bundled presentation with an installed desktop viewer."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def open_presentation():
    deck = ROOT / 'docs/Jetson_Nano_Local_AI_Experiments.pptx'
    pdf = deck.with_suffix('.pdf')
    if not deck.is_file():
        raise RuntimeError('Presentation missing: ' + str(deck))
    print('Presentation:', deck, flush=True)
    if sys.platform != 'darwin' and not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
        print('No desktop display detected. Open the file from the Nano desktop or copy it to a computer with a viewer.')
        return False
    if sys.platform == 'darwin':
        command = ['open', str(deck)]
    else:
        office = shutil.which('libreoffice') or shutil.which('soffice')
        if office:
            command = [office, '--show', str(deck)]
        elif shutil.which('xdg-open'):
            command = ['xdg-open', str(pdf if pdf.is_file() else deck)]
        else:
            print('No presentation viewer found. Open the bundled PPTX/PDF on a computer with a viewer.')
            return False
    # A desktop viewer can outlive the menu; do not put it under demo supervision.
    subprocess.Popen(command, start_new_session=True)
    return True


if __name__ == '__main__':
    try:
        open_presentation()
    except (OSError, RuntimeError) as error:
        print('Cannot open presentation:', error, file=sys.stderr)
        sys.exit(1)
