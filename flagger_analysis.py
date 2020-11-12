## testing applying flagger on all spectra of a given block
## see if the noise is not too much to detect outliers

import argparse
import numpy as np
import matplotlib.pyplot as plt
import sigproc
import warnings
from pathlib import Path
import scipy.signal
from scipy import stats
import numpy.matlib as npm
import sys

dSNR = 20; # fake signal strength
threshold = 5;
filtsize = 21;  # seems to work, can be increased if needed

nBeam = 0;
nBlock = 0;
#infile = '/home/user/vikram/scratch/bsfil_B0531_1.fil';
infile = '/home/user/vikram/scratch/bsfil_TEST_2.fil';

header = sigproc.read_header(infile);
nBeams = 64; #header['nbeams'];
nChans = 1024; #header['nchans'];
nInts = 4096; #header['nsamples'];

nBlockSize = nBeams * nChans * nInts;
FilSize = Path(infile).stat().st_size;
nTotBlocks = round(FilSize / nBlockSize);

fh  = open(infile, 'rb');
while True:
	keyword, value, idx = sigproc.read_next_header_keyword(fh);
	if keyword == 'HEADER_END':
		break;

nStartDataIdx = fh.tell();

nBeam = 10; #np.random.randint(nBeams);
nBlock = 10; #np.random.randint(nTotBlocks);

fh.seek(0,0);
data = np.fromfile(fh, dtype=np.uint8, count=nBlockSize, offset=nStartDataIdx + nBlock * nBlockSize);
data = np.reshape(data, (nBeams,nInts,nChans), order = 'C');
data = data[nBeam,:,128:895];

## inject fake FRB -- sort of
N = 500;
n = np.linspace(-N/2,N/2,N);
stdev = (N-1)/(6);
y = np.exp(-1/2*np.power(n/stdev,2));
y = npm.repmat(y,N,1);
y = np.multiply(y,y.T);

dataInj = np.copy(data);
dataInj[int(data.shape[0]/2)-int(N/2):int(data.shape[0]/2)+int(N/2),int(data.shape[1]/2)-int(N/2):int(data.shape[1]/2)+int(N/2)] =\
    dataInj[int(data.shape[0]/2)-int(N/2):int(data.shape[0]/2)+int(N/2),int(data.shape[1]/2)-int(N/2):int(data.shape[1]/2)+int(N/2)] +\
        dSNR*y;

## processing

# mask = np.zeros(np.shape(data));
# #spec = np.mean(data,axis=0);
# #specfilt = scipy.signal.medfilt(spec,kernel_size=filtsize);
# for k in range(nInts):
    # spec = data[k,:];
    # specfilt = scipy.signal.medfilt(spec,kernel_size=filtsize);
    # speccorrec = spec - specfilt;
    # sig = stats.median_abs_deviation(speccorrec);
    # for kk in range(data.shape[1]):
        # if speccorrec[kk]>=threshold*sig or speccorrec[kk]<=-threshold*sig:
            # mask[k,kk] = 1;

# plt.figure();
# plt.subplot(2,3,1);
# plt.imshow(data,aspect='auto');
# plt.title('data : beam '+str(nBeam)+' - block '+str(nBlock));
# plt.xlabel('freq channel');
# plt.ylabel('time sample');
# plt.subplot(2,3,4);
# plt.imshow(mask,aspect='auto');
# plt.title('mask');
# plt.xlabel('freq channel');
# plt.ylabel('time sample');


mask = np.zeros(np.shape(dataInj));
data2 = np.copy(dataInj);   # remove impulsive RFI
for k in range(nInts):
    spec = dataInj[k,:];
    specfilt = scipy.signal.medfilt(spec,kernel_size=filtsize);
    speccorrec = spec - specfilt;
    sig = stats.median_abs_deviation(speccorrec);
    for kk in range(dataInj.shape[1]):
        if speccorrec[kk]>=threshold*sig or speccorrec[kk]<=-threshold*sig:
            mask[k,kk] = 1;
            speccorrec[kk] = np.random.normal(0.,1.4826*sig);
    data2[k,:] = speccorrec + specfilt;

## narrowband flagger
data3 = np.copy(data2); # remove narrowband RFI
spec = np.mean(data3,axis=0);
specfilt = scipy.signal.medfilt(spec,kernel_size=filtsize);
speccorrec = spec - specfilt;
sig = stats.median_abs_deviation(speccorrec);
sigTot = stats.median_abs_deviation(np.reshape(data3,-1));
for kk in range(dataInj.shape[1]):
    if speccorrec[kk]>=threshold*sig or speccorrec[kk]<=-threshold*sig:
        data3[:,kk] = np.random.normal(specfilt[kk],1.4826*sigTot,(nInts));

plt.figure();
plt.subplot(2,3,1);
plt.imshow(dataInj,aspect='auto');
plt.title('data : beam '+str(nBeam)+' - block '+str(nBlock)+' + FRB');
plt.xlabel('freq channel');
plt.ylabel('time sample');
plt.subplot(2,3,4);
plt.imshow(mask,aspect='auto');
plt.title('impulsive RFI mask');
plt.xlabel('freq channel');
plt.ylabel('time sample');
plt.subplot(2,3,2);
plt.imshow(data2,aspect='auto');
plt.title('impulsive RFI flagged');
plt.xlabel('freq channel');
plt.ylabel('time sample');
plt.subplot(2,3,5);
plt.imshow(data3,aspect='auto');
plt.title('impulsive + narrowband RFI flagged');
plt.xlabel('freq channel');
plt.ylabel('time sample');
plt.subplot(2,3,3);
plt.plot(np.mean(dataInj,axis=0),label='original');
plt.plot(np.mean(data2,axis=0),label='impulsive flagged');
plt.plot(np.mean(data3,axis=0),label='impulsive+narrow flagged');
plt.legend();
plt.grid();
plt.title('data profile');
plt.xlabel('freq channel');
plt.ylabel('power');
plt.subplot(2,3,6);
plt.plot(np.mean(dataInj,axis=1),label='original');
plt.plot(np.mean(data2,axis=1),label='impulsive flagged');
plt.plot(np.mean(data3,axis=1),label='impulsive+narrow flagged');
plt.legend();
plt.grid();
plt.title('data profile');
plt.xlabel('time sample');
plt.ylabel('power');
plt.show();

