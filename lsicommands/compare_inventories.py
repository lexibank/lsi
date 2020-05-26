"""
Compare the phoneme inventories from LSI with ASJP (as lower bound) and PHOIBLE (as upper bound).

Uses
- PHOIBLE data from https://github.com/cldf-datasets/phoible/releases/tag/v2.0.1
- ASJP data from https://github.com/lexibank/asjp/releases/tag/v19.1
"""
import collections

import pycldf
from clldutils.clilib import PathType
from cldfbench.cli_util import add_catalog_spec
from termcolor import colored

from lexibank_lsi import Dataset


def register(parser):
    parser.add_argument(
        'asjp_cldf',
        type=PathType(type='file'),
        help='path to metadata.json of ASJP as CLDF dataset')
    parser.add_argument(
        'phoible_cldf',
        type=PathType(type='file'),
        help='path to metadata.json of PHOIBLE as CLDF dataset')
    add_catalog_spec(parser, 'clts')


def run(args):
    assert args.clts
    clts = args.clts.api

    lsi = Dataset(args).cldf_reader()
    lsi_langs = {l['ID']: l for l in lsi['LanguageTable']}

    lsi_inventories = collections.defaultdict(collections.Counter)
    for form in lsi['FormTable']:
        lsi_inventories[form['Language_ID']].update(form['Segments'])

    lsi_glottocodes = set(l['Glottocode'] for l in lsi_langs.values())

    #
    # Now prepare the PHOIBLE data for comparison:
    #
    phoible = pycldf.Dataset.from_metadata(args.phoible_cldf)
    phoible_langs = {
        l['ID']: l for l in phoible['LanguageTable'] if l['Glottocode'] in lsi_glottocodes}
    phoible_inventories = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    phoible_params = {p['ID']: p['Name'] for p in phoible['ParameterTable']}
    for val in phoible['ValueTable']:  # Values in PHOIBLE indicate presence of a segment in an inventory.
        if val['Language_ID'] in phoible_langs:
            phoible_inventories[phoible_langs[val['Language_ID']]['Glottocode']][val['Language_ID']].update(
                [phoible_params[val['Parameter_ID']]])

    # We select the PHOIBLE inventory with the smallest number of segments: (maybe we should go for average rather?)
    phoible_inventories_per_glottocode = {}
    clts_phoible = clts.transcriptiondata('phoible')
    for gc, invs in phoible_inventories.items():
        for lid, inv in sorted(invs.items(), key=lambda i: len(i[1])):
            stats = collections.Counter()
            for grapheme in inv:
                try:
                    stats.update([clts_phoible.resolve_grapheme(grapheme).__class__.__name__])
                except KeyError as e:
                    print(e)  # FIXME: We shouldn't have to discard so many segments here!
            phoible_inventories_per_glottocode[gc] = (lid, stats)
            break

    #
    # Prepare the ASJP data for comparison:
    #
    asjp = pycldf.Dataset.from_metadata(args.asjp_cldf)
    asjp_langs = {
        l['ID']: l['Glottocode'] for l in asjp['LanguageTable'] if l['Glottocode'] in lsi_glottocodes}
    asjp_inventories = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for form in asjp['FormTable']:
        if form['Language_ID'] in asjp_langs:
            asjp_inventories[asjp_langs[form['Language_ID']]][form['Language_ID']].update(
                form['Segments'])

    # We select the ASJP wordlist with the biggest number of tokens per Glottocode.
    asjp_inventories_per_glottocode = {}
    for gc, invs in asjp_inventories.items():
        for lid, inv in sorted(invs.items(), key=lambda i: -sum(i[1].values())):
            stats = collections.Counter()
            for grapheme in inv:
                stats.update([clts.bipa[grapheme].__class__.__name__])
            asjp_inventories_per_glottocode[gc] = (lid, stats)
            break

    #
    # ... and compare:
    #
    for lid, inv in lsi_inventories.items():
        stats = collections.Counter()
        for grapheme in inv:
            stats.update([clts.bipa[grapheme].__class__.__name__])

        if lsi_langs[lid]['Glottocode'] in asjp_inventories_per_glottocode\
                and lsi_langs[lid]['Glottocode'] in phoible_inventories_per_glottocode:
            asjp_lid, asjp_stats = asjp_inventories_per_glottocode[lsi_langs[lid]['Glottocode']]
            phoibe_lid, phoible_stats = phoible_inventories_per_glottocode[lsi_langs[lid]['Glottocode']]

            print('Comparing {} with {} from ASJP and {} from PHOIBLE'.format(lid, asjp_lid, phoible_langs[phoibe_lid]['Name']))
            for k, v in stats.items():
                if k == 'Marker':
                    continue
                if (k in asjp_stats) and (k in phoible_stats):
                    asjp_v = asjp_stats[k]
                    phoible_v = phoible_stats[k]
                    text = '{}: {} {} {} {} {}'.format(
                        k,
                        asjp_v,
                        '<=' if asjp_v <= v else '>',
                        v,
                        '<=' if v <= phoible_v else '>',
                        phoible_v)
                    print(colored(text, 'red' if v < asjp_v or v > phoible_v else 'green'))
            print('')


