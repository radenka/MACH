class Atom:
    def __init__(self, coordinates, atomic_symbol, atomic_symbol_high_bond, index, classifier, external_atom_type):
        self.coordinates = coordinates
        self.plain = atomic_symbol
        self.hbo = atomic_symbol_high_bond
        self.index = index
        # creates attribute self.external_atom_type
        if external_atom_type:
            at_type = []
            at_type.append(external_atom_type)
            setattr(self, classifier, at_type)

    def get_representation(self, pattern):
        # better to change to 'return getattr(self, pattern)'?
        if pattern == "plain":
            return self.plain
        elif pattern == "hbo":
            return self.hbo
        else:
            return getattr(self, pattern)

