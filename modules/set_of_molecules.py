from sys import exit
from termcolor import colored
from .molecule import Molecule, MoleculeChg
from collections import Counter
from tabulate import tabulate


def sort(a, b):
    if a > b:
        return b, a
    return a, b


class SetOfMolecules:
    def __init__(self, file, method=None, from_charges_file=False):
        print("Loading of set of molecules from {}...".format(file))
        self.molecules = []
        self.file = file
        if from_charges_file:
            self.load_molecules_from_charges_file()
        else:
            self.method = method
            with open(file, "r") as sdf:
                molecules_data = sdf.read()
            if molecules_data[-5:].strip() != "$$$$":
                exit(colored("{} is not valid sdf file. Last line is not $$$$.".format(sdf.name), "red"))
            molecules_data = [x.splitlines() for x in molecules_data.split("$$$$\n")]
            from time import time
            start = time()
            for molecule_data in molecules_data[:-1]:
                type_of_sdf_record = molecule_data[3][-5:]
                if type_of_sdf_record == "V2000":
                    self.load_sdf_v2000(molecule_data)
                elif type_of_sdf_record == "V3000":
                    self.load_sdf_v3000(molecule_data)
                else:
                    exit(colored("{} if not valid sdf file.".format(sdf), "red"))
            print(time() - start)
            self.num_of_molecules = len(self.molecules)
            self.num_of_atoms = sum([len(molecule) for molecule in self.molecules])
        print(colored("ok\n", "green"))

    def load_sdf_v2000(self, molecular_data):
        name = molecular_data[0]
        info_line = molecular_data[3]
        num_of_atoms = int(info_line[:3])
        num_of_bonds = int(info_line[3:6])
        atomic_symbols, atomic_coordinates, bonds = [], [], []
        for atom_line in molecular_data[4: num_of_atoms + 4]:
            line = atom_line.split()
            atomic_coordinates.append((float(line[0]), float(line[1]), float(line[2])))
            atomic_symbols.append(line[3])
        for bond_line in molecular_data[num_of_atoms + 4: num_of_atoms + num_of_bonds + 4]:
            bonds.append((sort(int(bond_line[:3]), int(bond_line[3:6])), int(bond_line[8])))
        self.molecules.append(Molecule(name, num_of_atoms, atomic_symbols, atomic_coordinates, bonds, method=self.method))

    def load_sdf_v3000(self, molecular_data):
        name = molecular_data[0]
        info_line = molecular_data[5].split()
        num_of_atoms = int(info_line[3])
        num_of_bonds = int(info_line[4])
        atomic_symbols, atomic_coordinates, bonds = [], [], []
        for atom_line in molecular_data[7: num_of_atoms + 7]:
            line = atom_line.split()
            atomic_coordinates.append((float(line[4]), float(line[5]), float(line[6])))
            atomic_symbols.append(line[3])
        for bond_line in molecular_data[num_of_atoms + 9: num_of_atoms + num_of_bonds + 9]:
            line = bond_line.split()
            bonds.append((sort(int(line[4]), int(line[5])), int(line[3])))
        self.molecules.append(Molecule(name, num_of_atoms, atomic_symbols, atomic_coordinates, bonds, method=self.method))

    def __len__(self):
        return self.num_of_molecules

    def __getitem__(self, index):
        return self.molecules[index]

    def __iter__(self):
        return iter(self.molecules)

    def info(self, atomic_types_pattern):
        counter = Counter()
        if atomic_types_pattern == "atom":
            for molecule in self.molecules:
                counter.update(molecule.atomic_symbols)
        elif atomic_types_pattern == "atom_high_bond":
            for molecule in self.molecules:
                counter.update(molecule.atomic_symbols_high_bond)
        table = []
        for atom, count in sorted(counter.items()):
            table.append((atom, count, round(count / (self.num_of_atoms / 100), 2)))
        print("""
Statistics data from set of molecules from {}
Number of molecules:   {}
Number of atoms:       {}
Number of atoms type:  {}\n
{}\n""".format(self.file, self.num_of_molecules, self.num_of_atoms, len(counter),
           tabulate(table, headers=["Type", "Number", "%"])))

    def load_molecules_from_charges_file(self):
        with open(self.file, "r") as charges_file:
            molecules_data = [[line.split() for line in molecule.splitlines()]
                              for molecule in charges_file.read().split("\n\n")[:-1]]
            self.num_of_atoms = 0
            for molecule in molecules_data:
                name = molecule[0][0]
                num_of_atoms = int(molecule[1][0])
                self.num_of_atoms += num_of_atoms
                atomic_symbols = [atom_line[1] for atom_line in molecule[2:]]
                charges = [float(atom_line[2]) for atom_line in molecule[2:]]
                self.molecules.append(MoleculeChg(name, num_of_atoms, atomic_symbols, charges))
            self.num_of_molecules = len(self.molecules)


