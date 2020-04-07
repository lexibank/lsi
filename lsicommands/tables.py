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
    text = '<h1> Data in the LSI</h1>'
    for concept in progressbar(wl.rows):
        text += '<h2 name="{0}">Concept {0}</h2>'.format(
                concept)
        idxs = wl.get_list(row=concept, flat=True)
        text += '<table>'
        text += '<tr><th>ID</th><th>Doculect</th><th>Value</th><th>Form</th><th>Segments</th></tr>'
        for idx in idxs:
            tks = wl[idx, 'tokens']
            try:
                cols = tokens2class(tks, color)
            except:
                cols = ['gray' for x in tks]
            row = [
                idx,
                wl[idx, 'doculect'],
                wl[idx, 'value'],
                wl[idx, 'form'],
                ' '.join([
                    '<span style="display:table-cell;padding:2px;width:20px;background-color:{0};">{1}</span>'.format(
                        a, b) for a, b in zip(cols, tks)])
                    ]
            text += '<tr>'+''.join([
                    '<td style="padding:2px;border:1px solid gray">{0}</td>'.format(
                        x) for x in row])+'</tr>'
        text += '</table>'

    with open(ds.dir.joinpath('tables.html').as_posix(), 'w') as f:
        f.write(html.format(text=text))


