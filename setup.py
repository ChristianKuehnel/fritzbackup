#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from distutils.core import setup


setup(name='fritzbackup',
      version='0.1.0',
      description='backup scripts storing backup on Fritz!NAS',
      author='Christian Kühnel',
      author_email='christian.kuehnel@gmail.com',
      url='https://www.python.org/sigs/distutils-sig/',
      packages=['fritzbackup'],
      install_requires=['pyyaml'],
      scripts=['fritzbackup/fritzbackup'],
      )
