import json
import ROOT
import os
import numpy as np
import pandas as pd
import python.plotting as plot
from eftanalysis import EFTAnalysis
from python.tools import Matrix
from collections import OrderedDict
from argparse import ArgumentParser

# default ordering for Wilson coefficients
wilson_coeffs = ['cw','cg',                                    # 3 gauge boson
    'chb','chw','chg','chwb',                                  # 2 higgs 3 gauge boson
    'chbox','chdd',                                            # 4 higgs 2 derivatives
    'ctgre','ctwre','ctbre','cbgre','cbwre',                   # 1 higgs 2 fermion 1 gauge boson
    'cbhre','cthre',                                           # 3 higgs 2 fermion
    'chbq','cht','chq1','chq3','chtbre',                       # 2 higgs 2 fermion (heavy) 1 derivative
    'che','chl1','chl3','chd','chu','chj1','chj3',             # 2 higgs 2 fermion (light) 1 derivative
    'cll1','clj1','clj3','clu','cld','cql1','cql3','cte','ctl',# 4 fermion
    'cqq1','cqt1','cqt8','ctt',                                # 4 quark (heavy)
    'cqu1','cqu8','cqd1','cqd8','ctj1','ctj8','cqj11',         # 4 quark (2h2l)
    'cqj18','cqj31','cqj38','ctd1','ctd8','ctu1','ctu8',       # 4 quark (2h2l)
    'cju1','cju8','cjd1','cjd8','cjj11','cjj18','cjj31',       # 4 quark (light)
    'cjj38','cdd1','cdd8','cud1','cud8','cuu1','cuu8']         # 4 quark (light)

def calculateContributions(eftanalysis, channel_groups=None, min_eigval=0., POIs=None, sort_poi=False, external_info=None, external_rotation=None):
    if channel_groups is None:
        channel_groups = OrderedDict([(ch, {'channels':[ch]}) for ch in eftanalysis.channels])
    info_matrix = eftanalysis.info_matrix
    if external_info is not None:
        external_label, external_info_matrix, external_color = external_info.split(':')
        external_info_matrix = Matrix.fromJSON(external_info_matrix)
        info_matrix = info_matrix + external_info_matrix

    if eftanalysis.basis_rotation is None and external_rotation is None:
        if POIs is None:
            POIs = info_matrix.xpars
        else:
            POIs = [p for p in POIs if p in info_matrix.xpars]
    else:
        rot = eftanalysis.basis_rotation if external_rotation is None else Matrix.fromJSON(external_rotation)
        info_matrix = rot * info_matrix * rot.T
        if POIs is None:
            if rot.eigenvalues is None:
                POIs = rot.ypars
            else:
                POIs = [rot.ypars[i] for i,ev in enumerate(rot.eigenvalues) if ev>min_eigval]
        else:
            POIs = [p for p in POIs if p in rot.ypars]

    # if POIs are Wilson coefficients, sort them like the list above
    if sort_poi:
        POIs = sorted(POIs, key=lambda x: wilson_coeffs.index(x) if x in wilson_coeffs else -1)

    res = OrderedDict([
        (p, OrderedDict([(cg, 0.) for cg in channel_groups])) 
        for p in POIs])

    for cg in channel_groups:
        for ch in channel_groups[cg]['channels']:
            info = eftanalysis.inputs[ch]['info_matrix']
            if eftanalysis.basis_rotation is not None or external_rotation is not None:
                rotation = rot.loc[POIs,:]
                info = rotation * info * rotation.T

            for p in POIs:
                if p in info.xpars:
                    res[p][cg] += info.loc[p,p]
    if external_info is not None:
        if eftanalysis.basis_rotation is not None or external_rotation is not None:
            rotation = rot.loc[POIs,:]
            external_info_matrix = rotation * external_info_matrix * rotation.T
        for p in POIs:
            res[p][external_label] = external_info_matrix.loc[p,p] if p in external_info_matrix.xpars else 0.

    return res


def makeContributionPlot(eftanalysis, channel_groups=None, min_eigval=0., POIs=None, sort_poi=False, translate_poi=None, external_info=None, external_rotation=None, text_size=1.0, align_labels=False):
    if channel_groups is None:
        channel_groups = OrderedDict([(ch, {'channels':[ch]}) for ch in eftanalysis.channels])
    for i,cg in enumerate(channel_groups):
        if not 'color' in channel_groups[cg]:
            channel_groups[cg]['color'] = i+2

    res = calculateContributions(eftanalysis, channel_groups, min_eigval, POIs, sort_poi, external_info, external_rotation)
    if external_info is not None:
        external_label, external_info_matrix, external_color = external_info.split(':')
        channel_groups[external_label] = {'color': eval(external_color) if not external_color[0]=='#' else ROOT.TColor.GetColor(external_color)}

    ordering = ['H #rightarrow #gamma#gamma','W#gamma','Z #rightarrow #nu#nu','WW','t#bar{t}','t(#bar{t})X','Incl. jet','EWPO']
    ordering += [cg for cg in channel_groups if not cg in ordering]
    channel_groups = OrderedDict([(k,channel_groups[k]) for k in ordering if k in channel_groups])

    ROOT.gROOT.SetBatch(ROOT.kTRUE)
    plot.ModTDRStyle()
    ROOT.gStyle.SetPadLeftMargin(0.07)
    ROOT.gStyle.SetPadRightMargin(0.02)
    ROOT.gStyle.SetPadBottomMargin(0.08)
    ROOT.gStyle.SetLegendTextSize(0.03)
    ROOT.gStyle.SetLineScalePS(0.8)
    ROOT.gStyle.SetFrameLineWidth(3)

    colors = dict([(cg, channel_groups[cg]['color']) for cg in channel_groups])

    h_axes = ROOT.TH1D('h_axes', ';;Fractional contribution f_{ #lower[-0.1]{j}}^{ #lower[0.1]{#alpha}}', len(res.keys()), 0, len(res.keys()))
    h_axes.SetMaximum(1)
    h_axes.GetXaxis().SetLabelSize(0.04*text_size)
    h_axes.SetTitleSize(0.04,'y')
    h_axes.GetYaxis().CenterTitle(True)
    h_axes.GetYaxis().SetTitleOffset(0.9)

    stack = ROOT.THStack()
    legend = ROOT.TLegend(*([0.26, 0.95, 0.95, 0.98, '', 'NBNDC']))
    legend.SetNColumns(len(channel_groups.keys()))

    hists = OrderedDict()
    for cg in channel_groups:
        hists[cg] = ROOT.TH1D('h_%s' % cg, 'h_%s' % cg, len(res.keys()), 0, len(res.keys()))
        hists[cg].SetFillColor(colors[cg])
        hists[cg].SetBarWidth(0.6)
        hists[cg].SetBarOffset(0.2)
        hists[cg].SetLineWidth(0)
        legend.AddEntry(hists[cg], ' '+cg, 'F')
        stack.Add(hists[cg])

    if translate_poi is not None and os.path.isfile(translate_poi):
        with open(translate_poi,'r') as f:
            translate_poi = json.load(f)
    else:
        translate_poi = dict()

    for i,poi in enumerate(res.keys()):
        bin_label = translate_poi[poi] if poi in translate_poi else poi
        h_axes.GetXaxis().SetBinLabel(i+1, '#color[0]{#int } '+bin_label if align_labels else bin_label)
        for cg in channel_groups:
            hists[cg].SetBinContent(i+1, res[poi][cg]/sum(res[poi].values()))

    h_axes.LabelsOption('v','X')

    return h_axes, stack, legend


def drawResults(eftanalysis, filepath, channel_groups, min_eigval, POIs=None, sort_poi=False, translate_poi=None, external_info=None, external_rotation=None, text_size=1., align_labels=False, title='#bf{CMS} #it{Preliminary}'):
    h_axes,stack,legend = makeContributionPlot(eftanalysis, channel_groups, min_eigval, POIs, sort_poi, translate_poi, external_info, external_rotation, text_size, align_labels)
    f = 1.5 if filepath[-4:] == '.png' else 1
    c = ROOT.TCanvas('c','c',int(f*1200),int(f*500))
    pads = plot.OnePad()
    pads[0].SetTickx()
    pads[0].SetTicky()

    h_axes.Draw('bar')
    stack.Draw('bar same')
    legend.Draw('same')

    plot.DrawTitle(pads[0], title, 1)

    pads[0].GetFrame().Draw()
    pads[0].RedrawAxis()

    c.Print(filepath)


def printResults(eftanalysis, channel_groups, min_eigval, POIs=None):
    if channel_groups is None:
        channel_groups = OrderedDict([(ch, {'channels':[ch]}) for ch in eftanalysis.channels])
    res = calculateContributions(eftanalysis, channel_groups, min_eigval, POIs)
    header_str = '\n          {:>12}'.format('unc.') + ' {:>12}'*len(channel_groups.keys())
    header_str = header_str.format(*channel_groups.keys())
    print(header_str)
    print('-'*len(header_str))
    
    for poi in res.keys():
        Fii = sum(res[poi].values())
        line_str = ' {:<8} {:>12.3f}'.format(poi, 1./np.sqrt(Fii)) + ' {:>12.1%}'*len(channel_groups)
        line_str = line_str.format(*[res[poi][cg]/Fii for cg in channel_groups])
        print(line_str)
    print('-'*len(header_str)+'\n')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--input', '-i', help='EFTAnalysis cfg file')
    parser.add_argument('--channels', nargs='+', help='[name1]:[channel1,channel2,..]:[color1]')
    parser.add_argument('--output', '-o', help='output file')
    parser.add_argument('--min-eigval', default=0.04, type=float, help='remove directions with ev<min_eigval')
    parser.add_argument('--pois', nargs='+', default=None)
    parser.add_argument('--sort-poi', action='store_true', help='sort Wilson coefficients')
    parser.add_argument('--text-size', default=1, type=float)
    parser.add_argument('--translate', default='translate_root_SMEFTsim3.json')
    parser.add_argument('--external-info', default=None, help='[name]:[path to information matrix]:[color]')
    parser.add_argument('--external-rotation', help='path to rotation matrix (replaces the one in EFTAnalysis cfg file)')
    parser.add_argument('--align-labels', action='store_true')
    parser.add_argument('--pub', action='store_true')
    parser.add_argument('--supplementary', action='store_true')
    args = parser.parse_args()

    eftanalysis = EFTAnalysis.fromJSON(args.input, load_data=False)

    if args.channels:
        channel_groups = OrderedDict()
        for i,cg in enumerate(args.channels):
            if len(cg.split(':'))>2:
                name,channels,color = cg.split(':')
                channel_groups[name] = {'channels': channels.split(','), 'color': eval(color) if not color[0]=='#' else ROOT.TColor.GetColor(color)}
            else:
                name,channels = cg.split(':')
                channel_groups[name] = {'channels': channels.split(',')}
    else:
        channel_groups = None
    
    if args.output:
        out_dir,filename = os.path.split(args.output)
        if not out_dir=='' and not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        title = '#bf{CMS}' if args.pub else '#bf{CMS} #it{Supplementary}' if args.supplementary else '#bf{CMS} #it{Preliminary}'
        drawResults(eftanalysis, args.output, channel_groups, args.min_eigval, args.pois, args.sort_poi, args.translate, args.external_info, args.external_rotation, args.text_size, args.align_labels, title)
    else:
        printResults(eftanalysis, channel_groups, args.min_eigval)



