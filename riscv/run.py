import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(script, args):
    sys.argv = [script] + args
    try:
        runpy.run_path(script, run_name="__main__")
    except SystemExit as e:
        if e.code not in (None, 0):
            sys.exit(e.code)


source, binary_out, trace_out = sys.argv[1], sys.argv[2], sys.argv[3]

run(os.path.join(HERE, "assembler.py"), [source, binary_out])
run(os.path.join(HERE, "simulator.py"), [binary_out, trace_out])