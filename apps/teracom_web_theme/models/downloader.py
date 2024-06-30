# -*- coding: utf-8 -*-

import shutil
import sys
from pathlib import Path

try:
    from bing import Bing
except ImportError:
    from .bing import Bing


def download(query, limit=100, output_dir='dataset', adult_filter_off=True,
             force_replace=False, timeout=60, filter="", verbose=True):
    """download the images within the limit provided"""
    if adult_filter_off:
        adult = 'off'
    else:
        adult = 'on'

    image_dir = Path(output_dir).joinpath(query).absolute()

    if force_replace:
        if Path.isdir(image_dir):
            shutil.rmtree(image_dir)

    try:
        if not Path.is_dir(image_dir):
            Path.mkdir(image_dir, parents=True)

    except Exception:
        sys.exit(1)

    bing = Bing(query, limit, image_dir, adult, timeout, filter, verbose)
    return bing.run()
