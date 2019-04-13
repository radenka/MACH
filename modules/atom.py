class Atom:
    def __init__(self, coordinates, atomic_symbol, atomic_symbol_high_bond, index, classifier, atom_type):
        self.coordinates = coordinates
        self.plain = atomic_symbol
        # self.hbo = atomic_symbol_high_bond
        self.index = index
        at_type = []
        at_type.append(atom_type)
        setattr(self, classifier, at_type)

    def get_representation(self, pattern):
        if pattern == "plain":
            return self.plain
        # elif pattern == "hbo":
        #     return self.hbo
        else:
            if type(getattr(self, pattern)) == list:
                return tuple(getattr(self, pattern))
            elif type(getattr(self, pattern)) == tuple:
                return list(getattr(self, pattern))

