from sys import exit
from termcolor import colored
from numba import jit
from numpy import float64, empty, array, ones, zeros, sqrt, cosh, concatenate, int64, sum, prod
from numpy.linalg import solve, inv
from math import erf


class Methods:
    def __init__(self):
        self.necessarily_data = {"EEM": ["distances"], "QEq": ["distances"], "SFKEEM": ["distances"], "GM": ["bonds_without_bond_type", "num_of_bonds_mul_two"], "MGC": ["MGC_matrix"], "BEEM": ["distances"]}[str(self)]

    def create_method_data(self, set_of_molecules):
        set_of_molecules.all_num_of_atoms = array([molecule.num_of_atoms for molecule in set_of_molecules], dtype=int64)
        set_of_molecules.all_symbolic_numbers = concatenate([molecule.symbolic_numbers(self) for molecule in set_of_molecules], axis=0)
        set_of_molecules.multiplied_all_symbolic_numbers = set_of_molecules.all_symbolic_numbers * len(self.value_symbols)
        for data in self.necessarily_data:
            setattr(set_of_molecules, "all_" + data, concatenate([getattr(molecule, data)() for molecule in set_of_molecules], axis=0))

    def control_parameters(self, file, all_symbolic_numbers):
        missing_atoms_in_parameters = [self.atomic_types[sym_num] for sym_num in range(len(self.atomic_types)) if sym_num not in all_symbolic_numbers]
        if missing_atoms_in_parameters:
            exit(colored("No {} atoms in {}. Parameterization is not possible.".format(", ".join(missing_atoms_in_parameters), file), "red"))

    def __repr__(self):
        return self.__class__.__name__

    def load_parameters(self, parameters_file):
        print("Loading of parameters from {}...".format(parameters_file))
        with open(parameters_file, "r") as parameters_file:
            parameters_file = parameters_file.read()
            for keyword in ["<<global>>", "<<key>>", "<<value_symbol>>", "<<value>>", "<<end>>"]:
                if keyword not in parameters_file:
                    exit(colored("File with parameters is wrong! File not contain keywords <<global>>, <<key>>, "
                                 "<<value_symbol>>, <<value>> and <<end>>!\n", "red"))
            parameters_file = parameters_file.splitlines()
            method_in_parameters_file = parameters_file[0].split()[1]
            if self.__class__.__name__ != method_in_parameters_file:
                exit(colored("These parameters are for method {} but you want to calculate charges by method {}!\n"
                             .format(method_in_parameters_file, self.__class__.__name__), "red"))
            length_corrections = {"Angstrom": 1.0, "Bohr_radius": 1.8897261245}
            try:
                self.length_correction_key = parameters_file[1].split()[1]
                self.length_correction = length_corrections[self.length_correction_key]
            except KeyError:
                exit(colored("Unknown length type {} in parameter file. Please, choice one of {}.\n"
                             .format(length_correction, ", ".join(length_corrections.keys())), "red"))
            key_index = parameters_file.index("<<key>>")
            value_symbol_index = parameters_file.index("<<value_symbol>>")
            value_index = parameters_file.index("<<value>>")
            end_index = parameters_file.index("<<end>>")
            self.parameters = {}
            for line in parameters_file[3: key_index]:
                key, value = line.split()
                self.parameters[key] = float64(value)
            self.keys = [line for line in parameters_file[key_index + 1: value_symbol_index]]
            self.atomic_types_pattern = "_".join([key for key in self.keys])
            self.value_symbols = [line for line in parameters_file[value_symbol_index + 1: value_index]]
            self.atomic_types = []
            for line in parameters_file[value_index + 1: end_index]:
                atomic_type_data = line.split()
                for x in range(len(self.value_symbols)):
                    atomic_type = "~".join(atomic_type_data[:len(self.keys)])
                    self.atomic_types.append(atomic_type)
                    self.parameters["{}_{}".format(atomic_type, self.value_symbols[x])] = float(atomic_type_data[x + len(self.keys)])
        self.atomic_types = sorted(tuple(set(self.atomic_types)))
        parameters_values = [0 for _ in range(len(self.parameters))]
        writed_glob_par = 1
        for key, value in self.parameters.items():
            if key[0].isupper():
                atomic_type, value_symbol = key.split("_")
                parameters_values[self.atomic_types.index(atomic_type) * len(self.value_symbols) + self.value_symbols.index(value_symbol)] = value
            else:
                parameters_values[-1] = value
                writed_glob_par += 1
        self.parameters_values = array(parameters_values, dtype=float64)
        print(colored("ok\n", "green"))

#####################################################################
@jit(nopython=True, cache=True)
def eem_calculate(distances, symbols, all_num_of_atoms, parameters_values):
    results = empty(symbols.size, dtype=float64)
    kappa = parameters_values[-1]
    formal_charge = 0
    index = 0
    counter_distance = 0
    counter_symbols = 0
    for num_of_atoms in all_num_of_atoms:
        new_index = index + num_of_atoms
        num_of_atoms_add_1 = num_of_atoms + 1
        matrix = empty((num_of_atoms_add_1, num_of_atoms_add_1), dtype=float64)
        vector = empty(num_of_atoms_add_1, dtype=float64)
        for x in range(num_of_atoms):
            matrix[num_of_atoms][x] = matrix[x][num_of_atoms] = 1.0
            symbol = symbols[counter_symbols]
            counter_symbols += 1
            matrix[x][x] = parameters_values[symbol + 1]
            vector[x] = -parameters_values[symbol]
            for y in range(x+1, num_of_atoms):
                matrix[x][y] = matrix[y][x] = kappa / distances[counter_distance]
                counter_distance += 1
        matrix[num_of_atoms, num_of_atoms] = 0.0
        vector[-1] = formal_charge
        results[index: new_index] = solve(matrix, vector)[:-1] # poresit
        index = new_index
    return results


class EEM(Methods):
    def calculate(self, set_of_molecules):
        self.results = eem_calculate(set_of_molecules.all_distances, set_of_molecules.multiplied_all_symbolic_numbers,
                                     set_of_molecules.all_num_of_atoms, self.parameters_values)

##########################################################################################


@jit(nopython=True, cache=True)
def sfkeem_calculate(distances, symbols, all_num_of_atoms, parameters_values):
    results = empty(symbols.size, dtype=float64)
    sigma = parameters_values[-1]
    formal_charge = 0
    index = 0
    counter_distance = 0
    counter_symbols = 0
    for num_of_atoms in all_num_of_atoms:
        new_index = index + num_of_atoms
        num_of_atoms_add_1 = num_of_atoms + 1
        matrix = ones((num_of_atoms_add_1, num_of_atoms_add_1), dtype=float64)
        vector = empty(num_of_atoms_add_1, dtype=float64)
        for x in range(num_of_atoms):
            symbol = symbols[counter_symbols]
            counter_symbols += 1
            vector[x] = - parameters_values[symbol]
            value = parameters_values[symbol + 1]
            for y in range(num_of_atoms):
                matrix[x][y] *= value
                matrix[y][x] *= value
        for x in range(num_of_atoms):
            matrix[x][x] = 2.0 * sqrt(matrix[x][x])
            for y in range(x+1, num_of_atoms):
                matrix[x][y] = matrix[y][x] = 2.0 * sqrt(matrix[x][y]) / cosh(distances[counter_distance] * sigma) # poresit, nejde to rychleji? ale asi nejde...
                counter_distance += 1
        vector[-1] = formal_charge
        matrix[num_of_atoms, num_of_atoms] = 0.0
        results[index: new_index] = solve(matrix, vector)[:-1]
        index = new_index
    return results


class SFKEEM(Methods):
    def calculate(self, set_of_molecules):
        self.results = sfkeem_calculate(set_of_molecules.all_distances, set_of_molecules.multiplied_all_symbolic_numbers,
                                     set_of_molecules.all_num_of_atoms, self.parameters_values)

##########################################################################################
@jit(nopython=True, cache=True)
def qeq_calculate(distances, all_symbols, all_num_of_atoms, parameters_values):
    results = empty(all_symbols.size, dtype=float64)
    formal_charge = 0
    index = 0
    counter_distance = 0
    for num_of_atoms in all_num_of_atoms:
        new_index = index + num_of_atoms
        symbols = all_symbols[index: new_index]
        num_of_atoms_add_1 = num_of_atoms + 1
        matrix = empty((num_of_atoms_add_1, num_of_atoms_add_1), dtype=float64)
        vector = empty(num_of_atoms_add_1, dtype=float64)
        matrix[num_of_atoms, num_of_atoms] = 0.0
        vector_rad = empty(num_of_atoms, dtype=float64)
        for x in range(num_of_atoms):
            vector_rad[x] = parameters_values[symbols[x] + 2]
            matrix[x][num_of_atoms] = 1.0
            matrix[num_of_atoms][x] = 1.0
        for i in range(num_of_atoms):
            symbol = symbols[i]
            matrix[i][i] = parameters_values[symbol + 1]
            vector[i] = -parameters_values[symbol]
            for j in range(i + 1, num_of_atoms):
                rad1 = vector_rad[i]
                rad2 = vector_rad[j]
                distance = distances[counter_distance]
                matrix[i][j] = matrix[j][i] = erf(sqrt(rad1 * rad2 / (rad1 + rad2)) * distance) / distance
                counter_distance += 1
        vector[-1] = formal_charge
        results[index: new_index] = solve(matrix, vector)[:-1]
        index = new_index
    return results


class QEq(Methods):
    def calculate(self, set_of_molecules):
        self.results = qeq_calculate(set_of_molecules.all_distances, set_of_molecules.multiplied_all_symbolic_numbers,
                                     set_of_molecules.all_num_of_atoms, self.parameters_values)


##########################################################################################
@jit(nopython=True, cache=True)
def gm_calculate(all_bonds, all_symbols, all_num_of_atoms, all_num_of_bonds, parameters_values):
    results = empty(all_symbols.size, dtype=float64)
    formal_charge = 0 #???? neni tam
    index_a = 0
    index_b = 0
    for num_of_atoms, num_of_bonds in zip(all_num_of_atoms, all_num_of_bonds):
        new_index_b = index_b + num_of_bonds
        new_index_a = index_a + num_of_atoms
        bonds = all_bonds[index_b: new_index_b]
        symbols = all_symbols[index_a: new_index_a]
        work_electronegativies = zeros(num_of_atoms, dtype=float64)
        work_charges = zeros(num_of_atoms, dtype=float64)
        for alpha in range(4):
            for x in range(num_of_atoms):
                work_charge = work_charges[x]
                parameter_key = symbols[x]
                work_electronegativies[x] = parameters_values[parameter_key] + parameters_values[parameter_key+1] * work_charge + parameters_values[parameter_key+2] * work_charge ** 2
            for bond_index in range(0, len(bonds), 2):
                atom1, atom2 = bonds[bond_index: bond_index+2]
                if work_electronegativies[atom1] < work_electronegativies[atom2]:
                    chi_plus = parameters_values[symbols[atom1]+3]
                else:
                    chi_plus = parameters_values[symbols[atom2]+3]
                charge_diff = ((work_electronegativies[atom1] - work_electronegativies[atom2]) / chi_plus) * 0.5 ** alpha
                work_charges[atom1] -= charge_diff
                work_charges[atom2] += charge_diff
        results[index_a: new_index_a] = work_charges
        index_a = new_index_a
        index_b = new_index_b
    return results


class GM(Methods):
    def calculate(self, set_of_molecules):
        self.results = gm_calculate(set_of_molecules.all_bonds_without_bond_type, set_of_molecules.multiplied_all_symbolic_numbers,
                                    set_of_molecules.all_num_of_atoms, set_of_molecules.all_num_of_bonds_mul_two,
                                    self.parameters_values)











































#@jit(nopython=True, cache=True)
def mgc_calculate(all_num_of_atoms, all_mgc_matrix, all_symbols, parameters_values):
    results = empty(all_symbols.size, dtype=float64)
    # no formal charge
    index = 0
    counter_symbols = 0
    counter = 0
    for num_of_atoms in all_num_of_atoms:
        new_index = index + num_of_atoms
        vector = empty(num_of_atoms, dtype=float64)
        matrix = empty((num_of_atoms, num_of_atoms), dtype=float64)
        for x in range(num_of_atoms):
            vector[x] = parameters_values[all_symbols[counter_symbols]]
            counter_symbols += 1
            for y in range(x, num_of_atoms):
                matrix[x][y] = matrix[y][x] = all_mgc_matrix[counter]
                counter += 1
        # ./mach.py --mode parameterization_find_args --optimization_method minimization --data_dir asldfjalksdf -f --path  data/MGC/1/  --num_of_molecules 1
        print((solve(matrix, vector) - vector)/(prod(vector)**(1/num_of_atoms)))
        from sys import exit ; exit()
        results[index: new_index] = (solve(matrix, vector) - vector)/(prod(vector)**(1/num_of_atoms))
        index = new_index
        # je nanic
    return results



class MGC(Methods):
    def calculate(self, set_of_molecules):
        self.results = mgc_calculate(set_of_molecules.all_num_of_atoms, set_of_molecules.all_MGC_matrix, set_of_molecules.multiplied_all_symbolic_numbers, self.parameters_values)




