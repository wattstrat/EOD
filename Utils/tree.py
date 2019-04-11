from collections import defaultdict


def Tree(): return defaultdict(Tree)


class AlreadyAdded(Exception):
    def __init__(self, child_node, parent_node):
        super().__init__()
        self._child = child_node
        self._parent = parent_node


class DepTree(object):
    def __init__(self):
        self._dep_tree = {'_parent': None, '_name': None}
        self._id = {None: self._dep_tree}
        self._leaf = {}

    def __iter__(self):
        # iter over DP => iter over leaf name
        return iter(self._leaf.keys())

    def __getitem__(self, key):
        return self._id[key]

    def __eq__(self, other):
        return DepTree._filterNode(self._dep_tree) == DepTree._filterNode(other._dep_tree)

    @staticmethod
    def _filterNode(h):
        def hashlist(h):
            if not isinstance(h, dict):
                return h
            if sum([len(v) for v in h.values()]) == 0:
                return set(h.keys())
            return h

        if not isinstance(h, dict):
            return h
        return {k: hashlist(DepTree._filterNode(v)) for k, v in h.items() if k not in ["_parent", "_name"]}

    def __repr__(self):
        return repr(DepTree._filterNode(self._dep_tree))

    def _ptr(self, t, filt=[], depth=0):
        """ print a tree """
        node = ((k, v) for k, v in t.items() if k not in filt)

        for k, v in node:
            print("%s (%2d) %s" % ("".join(depth * ["    "]), depth, k), end="")
            if k in self._leaf:
                print('*')
            else:
                print('')
            self._ptr(v, filt, depth + 1)

    def _print(self, depth=0):
        self._ptr(self._dep_tree, ["_parent", "_name"], 0)

    def add_dep(self, child_var, parent_var=None):
        parent_node = None
        try:
            parent_node = self._id[parent_var]
        except KeyError:
            # No variable dep in tree : adding a leaf to ROOT
            parent_node = self._add_leaf(self._dep_tree, parent_var)

        if not isinstance(child_var, (list, set)):
            child_var = [child_var]

        if len(child_var) == 0:
            return

        # Are we a leaf
        lpn = (parent_node is not self._dep_tree) and (len(parent_node) == 2)

        for cv in child_var:
            try:
                cn = self._id[cv]
                if cn['_parent'] is not self._dep_tree:
                    # Well, our child is somebody other child
                    if lpn and len(parent_node) > 2:
                        self._leaf.pop(parent_var, None)
                    raise AlreadyAdded(cn, parent_node)
                parent_node[cv] = cn['_parent'].pop(cv)
                cn['_parent'] = parent_node

            except KeyError:
                self._add_leaf(parent_node, cv)

        # If parent_var is a leaf => not a leaf anymore
        if lpn:
            self._leaf.pop(parent_var, None)

    def _add_leaf(self, pn, cv):
        if isinstance(cv, tuple) and len(cv) == 2 and isinstance(cv[1], DepTree):
            return self._add_DepTree(pn, cv[0], cv[1])
        elif isinstance(cv, DepTree) and cv._dep_tree['_name'] is not None:
            return self._add_DepTree(pn, cv._dep_tree['_name'], cv[1])
        else:
            cn = {'_name': cv, '_parent': pn}
            pn[cv] = cn
            self._id[cv] = cn
            self._leaf[cv] = cn
            return cn
        return None

    def _add_DepTree(self, parent, name, DT):
        inter = set(self._id) & set(DT._id) - set({None})
        if name in DT._id:
            # name should not be in DT
            raise AlreadyAdded(name, parent)
        if len(inter) > 1:
            # intersection should be empty
            raise AlreadyAdded(inter, parent)

        DT._dep_tree['_name'] = name
        DT._dep_tree['_parent'] = parent
        DT._id[name] = DT._id.pop(None, DT._dep_tree)

        self._id.update(DT._id)
        self._leaf.update(DT.leaf)

        # Add back the ROOT
        DT._id[None] = DT._dep_tree
        parent[name] = DT._dep_tree

    def add_dep_map(self, mapping):
        if not isinstance(mapping, dict):
            mapping = {None: mapping}

        for k, v in mapping.items():
            if isinstance(v, dict):
                self.add_dep_map(v)
                v = list(v.keys())
            self.add_dep(v, k)

    @property
    def leaf(self):
        return self._leaf
