# 1st argument = siglent file name
# 2nd argument = threshold value (suggested 4)

import numpy as np
import matplotlib.pyplot as plt
import sys
from astropy.stats import median_absolute_deviation
import scipy.signal
import numpy.matlib


fname = sys.argv[1];

f = open(fname, 'r');
d = f.readlines();
f.close();

k = 0;
while len(d[k]) < 100:
    if d[k].find('Start =') != -1:
        startstr = d[k][d[k].find('Start =')+8:-2];
    if d[k].find('Start Frequency = ') != -1:
        fmin = float( d[k][d[k].find('= ')+2 : d[k].find(' MHz')] );
    if d[k].find('Stop Frequency =') != -1:
        fmax = float( d[k][d[k].find('= ')+2 : d[k].find(' MHz')] );
    k += 1;

nPoints = len(np.array((d[k].split(',')[1:-2])).astype(np.float));
nSpec = len(d[k:]);
spec = np.zeros((nSpec,nPoints));

for i in range(k,len(d)):
    spec[i-k,:] = np.array((d[i].split(',')[1:-2])).astype(np.float);


filtsize = 41;
thres = float(sys.argv[2]);

meanspec = np.mean(spec,axis=0);
baseline = scipy.signal.medfilt(meanspec,kernel_size=filtsize);
baseline = np.matlib.repmat(baseline.T, nSpec, 1);
speccorrec = spec - baseline;

flags = np.zeros(spec.shape);
for i in range(spec.shape[0]):
    stdest = median_absolute_deviation(speccorrec[i,:]);
    flags[i,:] = (speccorrec[i,:] > thres*stdest).astype(int);

plt.figure();
plt.subplot(221);
plt.imshow(spec,aspect='auto',extent=[fmin,fmax,0,nSpec]);
plt.xlabel('frequency [MHz]');
plt.ylabel('spectrum number');
plt.title('dynamic spectrum');
plt.subplot(222);
plt.plot(np.linspace(fmin,fmax,nPoints),meanspec, label='mean spectrum');
plt.plot(np.linspace(fmin,fmax,nPoints),baseline[0,:], label='baseline');
plt.legend();
plt.grid();
plt.xlabel('frequency [MHz]');
plt.ylabel('power');
plt.title('avg spectrum');
plt.subplot(223);
plt.imshow(flags,aspect='auto',extent=[fmin,fmax,0,nSpec]);
plt.xlabel('frequency [MHz]');
plt.ylabel('spectrum number');
plt.title('flags');
plt.subplot(224);
plt.plot(np.linspace(fmin,fmax,nPoints),np.mean(flags,axis=0)*100.);
plt.grid();
plt.xlabel('frequency [MHz]');
plt.ylabel('occupancy [%]');
plt.title('spectral occupancy');
plt.suptitle(startstr)
plt.show();
