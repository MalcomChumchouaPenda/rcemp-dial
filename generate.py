
from argparse import ArgumentParser
from tools import benchmarks


progname = 'BenchmarkGenerator'
description='Generator of benchmarks'
parser = ArgumentParser(prog=progname, description=description)

parser.add_argument('-b', '--benchmark', required=True)
parser.add_argument('-v', '--verbose', action='store_true')
parser.add_argument('-r', '--replace', action='store_true')
parser.add_argument('-f', '--filter', default='%')


def main(id_, filter_, verbose, replace):
    benchmarkcls = getattr(benchmarks, id_)
    benchmark = benchmarkcls(filter_=filter_, verbose=verbose)
    if replace:
        benchmark.clear_problems()
    benchmark.generate_problems()

if __name__ == '__main__':
    args = parser.parse_args()
    id_ = args.benchmark
    filter_ = args.filter
    verbose = args.verbose
    replace = args.replace
    main(id_, filter_, verbose, replace)