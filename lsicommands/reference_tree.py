"""
Compute the Glottolog reference tree.
"""
import collections

from cldfbench.cli_util import add_catalog_spec

from lexibank_lsi import Dataset


def register(parser):
    add_catalog_spec(parser, 'glottolog')


def run(args):
    assert args.glottolog
    glottolog = args.glottolog.api
    nodes = {l.id: l for l in glottolog.languoids()}

    lsi = Dataset(args).cldf_reader()
    langs_by_family = collections.defaultdict(dict)
    for l in lsi.iter_rows('LanguageTable', 'glottocode', 'name'):
        if not l['glottocode']:
            continue
        glang = nodes[l['glottocode']]
        family = nodes[glang.lineage[0][1]] if glang.lineage else glang
        langs_by_family[family.id][glang.id] = l['name'].replace('(', '_').replace(')', '_')

    trees = []
    for fid, tips in langs_by_family.items():
        # collect the newick trees for the relevant families,
        tree = nodes[fid].newick_node(nodes=nodes, template="{l.id}")
        # prune to the contained tips,
        tree.prune_by_names(list(tips), inverse=True)
        tree.remove_redundant_nodes(keep_leaf_name=True)
        tree.remove_internal_names()

        def rename(n):
            if n.name:
                n.name = tips[n.name]
                return

        # rename tip labels.
        tree.visit(visitor=rename)
        trees.append(tree.newick)
    print('({}):1;'.format(','.join(trees)))
