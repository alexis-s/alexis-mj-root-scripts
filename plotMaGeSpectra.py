#!/usr/bin/env python

"""
Compare MC spectra produced with different dead layers.

27 Oct 2012 A. Schubert
"""

import os
import sys
import math
import glob

from ROOT import gROOT
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TFile
from ROOT import TH1D
from ROOT import TLegend


def get_hist_from_files(
    directory,
):
    """
    Return a histogram energy spectrum constructed from root files in directory.
    """
    root_file_names = glob.glob('%s/*.root' % directory)
    root_file_names.sort()

    gROOT.cd() # deal with TH1D/TFile/python scope issues!!

    name = directory.split('/')[0]
    hist = TH1D('%s' % name, '', 3000, 0, 3000)
    hist.Sumw2()
    hist.SetLineWidth(2)

    for root_file_name in root_file_names:

        root_file = TFile(root_file_name)
        tree = root_file.Get('fTree')

        hist.GetDirectory().cd()
        n_entries = tree.Draw(
            'fTotalEnergy*1e3 >> +%s' % hist.GetName(), 
            'fTotalEnergy>0', 
            'goff'
        )

        tree.GetEntry(0)
        a_max = tree.fMCRun.GetAmax()

    peak_energy = 2614.5
    if a_max == 214:
        #peak_energy = 1764.49
        peak_energy = 609.320

    peak_counts = hist.GetBinContent(
        hist.FindBin(peak_energy)
    )


    roi_counts = hist.Integral(
        hist.FindBin(2039),
        hist.FindBin(2041)-1,
    )

    ratio = roi_counts / peak_counts
    ratio_err = ratio * math.sqrt( 
        1.0/peak_counts +
        1.0/roi_counts
    )

    print '%s | %.1f-keV peak: %i +/- %.1f | roi: %i +/- %.1f | ratio: (%.2f +/- %.2f) x 10^-3' % (
        name,
        peak_energy,
        peak_counts,
        math.sqrt(peak_counts),
        roi_counts,
        math.sqrt(roi_counts),
        ratio*1e3,
        ratio_err*1e3,
    )

    hist.Rebin(5)
    hist.SetXTitle('Energy [keV]')
    hist.SetYTitle('Counts / %.1f keV' % hist.GetBinWidth(1))
    hist.GetYaxis().SetTitleOffset(1.2)

    return hist


def main(directories):
  
    hists = []

    for directory in directories:
        
        #basename = os.path.basename(root_file_name)
        #print '--> processing %s' % basename

        hist = get_hist_from_files(directory)
        hists.append(hist)

        # end loop over hists


    canvas = TCanvas('canvas', '')
    canvas.SetLogy(1)
    legend = TLegend(0.1, 0.9, 0.9, 0.99)
    legend.SetNColumns(2)

    hist_zero = hists[0]
    hist_zero.Draw('hist')
    max = hist_zero.GetMaximum()
    for i_hist in range(len(hists)):
        hist = hists[i_hist]
        hist.SetLineColor(i_hist+1)
        hist.Draw('hist same')
        legend.AddEntry(hist, hist.GetName(), 'l')

    legend.Draw()
    hist_zero.SetMinimum(max/1e4)
    canvas.Update()
    canvas.Print('mageSpectra.pdf')
    raw_input('--> enter to continue')

    return
    hist_zero.SetAxisRange(2030, 2040)
    hist_zero.SetMinimum(0)
    canvas.SetLogy(0)
    canvas.Update()
    canvas.Print('mageSpectra_zoom.pdf')
    raw_input('--> enter to continue')


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print 'arguments: [directories of MaGe/GAT ROOT output]'
        sys.exit()

    main(sys.argv[1:])

