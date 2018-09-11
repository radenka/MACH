from .set_of_molecules import SetOfMolecules
from .control_existing import control_existing_files
from .calculation import write_charges_to_file
from .comparison import Comparison
from .molecule import MoleculeChg
from importlib import import_module
from termcolor import colored
from scipy.optimize import minimize, differential_evolution
from numba import jit
from sys import exit
from numpy import sum, sqrt, abs, max, array_split, linalg, array
from pyDOE import lhs
from functools import partial
from multiprocessing import Pool
from itertools import chain
from operator import itemgetter
from datetime import datetime as date
from datetime import timedelta
from os import path
from shutil import copyfile


def calculate_charges_for_set_of_parameters(set_of_parameters, method, set_of_molecules):
    results = []
    for parameters in set_of_parameters:
        results.append((calculate_charges_and_statistical_data(parameters, method, set_of_molecules), tuple(parameters)))
    return results


def local_minimization(input_parameters, method, set_of_molecules, bounds):
    res = minimize(calculate_charges_and_statistical_data, input_parameters, method="SLSQP", bounds=bounds,
                   args=(method, set_of_molecules))
    return res.fun, res.x


def write_parameters_to_file(parameters_file, method, set_of_molecules_file, summary_statistics, optimization_method, start_time):
    print("Writing parameters to {}...".format(parameters_file))
    parameters_lines = ["method: {}".format(method),
                        "length_type: {}".format(method.length_correction_key),
                        "<<global>>"] + \
                       ["{}: {}".format(key, value) for key, value in method.parameters.items() if key[0].islower()] + \
                       ["<<key>>"] + \
                       [key for key in method.keys] + \
                       ["<<value_symbol>>"] + \
                       [key for key in method.value_symbols] + \
                       ["<<value>>"] + \
                       ["{}  {}".format(atomic_type.replace("~", " "),
                                        "  ".join([str(method.parameters["{}_{}".format(atomic_type, key)])
                                                   for key in method.value_symbols]))
                        for atomic_type in method.atomic_types] + ["<<end>>"]
    summary_lines = ["Set of molecules: {}".format(set_of_molecules_file),
                     "Method: {}".format(method),
                     "Optimization method: {}".format(optimization_method),
                     "Date of parameterization: {}".format(start_time.strftime("%Y-%m-%d %H:%M")),
                     "Time of parameterization: {}\n\n".format(str(date.now() - start_time)[:-7])]
    with open(parameters_file, "w") as par_file:
        par_file.writelines("\n".join(parameters_lines) + "\n\n\n")
        par_file.writelines("\n".join(summary_lines))
        par_file.write(summary_statistics)
    print(colored("ok\n", "green"))
    return summary_lines, parameters_lines

def prepare_data_for_comparison(method, set_of_molecules):
    atomic_types_charges = {}
    set_of_molecules.atomic_types_charges = {}
    for index, atomic_type_charges in enumerate(set_of_molecules.ref_atomic_types_charges):
        atomic_type, asn = method.atomic_types[index], set_of_molecules.all_symbolic_numbers
        atomic_types_charges[atomic_type] = separate_atomic_type_charges(method.results, asn, index)
        set_of_molecules.atomic_types_charges[atomic_type] = separate_atomic_type_charges(set_of_molecules.ref_charges, asn, index)
    chg_molecules = []
    index = 0
    for molecule in set_of_molecules.molecules:
        molecule_len = len(molecule)
        chg_molecules.append(MoleculeChg(method.results[index:index + molecule_len]))
        index += molecule_len
    return atomic_types_charges, chg_molecules

def prepare_data_for_parameterization(set_of_molecules, ref_charges, method):
    method.create_method_data(set_of_molecules)
    set_of_molecules.add_ref_charges(ref_charges, len(method.atomic_types), set_of_molecules.all_symbolic_numbers)
    method.control_parameters(set_of_molecules.file, set_of_molecules.all_symbolic_numbers)

@jit(nopython=True, cache=True)
def rmsd_calculation(results, right_charges):
    deviations = abs(results - right_charges)**2
    return sqrt((1.0 / deviations.size) * sum(deviations))


@jit(nopython=True, cache=True)
def separate_atomic_type_charges(charges, symbolic_numbers, atomic_type_symbolic_number):
    return charges[symbolic_numbers == atomic_type_symbolic_number]


def calculate_charges_and_statistical_data(list_of_parameters, method, set_of_molecules):
    method.parameters_values = list_of_parameters
    try:
        method.calculate(set_of_molecules)
    except (linalg.linalg.LinAlgError, ZeroDivisionError):
        return 1000
    rmsd = rmsd_calculation(method.results, set_of_molecules.ref_charges)
    atomic_types_rmsd = []
    for index, atomic_type_charges in enumerate(set_of_molecules.ref_atomic_types_charges):
        calculated_atomic_types_charges = separate_atomic_type_charges(method.results, set_of_molecules.all_symbolic_numbers, index)
        atomic_types_rmsd.append(rmsd_calculation(calculated_atomic_types_charges, atomic_type_charges))
    greater_rmsd = max(atomic_types_rmsd)
    print("Total RMSD: {}    Worst RMSD: {}".format(str(rmsd)[:8], str(greater_rmsd)[:8]), end="\r")
    return greater_rmsd + rmsd + sum(atomic_types_rmsd) / len(atomic_types_rmsd)


class Parameterization:
    def __init__(self, sdf, ref_charges, method, optimization_method, cpu, parameters, new_parameters, charges, data_dir, rewriting_with_force):
        start_time = date.now()
        control_existing_files(((sdf, True, "file"),
                                (ref_charges, True, "file"),
                                (parameters, True, "file"),
                                (data_dir, False, "directory")),
                               rewriting_with_force)
        method = getattr(import_module("modules.methods"), method)()
        method.load_parameters(parameters)
        set_of_molecules = SetOfMolecules(sdf)
        prepare_data_for_parameterization(set_of_molecules, ref_charges, method)
        print("Parameterizating of charges...")
        bounds = [(0.00001, 4)] * len(method.parameters_values) # dořesit
        if optimization_method == "minimization":
            if cpu != 1:
                exit(colored("Local minimization can not be parallelized!", "red"))
            final_parameters = local_minimization(method.parameters_values, method, set_of_molecules, bounds=bounds)[1]
        elif optimization_method == "guided_minimization":
            samples = lhs(len(method.parameters_values), samples=len(method.parameters_values) * 50, iterations=1000)
            partial_f = partial(calculate_charges_for_set_of_parameters, method=method, set_of_molecules=set_of_molecules)
            with Pool(cpu) as pool:
                candidates = sorted(list(chain.from_iterable(pool.map(partial_f, [sample for sample in array_split(samples, cpu)]))), key=itemgetter(0))[:3]
            partial_f = partial(local_minimization, method=method, set_of_molecules=set_of_molecules, bounds=bounds)
            with Pool(cpu) as pool:
                final_parameters = sorted([(result[0], result[1]) for result in pool.map(partial_f, [parameters[1] for parameters in candidates])], key=itemgetter(0))[0][1]
        elif optimization_method == "differential_evolution":
            final_parameters = differential_evolution(calculate_charges_and_statistical_data, bounds, args=(method, set_of_molecules))
        method.parameters_values = final_parameters
        method.calculate(set_of_molecules)
        print(colored("\033[Kok\n", "green"))
        atomic_types_charges, chg_molecules = prepare_data_for_comparison(method, set_of_molecules)
        comparison = Comparison(set_of_molecules, (method.results, atomic_types_charges, chg_molecules, charges), data_dir, rewriting_with_force, parameterization=True)
        copyfile(sdf, path.join(data_dir, path.basename(sdf)))
        copyfile(ref_charges, path.join(data_dir, path.basename(ref_charges)))
        write_charges_to_file(path.join(data_dir, charges), method.results, set_of_molecules)
        summary_lines, parameters_lines = write_parameters_to_file(path.join(data_dir, new_parameters), method, set_of_molecules.file, comparison.summary_statistics, optimization_method, start_time)
        comparison.write_html(path.join(data_dir, "{}_{}.html".format(path.basename(sdf)[:-4], method)), path.basename(sdf), charges, new_parameters, path.basename(ref_charges), summary_lines, parameters_lines)
