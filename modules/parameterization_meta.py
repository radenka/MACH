from os.path import basename
from os import system
from glob import glob
from termcolor import colored
import git


def parameterization_meta(sdf_file, ref_charges, parameters, method, optimization_method, minimization_method, atomic_types_pattern, num_of_molecules, num_of_samples, subset_heuristic, validation, cpu, RAM, walltime):  # only for my usage
    if not parameters:
        parameters = "modules/parameters/{}.json".format(method)
    command = "./mach.py --mode parameterization --method {} --optimization_method {} --minimization_method {} --parameters {} --sdf {} --ref_charges {} " \
              " --data_dir results_data --cpu {} --git_hash {} --atomic_types_pattern {} --subset_heuristic {} --num_of_samples {} --validation {} " \
        .format(method, optimization_method, minimization_method, basename(parameters), basename(sdf_file),
                basename(ref_charges), cpu, git.Repo(search_parent_directories=True).head.object.hexsha,
                atomic_types_pattern, subset_heuristic, num_of_samples, validation)
    command += " --num_of_molecules {}".format(num_of_molecules) if num_of_molecules else ""
    system("./modules/parameterization_meta.sh {} {} {} '{}' {} {} {}".format(parameters, sdf_file, ref_charges, command, cpu,
                                                            RAM, walltime))


