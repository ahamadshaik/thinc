#!/usr/bin/env python
from __future__ import print_function
import os
import sys
import shutil
from subprocess import call


def x(cmd):
    print('$ '+cmd)
    res = call(cmd, shell=True)
    if res != 0:
        sys.exit(res)


if len(sys.argv) < 2:
    print('usage: %s <install-mode> [<pip-date>]')
    sys.exit(1)


install_mode = sys.argv[1]


if install_mode == 'prepare':
    x('python setup.py clean --all')
    x('python pip-clear.py')

    pip_date = len(sys.argv) > 2 and sys.argv[2]
    if pip_date:
        x('python pip-date.py %s pip setuptools wheel six' % pip_date)

    x('pip install -r requirements.txt')
    x('pip install -r dev-requirements.txt')
    x('pip list')


elif install_mode == 'pip':
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    x('python setup.py sdist')
    x('python pip-clear.py')

    filenames = os.listdir('dist')
    assert len(filenames) == 1
    x('pip list')
    x('pip install dist/%s' % filenames[0])


elif install_mode == 'setup-install':
    x('python setup.py install')


elif install_mode == 'setup-develop':
    x('pip install -e .')


elif install_mode == 'test':
    x('pip install -r dev-requirements.txt')
    x('pip list')

    if os.path.exists('tmp'):
        shutil.rmtree('tmp')
    os.mkdir('tmp')

    try:
        old = os.getcwd()
        sys.path.remove(old)
        os.chdir('tmp')

        import thinc
        mod_path = os.path.abspath(os.path.dirname(thinc.__file__))
        x('python -m pytest %s' % mod_path)

    finally:
        os.chdir(old)