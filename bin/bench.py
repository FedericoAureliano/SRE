#!/usr/bin/env python3
import os
import sys
import glob
import subprocess
import signal
import datetime
import time
import concurrent.futures

from collections import namedtuple
from operator import attrgetter

# arguments
TIMEOUT     = 30.0
PROBLEMS    = "instances/**/*.smt2*"
RESULTS_DIR = "results"

# data
CSV_HEADER  = "Instance,Result,Time\n"
Result      = namedtuple('Result', ('problem', 'result', 'elapsed'))

# constants
SAT_RESULT     = 'sat'
UNSAT_RESULT   = 'unsat'
UNKNOWN_RESULT = 'unknown'
TIMEOUT_RESULT = 'timeout (%.1f s)' % TIMEOUT
ERROR_RESULT   = 'error'

SOLVERS = {
    #timeout is a little more than TIMEOUT
    # "Z3seq"   : "tools/z3 smt.string_solver=seq -T:33",
    "Z3str3"  : "tools/z3 smt.str.multiset_check=false  smt.str.count_abstraction=true smt.string_solver=z3str3 -T:33",
    # "CVC4"    : "tools/cvc4 --lang smt --strings-exp --tlimit=33000 -q",
}

def output2result(problem, output):
    # it's important to check for unsat first, since sat
    # is a substring of unsat
    if 'UNSAT' in output or 'unsat' in output:
        return UNSAT_RESULT
    if 'SAT' in output or 'sat' in output:
        return SAT_RESULT
    if 'UNKNOWN' in output or 'unknown' in output:
        return UNKNOWN_RESULT

    # print(problem, ': Couldn\'t parse output', file=sys.stderr)
    return ERROR_RESULT


def run_problem(solver, invocation, problem):
    # pass the problem to the command
    command = "%s %s" %(invocation, problem)
    # get start time
    start = datetime.datetime.now().timestamp()
    # run command
    process = subprocess.Popen(
        command,
        shell      = True,
        stdout     = subprocess.PIPE,
        stderr     = subprocess.PIPE,
        preexec_fn = os.setsid
    )
    # wait for it to complete
    try:
        process.wait(timeout=TIMEOUT)
    # if it times out ...
    except subprocess.TimeoutExpired:
        # kill it
        print('TIMED OUT:', repr(command), '... killing', process.pid, file=sys.stderr)
        os.killpg(os.getpgid(process.pid), signal.SIGINT)
        # set timeout result
        elapsed = TIMEOUT
        output  = TIMEOUT_RESULT
    # if it completes in time ...
    else:
        # measure run time
        end     = datetime.datetime.now().timestamp()
        elapsed = end - start
        # get result
        stdout = process.stdout.read().decode("utf-8", "ignore")
        stderr = process.stderr.read().decode("utf-8", "ignore")
        output = output2result(problem, stdout + stderr)
    # make result
    result = Result(
        problem  = problem.split("/", 2)[2],
        result   = output,
        elapsed  = elapsed
    )
    return result


def run_solver(args):
    solver   = args[0]
    command  = args[1]
    problems = args[2]
    filename = "%s/%s.csv" % (RESULTS_DIR, solver)

    with open(filename, 'w+', buffering=1) as fp:
        fp.write(CSV_HEADER)
        for problem in problems:
            result = run_problem(solver, command, problem)
            fp.write("%s,%s,%s\n" % (result.problem, result.result, result.elapsed))


def signal_handler(signal, frame):
    print("KILLING!")
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)


def main():
    signal.signal(signal.SIGTERM, signal_handler)
    problems = glob.glob(PROBLEMS, recursive=True)
    print(len(problems))
    
    args = [[solver, command, problems] for solver, command in SOLVERS.items()]
    try:
        with concurrent.futures.ProcessPoolExecutor() as executor:
            executor.map(run_solver, args)
    except KeyboardInterrupt:
        print('Interrupted!')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)


if __name__ == '__main__':
    main()
