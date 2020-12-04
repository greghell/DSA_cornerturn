import numpy as np
import matplotlib.pyplot as plt
import struct
from pathlib import Path
import sys
import os
from astropy.time import Time
from pathlib import Path

# arguments:
# 1 : data file
# 2 : calibration file
# 3 : start frequency
# 4 : filterbank file

#fname = 'fl_0.out';
#fname = sys.argv[1];
fname = '/mnt/data/dsa110/T3/corr07/03dec20/fl_0.out';

# first argument is calibration file
#calfl = sys.argv[2]
calfl = '/home/user/beamformer_weights/beamformer_weights_corr01.dat';

# second argument is frequency of native resolution channel 1
#f = float(sys.argv[3]) # in Hz
f = 1498.75;

#filfile = sys.argv[4]; # filterbank file
filfile = '/home/user/beamformer_test/test.fil';




blksize = int(24*384*2*2); #ant * channels * times * pols
nSam = int(Path(fname).stat().st_size);
nPackets = int(nSam / blksize);
data = np.zeros((24,384,2,2),dtype=np.complex64);

################ compute beamformer weights ########################

# some definitions
beampos = 1.0 # degrees east

# read in calibration file
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

# calculate actual weights
theta = beampos*np.pi/180. # angle of beam east in radians
freqs = np.reshape(f - np.arange(384)*(2.5e8/8192.),(48,8)).mean(axis=1) # frequencies of summed channels
afac = -2.*np.pi*freqs*theta/2.998e8; # factor for rotate

tw = np.zeros((64,48,2),dtype=np.complex64) # final weights array
for i in np.arange(64):
    tw[i,:,0].real = np.cos(afac*antpos[i])
    tw[i,:,0].imag = np.sin(afac*antpos[i])
    tw[i,:,1].real = np.cos(afac*antpos[i])
    tw[i,:,1].imag = np.sin(afac*antpos[i])

tw = tw*w # this is the final weights array


####################### set up fil file #########################

header_keyword_types = {
    b'telescope_id' : b'<l',
    b'machine_id'   : b'<l',
    b'data_type'    : b'<l',
    b'barycentric'  : b'<l',
    b'pulsarcentric': b'<l',
    b'nbits'        : b'<l',
    b'nsamples'     : b'<l',
    b'nchans'       : b'<l',
    b'nifs'         : b'<l',
    b'nbeams'       : b'<l',
    b'ibeam'        : b'<l',
    b'rawdatafile'  : b'str',
    b'source_name'  : b'str',
    b'az_start'     : b'<d',
    b'za_start'     : b'<d',
    b'tstart'       : b'<d',
    b'tsamp'        : b'<d',
    b'fch1'         : b'<d',
    b'foff'         : b'<d',
    b'refdm'        : b'<d',
    b'period'       : b'<d',
    b'src_raj'      : b'<d',
    b'src_dej'      : b'<d',
#    b'src_raj'      : b'angle',
#    b'src_dej'      : b'angle',
    }

def to_sigproc_keyword(keyword, value=None):
    """ Generate a serialized string for a sigproc keyword:value pair
    If value=None, just the keyword will be written with no payload.
    Data type is inferred by keyword name (via a lookup table)
    Args:
        keyword (str): Keyword to write
        value (None, float, str, double or angle): value to write to file
    Returns:
        value_str (str): serialized string to write to file.
    """

    keyword = bytes(keyword)

    if value is None:
        return np.int32(len(keyword)).tostring() + keyword
    else:
        dtype = header_keyword_types[keyword]

        dtype_to_type = {b'<l'  : np.int32,
                         b'str' : str,
                         b'<d'  : np.float64}#,
#                         b'angle' : to_sigproc_angle}

        value_dtype = dtype_to_type[dtype]

        if value_dtype is str:
            return np.int32(len(keyword)).tostring() + keyword + np.int32(len(value)).tostring() + value
        else:
            return np.int32(len(keyword)).tostring() + keyword + value_dtype(value).tostring()


    
fhead = {b'telescope_id': b'66',    # DSA
  b'az_start': b'0.0',  # not sure where to find
  b'nbits': str(8).encode(),
  b'source_name': 'source'.encode(),
  b'data_type': b'1',       # look into that
  b'nchans': str(384).encode(), # 2**18 for < 1Hz resolution at 200./1024. MHz sampling
  b'machine_id': b'99', # ??
  b'tsamp': str(16*8*8.196e-6).encode(),
  b'foff': str(30.5e3).encode(),
  b'nbeams': b'1',
  b'fch1': str(f).encode(),
  b'nifs': b'1'}

header_string = b''
header_string += to_sigproc_keyword(b'HEADER_START')
    
for keyword in fhead.keys():
    if keyword not in header_keyword_types.keys():
        pass
    else:
        header_string += to_sigproc_keyword(keyword, fhead[keyword])
    
header_string += to_sigproc_keyword(b'HEADER_END')

outfile = open(filfile, 'wb');
outfile.write(header_string);


for bloc in range(nPackets):

    print('sample '+str(bloc)+' / '+str(nPackets));
    sig = np.fromfile(fname,dtype=np.uint8,count=blksize);

    d_r = ((sig&15)<<4);
    d_i = sig&240;
    d_r = np.where(d_r>128.,d_r-255.,d_r);
    d_i = np.where(d_i>128.,d_i-255.,d_i);
    d_r = d_r.astype(np.int8);
    d_i = d_i.astype(np.int8);

    sig = d_r + d_i*1j;
    
    data = np.reshape(sig,(24,384,2,2));
    
    bfdata = np.zeros((384,2),dtype=np.uint8);
    nIdx = 0;
    for k in range(48):
        for kk in range(8):
            #print('beamforming channel #'+str(nIdx));
            bfdata[nIdx,:] = (np.abs(np.dot(tw[:24,k,0],data[:,nIdx,:,0]))**2 + np.abs(np.dot(tw[:24,k,1],data[:,nIdx,:,1]))**2).astype(np.uint8);
            nIdx+=1;
    
    for k in range(2):
        bfdata[:,k].astype('uint8').tofile(outfile);

outfile.close();
    
    
    
    
    
    
    
    
    
    
