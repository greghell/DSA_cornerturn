## to plot some basic metrics for Quality Control


import numpy as np
import matplotlib.pyplot as plt
import struct
from pathlib import Path
import sys
import os
from astropy.time import Time
from pathlib import Path
import scipy.stats as stats
from scipy.stats import kurtosis


fname = '/mnt/data/dsa110/T3/corr07/03dec20/fl_0.out';

f = 1428.437500;
df = -0.03051757812;

blksize = int(24*384*2*2); #ant * channels * times * pols
nSam = int(Path(fname).stat().st_size);
nPackets = int(nSam / blksize);

## plot power spectra

data = np.zeros((24,384,2,2),dtype=np.complex64);

dataspec = np.zeros((24,384,2));

for bloc in range(nPackets):

    print('sample '+str(bloc+1)+' / '+str(nPackets));
    sig = np.fromfile(fname,dtype=np.uint8,count=blksize,offset=bloc*blksize);

    d_r = ((sig&15));
    d_i = ((sig&240)>>4);
    d_r = np.where(d_r>7.,d_r-15.,d_r);
    d_i = np.where(d_i>7.,d_i-15.,d_i);
    
    d_r = d_r.astype(np.int8);
    d_i = d_i.astype(np.int8);

    sig = d_r + d_i*1j;
    
    data = np.reshape(sig,(24,384,2,2)); # antenna, freq, time, pol
    dataspec = dataspec + np.sum(np.abs(data)**2,axis=2);
    
dataspec /= (2*nPackets);

plt.figure();
ax1 = plt.subplot(2,1,1);
ax1.plot(np.linspace(1428.4375,1428.4375-0.03051757812*384,384),10.*np.log10(dataspec[:,:,0].T));
plt.grid();
plt.ylabel('power [dB]');
plt.title('pol X');
ax2 = plt.subplot(2,1,2,sharex=ax1,sharey=ax1);
ax2.plot(np.linspace(1428.4375,1428.4375-0.03051757812*384,384),10.*np.log10(dataspec[:,:,1].T));
plt.grid();
plt.xlabel('frequency [MHz]');
plt.ylabel('power [dB]');
plt.title('pol Y');
plt.suptitle(fname);
plt.show();
    
plt.figure();
ax1 = plt.subplot(2,1,1);
ax1.imshow(10.*np.log10(dataspec[:,:,0]),aspect='auto',extent=[1428.4375,1428.4375-0.03051757812*384,0,23]);
plt.ylabel('antenna #');
plt.title('pol X');
clb = plt.colorbar();
clb.ax.set_title('power [dB]');
ax2 = plt.subplot(2,1,2,sharex=ax1,sharey=ax1);
ax2.imshow(10.*np.log10(dataspec[:,:,1]),aspect='auto',extent=[1428.4375,1428.4375-0.03051757812*384,0,23]);
plt.xlabel('frequency [MHz]');
plt.ylabel('antenna #');
plt.title('pol Y');
clb = plt.colorbar();
clb.ax.set_title('power [dB]');
plt.suptitle(fname);
plt.show();
    
    
## plot histograms?

alldatareal = np.zeros((24,384,2*nPackets,2),dtype = np.int8);
alldataimag = np.zeros((24,384,2*nPackets,2),dtype = np.int8);
for bloc in range(nPackets):

    print('sample '+str(bloc+1)+' / '+str(nPackets));
    sig = np.fromfile(fname,dtype=np.uint8,count=blksize,offset=bloc*blksize);

    d_r = ((sig&15));
    d_i = ((sig&240)>>4);
    d_r = np.where(d_r>7.,d_r-15.,d_r);
    d_i = np.where(d_i>7.,d_i-15.,d_i);
    
    d_r = d_r.astype(np.int8);
    d_i = d_i.astype(np.int8);
    
    alldatareal[:,:,bloc*2:(bloc+1)*2,:] = np.reshape(d_r,(24,384,2,2));
    alldataimag[:,:,bloc*2:(bloc+1)*2,:] = np.reshape(d_i,(24,384,2,2));
    
    
nChan = 10;
plt.figure();
for k in range(24):
    plt.subplot(5,5,k+1);
    plt.plot(alldatareal[k,nChan,:,0],alldataimag[k,nChan,:,0],'.');
    plt.grid();
    plt.xlim((-8,7));
    plt.ylim((-8,7));
    plt.title('antenna '+str(k));
    plt.suptitle(fname+' - channel #'+str(nChan));
plt.show();

plt.plot(kurtosis(alldatareal[0,:,:,0], axis=1) + kurtosis(alldataimag[0,:,:,0], axis=1));
plt.show()


plt.figure();
ax1 = plt.subplot(2,1,1);
ax1.plot(np.linspace(1428.4375,1428.4375-0.03051757812*384,384),((kurtosis(alldatareal[:,:,:,0], axis=2) + kurtosis(alldataimag[:,:,:,0], axis=2))/2.).T);
plt.grid();
plt.ylabel('kurtosis');
plt.title('pol X');
ax2 = plt.subplot(2,1,2,sharex=ax1,sharey=ax1);
ax2.plot(np.linspace(1428.4375,1428.4375-0.03051757812*384,384),((kurtosis(alldatareal[:,:,:,1], axis=2) + kurtosis(alldataimag[:,:,:,1], axis=2))/2.).T);
plt.grid();
plt.xlabel('frequency [MHz]');
plt.ylabel('kurtosis');
plt.title('pol Y');
plt.suptitle(fname);
plt.show();

plt.figure();
ax1 = plt.subplot(2,1,1);
plt.imshow(((kurtosis(alldatareal[:,:,:,0], axis=2) + kurtosis(alldataimag[:,:,:,0], axis=2))/2.),aspect='auto',extent=[1428.4375,1428.4375-0.03051757812*384,0,23]);
plt.ylabel('antenna #');
plt.title('pol X');
clb = plt.colorbar();
clb.ax.set_title('kurtosis');
ax2 = plt.subplot(2,1,2,sharex=ax1,sharey=ax1);
plt.imshow(((kurtosis(alldatareal[:,:,:,1], axis=2) + kurtosis(alldataimag[:,:,:,1], axis=2))/2.),aspect='auto',extent=[1428.4375,1428.4375-0.03051757812*384,0,23]);
plt.xlabel('frequency [MHz]');
plt.ylabel('antenna #');
plt.title('pol Y');
clb = plt.colorbar();
clb.ax.set_title('kurtosis');
plt.suptitle(fname);
plt.show();

## cross correlation and SVD

alldata = np.zeros((24,384,2*nPackets,2),dtype=np.complex64);
for bloc in range(nPackets):

    print('sample '+str(bloc+1)+' / '+str(nPackets));
    sig = np.fromfile(fname,dtype=np.uint8,count=blksize,offset=bloc*blksize);

    d_r = ((sig&15));
    d_i = ((sig&240)>>4);
    d_r = np.where(d_r>7.,d_r-15.,d_r);
    d_i = np.where(d_i>7.,d_i-15.,d_i);
    
    d_r = d_r.astype(np.int8);
    d_i = d_i.astype(np.int8);

    sig = d_r + d_i*1j;
    
    alldata[:,:,bloc*2:(bloc+1)*2,:] = np.reshape(sig,(24,384,2,2));
    
SingVals = np.zeros((24,384,2));
for k in range(384):
    print('channel #'+str(k+1));
    R = np.matmul(alldata[:,k,:,0],np.conj(alldata[:,k,:,0]).T);
    R /= (2*nPackets);
    u, s, vh = np.linalg.svd(R);
    SingVals[:,k,0] = s;
    R = np.matmul(alldata[:,k,:,1],np.conj(alldata[:,k,:,1]).T);
    R /= (2*nPackets);
    u, s, vh = np.linalg.svd(R);
    SingVals[:,k,1] = s;

plt.figure();
ax1 = plt.subplot(2,1,1);
ax1.plot(np.linspace(1428.4375,1428.4375-0.03051757812*384,384),SingVals[:,:,0].T);
plt.grid();
plt.ylabel('Singular values');
plt.title('pol X');
ax2 = plt.subplot(2,1,2,sharex=ax1,sharey=ax1);
ax2.plot(np.linspace(1428.4375,1428.4375-0.03051757812*384,384),SingVals[:,:,1].T);
plt.grid();
plt.xlabel('frequency [MHz]');
plt.ylabel('Singular values');
plt.title('pol Y');
plt.suptitle(fname);
plt.show();


# locate RFI
plt.figure();
plt.subplot(211)
plt.plot(np.linspace(1428.4375,1428.4375-0.03051757812*384,384),SingVals[:,:,0].T);
plt.subplot(212)
plt.plot(SingVals[:,:,0].T);
plt.show();

nChan = 358;
R = np.matmul(alldata[:,nChan,:,0],np.conj(alldata[:,nChan,:,0]).T);
R /= (2*nPackets);
u, s, vh = np.linalg.svd(R);

f0 = 1417480000;

calfl = '/home/user/beamformer_weights/beamformer_weights_corr07.dat';

def read_bf(fl):

    f = open(fl,"rb")
    d = f.read()
    data = struct.unpack('12352f',d)
    antpos = np.asarray(data[:64])
    w = np.zeros((64,48,2),dtype=np.complex64)
    ww = np.asarray(data[64:]).reshape((64,48,2,2)) # this is 64 ants, 48 channels, 2 pols, real/imag
    w.real = ww[:,:,:,0]
    w.imag = ww[:,:,:,1]
    return antpos,w

antpos,w = read_bf(calfl)

dAngles = np.linspace(-np.pi,np.pi,1000);
doa = np.zeros((1000),dtype=np.complex64);
tw = np.zeros((64,2),dtype=np.complex64) # final weights array
for k in range(1000):
    theta = dAngles[k];
    afac = -2.*np.pi*f0*theta/2.998e8; # factor for rotate
    for i in np.arange(64):
        tw[i,0] = np.cos(afac*antpos[i]) + 1j*np.sin(afac*antpos[i]);
        tw[i,1] = np.cos(afac*antpos[i]) + 1j*np.sin(afac*antpos[i]);
    tw = tw*w[:,int(np.floor(nChan/8)),:]; # this is the final weights array
    doa[k] = np.matmul(tw[:24,0],np.conj(u[:,0]).T) / np.linalg.norm(tw[:24,0]) / np.linalg.norm(u[:,0]);

plt.figure();
plt.plot(dAngles,np.abs(doa));
plt.show();


## fine channelization
nResol = 1024;
nTimes = int(2*nPackets/nResol);
SuperSpec = np.zeros((nResol*384,2));

for k in range(384):
    print('channel #'+str(k+1));
    for kk in range(24):
        SuperSpec[k*nResol:(k+1)*nResol,0] = SuperSpec[k*nResol:(k+1)*nResol,0] + np.fft.fftshift(np.mean(np.abs(np.fft.fft(np.reshape(alldata[kk,k,:,0]-np.mean(alldata[kk,k,:,0]),(nResol,nTimes),order='F'),axis=0))**2,axis=1))/24.;
        SuperSpec[k*nResol:(k+1)*nResol,1] = SuperSpec[k*nResol:(k+1)*nResol,1] + np.fft.fftshift(np.mean(np.abs(np.fft.fft(np.reshape(alldata[kk,k,:,1]-np.mean(alldata[kk,k,:,1]),(nResol,nTimes),order='F'),axis=0))**2,axis=1))/24.;
    
    
plt.figure()
ax1 = plt.subplot(2,1,1);
ax1.plot(np.linspace(1428.4375,1428.4375-0.03051757812*384,384*nResol),10.*np.log10(SuperSpec[:,0]));
plt.grid();
plt.ylabel('power [dB]');
plt.title('PolX');
ax2 = plt.subplot(2,1,2,sharex=ax1,sharey=ax1);
ax2.plot(np.linspace(1428.4375,1428.4375-0.03051757812*384,384*nResol),10.*np.log10(SuperSpec[:,1]));
plt.grid();
plt.xlabel('frequency [MHz]');
plt.ylabel('power [dB]');
plt.title('PolY');
plt.suptitle(fname);
plt.show();

nChan = 356;
nResol = 64;
nTimes = int(2*nPackets/nResol);
SpecGram = np.zeros((nResol,nTimes,2));
for kk in range(24):
    SpecGram[:,:,0] = SpecGram[:,:,0] + np.fft.fftshift(np.abs(np.fft.fft(np.reshape(alldata[kk,nChan,:,0]-np.mean(alldata[kk,nChan,:,0]),(nResol,nTimes),order='F'),axis=0))**2,axes=0)/24.;
    SpecGram[:,:,1] = SpecGram[:,:,1] + np.fft.fftshift(np.abs(np.fft.fft(np.reshape(alldata[kk,nChan,:,1]-np.mean(alldata[kk,nChan,:,1]),(nResol,nTimes),order='F'),axis=0))**2,axes=0)/24.;

plt.figure()
ax1 = plt.subplot(2,1,1);
plt.imshow(10.*np.log10(SpecGram[:,:,0]),aspect='auto');
plt.ylabel('frequency channel');
plt.title('PolX');
ax2 = plt.subplot(2,1,2,sharex=ax1,sharey=ax1);
plt.imshow(10.*np.log10(SpecGram[:,:,1]),aspect='auto');
plt.xlabel('time sample');
plt.ylabel('frequency channel');
plt.title('PolY');
plt.show();
