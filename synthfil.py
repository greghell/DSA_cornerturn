import argparse
import numpy as np
from pathlib import Path
import sys
import os
from astropy.time import Time

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



parser = argparse.ArgumentParser(description="Creates DSA-like multi-beam synthetic data");
parser.add_argument("-o", type=str, dest='outfil', help="output .FIL file");
parser.add_argument("-b", type=int, dest='nBeams', help="number of beams", default=64);
parser.add_argument("-c", type=int, dest='nChan', help="number of frequency channels", default=1024);
parser.add_argument("-i", type=int, dest='nInt', help="number of time integrations", default=4096);
args = parser.parse_args();

if os.path.isfile(args.outfil):
    print("\n" + args.outfil + " already exists -- quitting\n");
    sys.exit();

print("\ngenerating synthetic DSA-like multi-beam FIL file");
print("simulating " + str(int(args.nBeams)) + " beams");
print("injecting " + str(int(args.nChan)) + " channels per spectrum");
print("over " + str(int(args.nInt)) + " time integrations\n");


f = {b'telescope_id': b'80',
  b'az_start': b'0.0',
  b'nbits': str(8).encode(),
  b'source_name': "fake".encode(),
  b'data_type': b'1',
  b'nchans': str(args.nChan).encode(),
  b'nsamples': str(args.nInt).encode(),
  b'machine_id': b'99',
  b'tsamp': str(1./200e6 * 1024. * 8. * 32.).encode(),
  b'foff': str(1280).encode(),
  b'src_raj': b'181335.2',
  b'src_dej': b'-174958.1',
#  b'tstart': str(Time(timestr).mjd).encode(),
  b'nbeams': str(args.nBeams).encode(),
  b'fch1': str(1280).encode(),
  b'za_start': b'0.0',
  b'nifs': b'1'};

header_string = b''
header_string += to_sigproc_keyword(b'HEADER_START')

for keyword in f.keys():
    if keyword not in header_keyword_types.keys():
        pass
    else:
        header_string += to_sigproc_keyword(keyword, f[keyword])
    
header_string += to_sigproc_keyword(b'HEADER_END')

fname = args.outfil;
outfile = open(fname, 'wb');
outfile.write(header_string);

# simulated spectrum
nChans = int(args.nChan);

p1 = round(nChans*0.15);    # transition band
spec = 150.*np.ones(nChans);
for k in range(p1):
    spec[k] = (100./p1)*k + 50.;
    spec[-k] = (100./p1)*k + 50.;

for k in range(int(args.nBeams)):
    offBeam = np.random.normal(0.,5.)*np.ones(nChans);
    print("generating beam #"+str(k+1)+" / "+str(int(args.nBeams)));
    for kk in range(int(args.nInt)):
        (spec+np.random.normal(0.,10.,np.size(spec))+offBeam).astype('uint8').tofile(outfile);
    
outfile.close()
