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
from ROOT import TColor
from ROOT import TFile
from ROOT import TH1D
from ROOT import TLegend


def get_hist(
    name,
    bin_width=5.0,
    max_bin=2000,
):

    gROOT.cd() # deal with TH1D/TFile/python scope issues!!
    n_bins = int(1.0*max_bin/bin_width)
    hist = TH1D('%s' % name, '', n_bins, 0, max_bin)
    hist.Sumw2()
    #print '----> making hist: %s' % hist.GetName()
    return hist


def main(root_file_names):

    weight_to_hist_dict = {}
    weight_to_n_events_dict = {}

    total_hist = get_hist('total')
    n_all_events = 0
    total_track_weight_hist = TH1D('track_weight_hist', '', 110, -100, 10)
    total_track_weight_hist.SetLineColor(TColor.kBlue+1)
    total_track_weight_hist.SetFillColor(TColor.kBlue+1)

    n_IS_entries = 0
    n_noIS_entries = 0

    n_files = 0
    for root_file_name in root_file_names:
        
        n_files += 1
        #if n_files > 4: break  # debugging

        basename = os.path.basename(root_file_name)

        print '--> processing %s' % basename

        root_file = TFile(root_file_name)
        tree = root_file.Get('fTree')
        #n_entries = tree.GetEntries()
        n_entries = tree.Draw('fTotalEnergy', 'fTotalEnergy>0', 'goff')

        if n_entries <= 0:  
            continue

        # get some info from the first tree entry
        tree.GetEntry(0)
        mc_run = tree.fMCRun
        n_events = mc_run.GetNEvents()
        is_used = mc_run.GetUseImportanceSampling()

        n_all_events += n_events

        if is_used:

            track_weight_hist = TH1D('track_weight_hist', '', 110, -100, 10)
            tree.Draw(
                'TMath::Log2(fSteps.fTrackWeight) >> track_weight_hist',
                'fEdep>0',
                'goff'
            )
            total_track_weight_hist.Add(track_weight_hist)

            min_weight = 1.0
            max_weight = -400
            for i_bin in range(track_weight_hist.GetNbinsX()):
                
                low_edge = track_weight_hist.GetBinLowEdge(i_bin)
                counts = track_weight_hist.GetBinContent(i_bin)

                if counts > 0:
                    #print i_bin, low_edge, counts

                    if low_edge > max_weight:
                        max_weight = low_edge
                    if low_edge <  min_weight:
                        min_weight = low_edge

            #print min_weight, max_weight

            # these were all log2 values:
            #min_weight = pow(2.0, min_weight)
            #max_weight = pow(2.0, max_weight)



            weight = max_weight # test!

        else:
            weight = 0.0


        print '\t %i events | %i entries | weight: %s | eff: %.1e +/- %.1e' % (
            n_events,
            n_entries,
            weight,
            weight*n_entries/n_events,
            weight*math.sqrt(n_entries)/n_events,
        )

        if is_used:
            print '\t\t weight range: %s, %s' % (min_weight, max_weight)
            n_IS_entries += n_entries
        else:
            n_noIS_entries += n_entries


        try:
            hist = weight_to_hist_dict[weight]
            n_total_events = weight_to_n_events_dict[weight]
            #print '--> found hist: %s' % hist.GetName()

        except KeyError:
            hist = get_hist(name = 'hist_weight%.3e' % weight)
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
        selection = '(fTotalEnergy>0)'
        if is_used:
            selection = 'fTrackWeight[1]*(fTotalEnergy>0)'
        #print selection


        n_drawn = tree.Draw(
            'fTotalEnergy*1e3 >> +%s' % hist.GetName(),
            selection,
            'goff'
        )

        tree.Draw(
            'fTotalEnergy*1e3 >> +%s' % total_hist.GetName(),
            selection,
            'goff'
        )

        #print hist.GetEntries(), n_drawn, total_hist.GetEntries()
        print '\t IS used:', is_used, mc_run.GetBiasedParticleID(), mc_run.GetUseTimeWindow(), mc_run.GetUseImportanceProcessWindow()

        #print hist.GetEntries()

        # end loop over input files


    weight_to_n_events_dict[4.0] = n_all_events
    weight_to_hist_dict[4.0] = total_hist

    weights = weight_to_hist_dict.keys()
    weights.sort()


    canvas = TCanvas('canvas', '')
    canvas.SetLogy(1)
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(4)

    # find the max
    max_y_value = 0
    min_max_y_value = weight_to_hist_dict.values()[0].GetMaximum()
    min_y_value = weight_to_hist_dict.values()[0].GetMinimum()
    hists = weight_to_hist_dict.values()
    for hist in hists:
        n_total_events = weight_to_n_events_dict[weight]
        hist.Scale(1.0/n_total_events)
        hist_max = hist.GetMaximum()
        hist_min = hist.GetMinimum()
        if hist_max > max_y_value: max_y_value = hist_max
        if hist_min < min_y_value: min_y_value = hist_min
        if hist_max < min_max_y_value: min_max_y_value = hist_max
        
    

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
        try:
            n_hits_err = n_hits_per_decay/math.sqrt(n_entries)
        except:
            n_hits_err = 0.0

        print 'hist %i | weight: 2^(%i) = %.2e | hits: %i | eff: %.2e +/- %.2e' % (
            i_weight,
            weight, 
            pow(2.0, weight),
            n_entries,
            n_hits_per_decay,
            n_hits_err,

        )

        draw_opt = 'e2'
        if i_weight is 0:
            hist.SetMaximum(max_y_value*2.0)
            #hist.SetMinimum(min_y_value/2.0)
            hist.SetMinimum(min_max_y_value/10.0)
            hist.SetXTitle('Energy [keV]')
            hist.SetYTitle('Counts / Decay / %.1f keV' % hist.GetBinWidth(1))
            hist.GetYaxis().SetTitleOffset(1.2)
        else:
            draw_opt += ' same'

        hist.Draw(draw_opt)
        entry_label = '%s, %.1e entries' % (weight, n_entries)
        legend.AddEntry(hist, entry_label, 'lf')


    legend.Draw()        
    canvas.Update()

    prefix = os.path.commonprefix(root_file_names)
    prefix = os.path.basename(prefix)
    #canvas.Print('%s_IS_Spectra.pdf' % prefix)

    print '---  %i entries with IS, %i entries w/o IS' % (
        n_IS_entries,
        n_noIS_entries,
    )

    response = raw_input('--> enter to continue, i to see indiv hists, q to quit: ')
    if response == 'q':
        return

    if response == 'i':

        for i_weight in range(len(weights)):
            
            weight = weights[i_weight]
            hist = weight_to_hist_dict[weight]

            print weight
            hist.Draw('e2')

            canvas.Update()
            raw_input('--> return to continue ')


    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(4)


    print '--> drawing track weight distribution:'
    total_track_weight_hist.Draw()
    canvas.Update()
    raw_input('--> return to continue ')

    # now look at the output of each run:
    hists = []
    hist_min = 1e5
    hist_max = 0.0
    for i_file in range(len(root_file_names)):

        root_file_name = root_file_names[i_file]
        root_file = TFile(root_file_name)
        tree = root_file.Get('fTree')

        # get some info from the first tree entry
        tree.GetEntry(0)
        mc_run = tree.fMCRun
        n_events = mc_run.GetNEvents()
        is_used = mc_run.GetUseImportanceSampling()
        run_id = mc_run.GetRunID()


        i_color = i_file +2
        hist = get_hist(name=run_id, bin_width=75.0)
        hist.SetLineColor(i_color)
        hist.SetFillColor(i_color)
        hist.SetLineWidth(3)

        entry_label = '%s' % run_id
        legend.AddEntry(hist, entry_label, 'lf')

        selection = '(fTotalEnergy>0)'
        if is_used:
            selection = 'fTrackWeight[1]*(fTotalEnergy>0)'
        #print selection

        n_drawn = tree.Draw(
            'fTotalEnergy*1e3 >> +%s' % hist.GetName(),
            selection,
            'goff'
        )
 
        hist.Scale(1.0/n_events)
        hists.append(hist)

        print run_id, i_color

        max = hist.GetMaximum()
        min = hist.GetMinimum()
        if min < hist_min: hist_min = min
        if max > hist_max: hist_max = max

        #if i_file > 5: break # debugging

        # end loop over files


    hists[0].SetMaximum(hist_max*2.0)
    hists[0].SetMinimum(hist_max/1e7)
    hists[0].Draw('e2')
    for hist in hists:
        hist.Draw('e2 same')

    legend.Draw()
    canvas.Update()
    x = raw_input('--> enter to continue')



if __name__ == '__main__':

    if len(sys.argv) < 2:
        print 'arguments: [MaGe ROOT output]'
        sys.exit()

    main(sys.argv[1:])




