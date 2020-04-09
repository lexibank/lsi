"""
Compute partial cognates and alignments and create a wordlist.
"""

from lingpy import *
from lexibank_lsi import Dataset
from pylexibank import progressbar
from tabulate import tabulate

def run(args):
    
    ds = Dataset(args)
    wl = Wordlist.from_cldf(str(ds.cldf_specs().metadata_path))
    args.log.info('[i] loaded wordlist')

    color = Model('color')

    html = '<html><head></head><body>{text}</body></html>'
    text = '<h1> Phonemes in the LSI</h1>'
    for lang in progressbar(wl.cols):
#        text += '<h2 name="{0}">Language {0}</h2>'.format(
#                lang)
        idxs = wl.get_list(col=lang, flat=True)
        text += '<table>'
        text += '<tr><th>Doculect</th><th>Segments</th></tr>'
        phons = []
        for idx in idxs:
            tks = wl[idx, 'tokens']
            for tk in tks:
                if tk not in phons:
                    phons.append(tk)

        try:
            cols = tokens2class(phons, color)
        except:
            cols = ['gray' for x in phons]
        row = [
            lang,
            ' '.join([
                '<span style="display:table-cell;padding:2px;width:20px;background-color:{0};">{1}</span>'.format(
                    a, b) for a, b in zip(cols, phons)])
                ]
        text += '<tr>'+''.join([
                    '<td style="padding:2px;border:1px solid gray">{0}</td>'.format(
                        x) for x in row])+'</tr>'
        text += '</table>'

    with open(ds.dir.joinpath('phonemes.html').as_posix(), 'w') as f:
        f.write(html.format(text=text))


