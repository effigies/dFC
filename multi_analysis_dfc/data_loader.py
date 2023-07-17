
"""
Implementation of dFC methods.

Created on Jun 29 2023
@author: Mohammad Torabi
"""

import numpy as np
import hdf5storage
import scipy.io as sio
import os

from .dfc_utils import intersection
from .time_series import TIME_SERIES

################################# DATA_LOADER functions ######################################

def find_subj_list(data_root):
    '''
    find the list of subjects in data_root
    the files must follow the format: subjectID_sessionID
    only these files should be in the data_root
    '''
    ALL_FILES = os.listdir(data_root)
    FOLDERS = [item for item in ALL_FILES if os.path.isdir(data_root+item)]
    
    FOLDERS.sort()
    SUBJECTS = list()
    for s in FOLDERS:
        num = s[:s.find('_')]
        SUBJECTS.append(num)
    # the subjects might be repeated because of different sessions
    SUBJECTS = list(set(SUBJECTS))
    SUBJECTS.sort()

    print( str(len(SUBJECTS)) + ' subjects were found. ')

    return SUBJECTS

def label2network(label):
    '''
    returns the network name of a label
    label format: Hemisphere_Network_ID
    '''
    return label[label.find('_')+1:label.find('_', label.find('_')+1)]

def load_np_array(subj_id2load=None, **params):
    '''
    load fMRI data from numpy files
    returns a dictionary of TIME_SERIES objects
    each corresponding to a session

    - the roi locations should be in the same folder
      with the name: params['roi_locs_file']

    - and the roi labels should be in the same folder
      with the name: params['roi_labels_file']
      
    - labels should be in the format: Hemisphere_Network_ID
    '''

    SESSIONs = params['SESSIONs'] #['Rest1_LR' , 'Rest1_RL', 'Rest2_LR', 'Rest2_RL']
    if subj_id2load is None:
        SUBJECTS = find_subj_list(params['data_root'])
    else:
        SUBJECTS = [subj_id2load]

    # LOAD Region Location DATA
    locs = np.load(params['data_root']+params['roi_locs_file'], allow_pickle='True').item()
    locs = locs['locs']

    # LOAD Region Labels DATA
    labels = np.load(params['data_root']+params['roi_labels_file'], allow_pickle='True').item()
    labels = labels['labels']

    # apply networks2include
    # if params['networks2include'] is None, all the regions will be included
    if not params['networks2include'] is None:
        nodes2include = [i for i, x in enumerate(labels) if label2network(x) in params['networks2include']]
    else:
        nodes2include = [i for i, x in enumerate(labels)]
    locs = locs[nodes2include, :]
    labels = [x for node, x in enumerate(labels) if node in nodes2include]


    BOLD = {}
    for session in SESSIONs:
        BOLD[session] = None
        for subject in SUBJECTS:

            subj_fldr = subject + '_' + session

            # LOAD BOLD Data

            # DATA = hdf5storage.loadmat(params['data_root']+subj_fldr+'/ROI_data_Gordon_333_surf.mat')
            # time_series = DATA['ROI_data']

            DATA = np.load(params['data_root']+subj_fldr+'/bold_data.npy', allow_pickle='True').item()
            time_series = DATA['ROI_data'] # time_series.shape = (time, roi)

            # change time_series.shape to (roi, time)
            time_series = time_series.T

            # apply networks2include
            time_series = time_series[nodes2include, :]

            if BOLD[session] is None:
                BOLD[session] = TIME_SERIES(data=time_series, subj_id=subject,
                                    Fs=params['Fs'],
                                    locs=locs, node_labels=labels,
                                    TS_name='BOLD Real', session_name=session
                                )
            else:
                BOLD[session].append_ts(new_time_series=time_series, subj_id=subject)

        print( '*** Session ' + session + ': ' )
        print( 'number of regions= '+str(BOLD[session].n_regions) + ', number of TRs= ' + str(BOLD[session].n_time) )

    return BOLD

####################################################################################################################################