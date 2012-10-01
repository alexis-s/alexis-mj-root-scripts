#!/usr/bin/env python

"""
Move spectra with old weighting values.

28 Sept 2012 A. Schubert
"""

import os
import sys
import math
import commands

from ROOT import gROOT
from ROOT import TCanvas
from ROOT import TFile


def main(root_file_names):

    #weight_threshold = 1e-1 # for Al stand plate
    #weight_threshold = 1e-2 # for Al stand plate
    #weight_threshold = 1e-3 # for Al stand plate

    #weight_threshold = 1e-6 # for rock
    weight_threshold = 1e-3 # for zeolite

    print '--> weight_threshold:  %.2e' % weight_threshold 

    #use_user_input = raw_input('--> would you like to change the default weight?  (y/n) ')
    use_user_input = 'n'
    if use_user_input != 'n':
        weight_threshold = raw_input('--> please enter weight_threshold: ')
        weight_threshold = float(weight_threshold)
        print '--> weight_threshold:  %.2e' % weight_threshold 

    weight_to_n_events_dict = {}
    files_to_delete = []
    n_counts_to_delete = 0
    n_counts = 0

    for root_file_name in root_file_names:
        
        basename = os.path.basename(root_file_name)

        print '--> processing %s' % basename

        root_file = TFile(root_file_name)
        tree = root_file.Get('fTree')
        #n_entries = tree.GetEntries()
        n_entries = tree.Draw('fTotalEnergy', 'fTotalEnergy>0', 'goff')
        n_counts += n_entries

        # get some info from the first tree entry
        tree.GetEntry(0)

        mc_run = tree.fMCRun
        n_events = mc_run.GetNEvents()

        eventSteps = tree.eventSteps
        n_steps = eventSteps.GetNSteps()

        # assume all tracks have the same weight
        weight = eventSteps.GetStep(n_steps-1).GetTrackWeight()

        if weight > weight_threshold:
            files_to_delete.append(root_file_name)
            n_counts_to_delete += n_entries

        print '\t %i events | %i entries | weight: %.1e | eff: %.1e +/- %.1e' % (
            n_events,
            n_entries,
            weight,
            weight*n_entries/n_events,
            weight*math.sqrt(n_entries)/n_events,
        )

    n_files_to_delete = len(files_to_delete)
    print '--> files to delete:'
    if n_files_to_delete == 0.0:
        return
    print '--> there are %i files to delete' % n_files_to_delete

    for file_name in files_to_delete:
        
        print '\t %s' % os.path.basename(file_name)

    print '--> %.1e of %.1e counts are above threshold' % (
        n_counts_to_delete,
        n_counts, 
    )

    print '--> this is %.2f' % (100.0*n_counts_to_delete/n_counts) + '% of the total'
    response = raw_input('--> move files with weights > %.1e ? (%i counts) (y/n) ' % (
        weight_threshold, 
        n_counts_to_delete,
    ) )

    if response != 'y': 
        print '--> NOT moving files'
        return

    print '--> moving files to $MAGERESULTS/problemFiles/'

    for file_name in files_to_delete:

        cmd = 'mv %s $MAGERESULTS/problemFiles/' % file_name 
        #print cmd
        output = commands.getstatusoutput(cmd)
        #print output




if __name__ == '__main__':

    if len(sys.argv) < 2:
        print 'arguments: [MaGe ROOT output]'
        sys.exit()

    main(sys.argv[1:])




