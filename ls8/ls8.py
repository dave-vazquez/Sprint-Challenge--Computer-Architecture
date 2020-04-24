#!/usr/bin/env python3

"""Main."""

import os
import sys

from cpu import *

os.system("clear")
program_filename = sys.argv[1]

cpu = CPU()
cpu.load(program_filename)
cpu.run()
