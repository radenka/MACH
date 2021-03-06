import argparse
import argcomplete
from termcolor import colored


def load_arguments():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--mode", help="Choice what MACH should do.",
                        required=True,
                        choices=("set_of_molecules_info", "calculation", "parameterization", "comparison", "parameterization_find_args",
                                 "calculation_meta", "parameterization_meta", "make_complete_html", "clusterization", "neural_network"))  # only for my usage
    parser.add_argument("--sdf", help="Sdf file with molecules data.")
    parser.add_argument("--charges", help="File to store calculated charges of file with charges for comparison.")
    parser.add_argument("--ref_charges", help="File with reference charges for comparison.")
    parser.add_argument("--parameters", help="File with parameters.")
    parser.add_argument("--method", help="Empirical method for calculation partial atomic charges.",
                        choices=("EEM", "EEMfixed", "SFKEEM", "QEq", "GM", "MGC", "SQE", "ACKS2"))
    parser.add_argument("--optimization_method", help="Optimization method for parameterization.", choices=("local_minimization", "guided_minimization"))
    parser.add_argument("--minimization_method", help="Minimization method for parameterization.", default="SLSQP")
    parser.add_argument("--cpu", help="Only for optimization method guided minimization. Define number of used cpu for parameterization.", default=1, type=int)
    parser.add_argument("--num_of_samples", help="Only for optimization method guided minimization. Define how many initial samples are used.", default=500000, type=int)
    parser.add_argument("--subset_heuristic", help="Only for optimization method guided minimization. For first step of GM is used only subset of n molecules. If 0 is provided, full set of molecules is used.", default=5, type=int)
    parser.add_argument("--random_seed", help="Only for parameterization. Set initial random state. Use for reproducion of results. Set 0 for no initial state.", type=int, default=1)
    parser.add_argument("--data_dir", help="For parameterization and comparison only. Defined directory is created to store correlation graphs and html file.")
    parser.add_argument("--RAM", help="For parameterization_meta and calculation_meta only. Define max. RAM usage for META job in GB.", default=10, type=int)  # only for my usage
    parser.add_argument("--walltime", help="For parameterization_meta and calculation_meta only. Define max time for META job in hours.", default=10, type=int)  # only for my usage
    parser.add_argument("--git_hash", help="For internal usage only.")  # only for my usage
    parser.add_argument("--validation", help="Adjust how many percent of set of molecules should be used for validation.", default=10, type=int)  # only for my usage
    parser.add_argument("--atomic_types_pattern",
                        help="For mode set_of_molecules_info and parameterization. Define atomic types for statistics",
                        choices=("plain", "hbo", "external_atom_type"), default="hbo")
    parser.add_argument("--num_of_molecules", help="Only these number of molecules will be loaded.", type=int)
    parser.add_argument("-f", "--rewriting_with_force", action="store_true",
                        help="All existed files with the same names like your outputs will be replaced.")
    parser.add_argument("--ext_file", help="Path to file where external atom types are stored.")
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    if args.mode == "set_of_molecules_info":
        if args.sdf is None:
            parser.error("For set_of_molecules_info must choice --sdf.")

    elif args.mode == "calculation":
        if args.method is None or args.sdf is None or args.charges is None:
            parser.error("For calculation must be choice --method, --sdf and --charges.")

    elif args.mode == "parameterization":
        if args.ref_charges is None or args.method is None \
                or args.sdf is None or args.data_dir is None:
            parser.error("For parameterization must be choice --ref_charges, --method, --sdf and --data_dir")

    elif args.mode == "comparison":
        if args.charges is None or args.ref_charges is None or args.data_dir is None:
            parser.error("For comparison must choice --charges, --ref_charges and --data_dir.")

    elif args.mode == "calculation_meta":  # only for my usage
        if args.method is None or args.sdf is None or args.charges is None:
            parser.error("For calculation_meta must be choice --method, --sdf and --charges.")

    elif args.mode == "parameterization_meta":  # only for my usage
        if args.ref_charges is None or args.method is None or args.sdf is None:
            parser.error("For parameterization_meta must be choice --ref_charges, --method and --sdf. ")

    return args
