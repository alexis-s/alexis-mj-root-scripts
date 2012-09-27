#!/usr/bin/env python

"""
Check spectra produced with different importance-sampling settings to be sure
they are similar.

27 Sept 2012 A. Schubert
"""

import os
import sys
import math

from ROOT import gROOT
from ROOT import TCanvas
from ROOT import TFile
from ROOT import TH1D
from ROOT import TH1
from ROOT import TObject

def get_hist(weight):
    
    gROOT.cd() # deal with TH1D/TFile/python scope issues!!
    name = 'hist_weight%.3e' % weight
    hist = TH1D(name, '', 3000, 0, 3000)
    print '----> making hist: %s' % hist.GetName()
    return hist


def main(root_file_names):

    weight_to_hist_dict = {}

    for root_file_name in root_file_names:
        
        basename = os.path.basename(root_file_name)

        print '--> processing %s' % basename

        root_file = TFile(root_file_name)
        tree = root_file.Get('fTree')
        #n_entries = tree.GetEntries()
        n_entries = tree.Draw('fTotalEnergy', 'fTotalEnergy>0', 'goff')

        # get some info from the first tree entry
        tree.GetEntry(0)

        mc_run = tree.fMCRun
        n_events = mc_run.GetNEvents()

        eventSteps = tree.eventSteps
        n_steps = eventSteps.GetNSteps()

        # assume all tracks have the same weight
        weight = eventSteps.GetStep(n_steps-1).GetTrackWeight()

        print '\t %i events | %i entries | weight: %.1e | eff: %.1e +/- %.1e' % (
            n_events,
            n_entries,
            weight,
            weight*n_entries/n_events,
            weight*math.sqrt(n_entries)/n_events,
        )


        try:
            hist = weight_to_hist_dict[weight]
            print '--> found hist: %s' % hist.GetName()

        except KeyError:
            hist = get_hist(weight=weight)
            weight_to_hist_dict[weight] = hist
            hist = weight_to_hist_dict[weight]


        print hist.GetEntries()
        hist.GetDirectory().cd()
        print tree.Draw(
            'fEdep >> +%s' % hist.GetName(),
            'fTrackWeight',
            'goff'
        )
        print hist.GetEntries()

        # end loop over input files

    weights = weight_to_hist_dict.keys()
    weights.sort()


        




if __name__ == '__main__':

    if len(sys.argv) < 2:
        print 'arguments: [MaGe ROOT output]'
        sys.exit()

    main(sys.argv[1:])




