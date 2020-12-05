import argparse
import numpy as np
import matplotlib.pyplot as plt
import sigproc
import warnings
from pathlib import Path

filfile = '/home/user/beamformer_test/spliced_beamf.fil';

fnames=['/mnt/data/dsa110/T3/corr01/03dec20/corr01_BF.fil',\
'/mnt/data/dsa110/T3/corr02/03dec20/corr02_BF.fil',\
'/mnt/data/dsa110/T3/corr03/03dec20/corr03_BF.fil',\
'/mnt/data/dsa110/T3/corr21/03dec20/corr21_BF.fil',\
'/mnt/data/dsa110/T3/corr05/03dec20/corr05_BF.fil',\
'/mnt/data/dsa110/T3/corr06/03dec20/corr06_BF.fil',\
'/mnt/data/dsa110/T3/corr07/03dec20/corr07_BF.fil',\
'/mnt/data/dsa110/T3/corr08/03dec20/corr08_BF.fil',\
'/mnt/data/dsa110/T3/corr09/03dec20/corr09_BF.fil',\
'/mnt/data/dsa110/T3/corr10/03dec20/corr10_BF.fil',\
'/mnt/data/dsa110/T3/corr11/03dec20/corr11_BF.fil',\
'/mnt/data/dsa110/T3/corr12/03dec20/corr12_BF.fil',\
'/mnt/data/dsa110/T3/corr13/03dec20/corr13_BF.fil',\
'/mnt/data/dsa110/T3/corr14/03dec20/corr14_BF.fil',\
'/mnt/data/dsa110/T3/corr15/03dec20/corr15_BF.fil',\
'/mnt/data/dsa110/T3/corr16/03dec20/corr16_BF.fil'];

nChans = 384;

fname = fnames[0];
print('processing file '+fname);
header_len = sigproc.len_header(fname);
filsize = int(Path(fname).stat().st_size);
nSam = int((filsize - header_len)/nChans);
data = np.fromfile(fname, dtype=np.uint8, count=-1, offset=header_len);
alldata = np.reshape(data,(nChans,nSam),order='F');

for fname in fnames[1:]:
    print('processing file '+fname);
    header_len = sigproc.len_header(fname);
    filsize = int(Path(fname).stat().st_size);
    nSam = int((filsize - header_len)/nChans);
    data = np.fromfile(fname, dtype=np.uint8, count=-1, offset=header_len);
    data = np.reshape(data,(nChans,nSam),order='F');
    alldata = np.concatenate((alldata,data),axis=0);


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
  b'nchans': str(384*16).encode(), # 2**18 for < 1Hz resolution at 200./1024. MHz sampling
  b'machine_id': b'99', # ??
  b'tsamp': str(4*8.192e-6).encode(),
  b'foff': str(-0.03051757812).encode(),
  b'nbeams': b'1',
  b'fch1': str(1498.75).encode(),
  b'tstart': str(55000.0).encode(),
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

np.reshape(alldata,(alldata.shape[0]*alldata.shape[1]),order='F').astype('uint8').tofile(outfile);

outfile.close();
