#!/usr/bin/env python

"""
plot energy spectrum due to cosmic ray muons from MaGe/GAT root files
"""

import os
import glob

#from ROOT import gROOT
#gROOT.SetBatch(True)
from ROOT import TFile
from ROOT import TH1D
from ROOT import TCanvas
from ROOT import TColor


def main(file_names):

    max_bin = 3000
    n_bins = 600
    
    hist = TH1D('hist', '', n_bins, 0, max_bin)
    n_total_events = 0

    for file_name in file_names:
        print os.path.basename(file_name)

        root_file = TFile(file_name)
        tree = root_file.Get('fTree')

        tree.GetEntry(0)
        n_events = tree.fMCRun.GetNEvents()


        hist.GetDirectory().cd()
        n_entries = tree.Draw(
            'fEnergy/0.001 + fRand * sqrt( 0.153845^2 + fEnergy/0.001 * 0.00296 * 0.12285 )>>+ %s' % hist.GetName(),
            'fMCEventWeight.fWaveformWeight*(fEnergy>0)',
            'goff'
        )

        print n_events, n_entries
        n_total_events += n_events

    print '%s total events' % n_total_events
    print hist.GetEntries()

    canvas = TCanvas('canvas', '')
    canvas.SetLogy(1)
    hist.SetXTitle('Energy [keV]')
    hist.SetYTitle('Counts / %.1f keV' % hist.GetBinWidth(1) )
    hist.SetLineColor(TColor.kBlue+1)
    hist.SetLineWidth(2)
    hist.Draw()
    canvas.Update()

    #canvas.Print('cosmicRayResponse.pdf')

    test = raw_input('--> any key >> ')


if __name__ == '__main__':

    # default is for MALBEK on cenpa-rocks:
    gat_dir = os.getenv('GATRESULTS')
    file_names = glob.glob('%s/BEGeKURFInShield/cosmicRays/cosmic/A0_Z0/*.root' % gat_dir)

    main(file_names=file_names)


