"""
The long tail of phonetic diversity in the LSI.

How many sounds appear in how many languages in the survey?

Usage:
    cldfbench lsi.sound_distribution | termgraph
"""
import itertools
import collections

from lexibank_lsi import Dataset


def run(args):
    lsi = Dataset(args).cldf_reader()
    sounds_per_language = collections.defaultdict(set)
    for form in lsi.iter_rows('FormTable', 'form', 'languageReference', 'segments'):
        for sound in form['segments']:
            sounds_per_language[sound].add(form['languageReference'])
    args.log.info('How many sounds appear in how many languages in the survey?')
    agg = 0
    for nlangs, sounds in itertools.groupby(
            sorted(sounds_per_language.items(), key=lambda i: len(i[1])), lambda i: len(i[1])):
        if nlangs < 50:
            print('{},{}'.format(nlangs, sum(1 for _ in sounds)))
        else:
            agg += sum(1 for _ in sounds)
    print('>50,{}'.format(agg))
