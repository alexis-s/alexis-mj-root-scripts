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
from ROOT import TLegend


def get_hist(weight):
    
    # options:
    max_bin = 1500
    bin_width = 20.0

    gROOT.cd() # deal with TH1D/TFile/python scope issues!!
    name = 'hist_weight%.3e' % weight
    n_bins = int(1.0*max_bin/bin_width)
    hist = TH1D(name, '', n_bins, 0, max_bin)
    hist.Sumw2()
    #print '----> making hist: %s' % hist.GetName()
    return hist


def main(root_file_names):

    weight_to_hist_dict = {}
    weight_to_n_events_dict = {}

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
            n_total_events = weight_to_n_events_dict[weight]
            #print '--> found hist: %s' % hist.GetName()

        except KeyError:
            hist = get_hist(weight=weight)
            weight_to_hist_dict[weight] = hist
            hist = weight_to_hist_dict[weight]
            n_total_events = 0


        n_total_events += n_events
        weight_to_n_events_dict[weight] = n_total_events
        #print hist.GetEntries()
        hist.GetDirectory().cd()

        # this draws edep from each step
        #tree.Draw(
        #    'fEdep*1e3 >> +%s' % hist.GetName(),
        #    'fTrackWeight*(fEdep>0)',
        #    'goff'
        #)

        # this draws total edep -- assuming fTrackWeight taken from the last step
        # in the first event applied to all events!
        tree.Draw(
            'fTotalEnergy*1e3 >> +%s' % hist.GetName(),
            #'%s*(fTotalEnergy>0)' % weight,
            'fTrackWeight[1]*(fTotalEnergy>0)',
            'goff'
        )

        #print hist.GetEntries()

        # end loop over input files

    weights = weight_to_hist_dict.keys()
    weights.sort()


    canvas = TCanvas('canvas', '')
    canvas.SetLogy(1)
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(4)

    # find the max
    max_y_value = 0
    hists = weight_to_hist_dict.values()
    for hist in hists:
        n_total_events = weight_to_n_events_dict[weight]
        hist.Scale(1.0/n_total_events)
        hist_max = hist.GetMaximum()
        if hist_max > max_y_value: max_y_value = hist_max
    

    for i_weight in range(len(weights)):
        
        weight = weights[i_weight]
        hist = weight_to_hist_dict[weight]
        hist.SetLineWidth(2)
        color = i_weight+2
        hist.SetFillColor(color)
        hist.SetLineColor(color)
        #hist.SetMarkerColor(color)
        n_entries = hist.GetEntries()
        n_hits_per_decay = hist.Integral(0, hist.GetNbinsX())

        print 'hist %i | weight: %.1e | hits: %i | eff: %.2e +/- %.2e' % (
            i_weight,
            weight, 
            n_entries,
            n_hits_per_decay,
            n_hits_per_decay/math.sqrt(n_entries),

        )

        draw_opt = 'e2'
        if i_weight is 0:
            hist.SetMaximum(max_y_value*2.0)
            hist.SetXTitle('Energy [keV]')
            hist.SetYTitle('Counts / Decay / %.1f keV' % hist.GetBinWidth(1))
            hist.GetYaxis().SetTitleOffset(1.2)
        else:
            draw_opt += ' same'

        hist.Draw(draw_opt)
        entry_label = '%.1e, %.1e entries' % (weight, n_entries)
        legend.AddEntry(hist, entry_label, 'l')


    legend.Draw()        
    canvas.Update()

    prefix = os.path.commonprefix(root_file_names)
    prefix = os.path.basename(prefix)
    #canvas.Print('%s_IS_Spectra.pdf' % prefix)

    raw_input('--> enter to continue')




if __name__ == '__main__':

    if len(sys.argv) < 2:
        print 'arguments: [MaGe ROOT output]'
        sys.exit()

    main(sys.argv[1:])




