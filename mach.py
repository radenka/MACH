#!/usr/bin/env python3
from termcolor import colored
from numpy import random
import warnings
warnings.filterwarnings("ignore")
from modules.arguments import load_arguments
from modules.set_of_molecules import SetOfMolecules
from modules.calculation import Calculation
from modules.comparison import Comparison
from modules.parameterization import Parameterization
from modules.calculation_meta import calculation_meta  # only for my usage
from modules.parameterization_meta import parameterization_meta # only for my usage
from modules.make_complete_html import make_complete_html
from modules.clusterization import clusterize
from numba import jit
import nlopt


@jit(nopython=True, cache=True)
def numba_seed(seed):
    random.seed(seed)


if __name__ == '__main__':
    args = load_arguments()
    if args.random_seed != 0:
        random.seed(args.random_seed)
        numba_seed(args.random_seed)
        nlopt.srand(args.random_seed)
    print(colored("\nMACH is running with mode: {}\n".format(args.mode), "blue"))
    if args.mode == "set_of_molecules_info":
        set_of_molecules = SetOfMolecules(args.sdf, args.num_of_molecules)
        set_of_molecules.info(args.atomic_types_pattern)

    elif args.mode == "calculation":
        Calculation(args.sdf,
                    args.method,
                    args.parameters,
                    args.charges,
                    args.atomic_types_pattern,
                    args.rewriting_with_force)

    elif args.mode == "parameterization":
        Parameterization(args.sdf,
                         args.ref_charges,
                         args.parameters,
                         args.method,
                         args.optimization_method,
                         args.minimization_method,
                         args.atomic_types_pattern,
                         args.num_of_molecules,
                         args.num_of_samples,
                         args.subset_heuristic,
                         args.validation,
                         args.cpu,
                         args.data_dir,
                         args.rewriting_with_force,
                         args.ext_file,
                         args.git_hash)

    elif args.mode == "comparison":
        Comparison(args.ref_charges,
                   args.charges,
                   args.data_dir,
                   args.rewriting_with_force)

    elif args.mode == "calculation_meta":  # only for my usage
        calculation_meta(args.sdf,
                         args.method,
                         args.parameters,
                         args.charges,
                         args.atomic_types_pattern,
                         args.RAM,
                         args.walltime)

    elif args.mode == "parameterization_meta":  # only for my usage
        parameterization_meta(args.sdf,
                              args.ref_charges,
                              args.parameters,
                              args.method,
                              args.optimization_method,
                              args.minimization_method,
                              args.atomic_types_pattern,
                              args.num_of_molecules,
                              args.num_of_samples,
                              args.subset_heuristic,
                              args.validation,
                              args.cpu,
                              args.RAM,
                              args.walltime)

    elif args.mode == "make_complete_html":
        make_complete_html()

    elif args.mode == "clusterization":
        clusterize(args.charges, args.sdf)

