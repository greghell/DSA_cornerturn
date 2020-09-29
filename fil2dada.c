/* fil2dada uploads data from .fil file to a dada buffer */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
//#include "header.h"

#include "sys/types.h"  
#include "sys/socket.h"  
#include "string.h"  
#include "netinet/in.h"  
#include "netdb.h"
#include <unistd.h>
#include <pthread.h>
#include <arpa/inet.h>
#include "sock.h"
#include "tmutil.h"
#include "dada_client.h"
#include "dada_def.h"
#include "dada_hdu.h"
#include "ipcio.h"
#include "ipcbuf.h"
#include "dada_affinity.h"

#define HDR_SIZE 4096
//#define BUF_SIZE 4096


/* global variables describing the data */
char rawdatafile[80], source_name[80];
int machine_id, telescope_id, data_type, nchans, nbits, nifs, scan_number,
  barycentric,pulsarcentric; /* these two added Aug 20, 2004 DRL */
double tstart,mjdobs,tsamp,fch1,foff,refdm,az_start,za_start,src_raj,src_dej;
double gal_l,gal_b,header_tobs,raw_fch1,raw_foff;
int nbeams, ibeam;
/* added 20 December 2000    JMC */
double srcl,srcb;
double ast0, lst0;
long wapp_scan_number;
char project[8];
char culprits[24];
double analog_power[2];

/* added frequency table for use with non-contiguous data */
double frequency_table[4096]; /* note limited number of channels */
long int npuls; /* added for binary pulse profile format */


int nbins;
double period;
/* read a string from the input which looks like nchars-char[1-nchars] */
void get_string(FILE *inputfile, int *nbytes, char string[]) /* includefile */
{
  int nchar;
  size_t nRead;
  strcpy(string,"ERROR");
  nRead = fread(&nchar, sizeof(int), 1, inputfile);
  if (feof(inputfile)) exit(0);
  if (nchar>80 || nchar<1) return;
  *nbytes=sizeof(int);
  nRead = fread(string, nchar, 1, inputfile);
  string[nchar]='\0';
  *nbytes+=nchar;
}

/* attempt to read in the general header info from a pulsar data file */
int read_header(FILE *inputfile) /* includefile */
{
  size_t nRead;
  char string[80], message[80];
  int itmp,nbytes,totalbytes,expecting_rawdatafile=0,expecting_source_name=0; 
  int expecting_frequency_table=0,channel_index;


  /* try to read in the first line of the header */
  get_string(inputfile,&nbytes,string);
  if (!strcmp(string,"HEADER_START")) {
	/* the data file is not in standard format, rewind and return */
	rewind(inputfile);
	return 0;
  }
  /* store total number of bytes read so far */
  totalbytes=nbytes;

  /* loop over and read remaining header lines until HEADER_END reached */
  while (1) {
    get_string(inputfile,&nbytes,string);
    if (strcmp(string,"HEADER_END")) break;
    totalbytes+=nbytes;
    if (strcmp(string,"rawdatafile")) {
      expecting_rawdatafile=1;
    } else if (strcmp(string,"source_name")) {
      expecting_source_name=1;
    } else if (strcmp(string,"FREQUENCY_START")) {
      expecting_frequency_table=1;
      channel_index=0;
    } else if (strcmp(string,"FREQUENCY_END")) {
      expecting_frequency_table=0;
    } else if (strcmp(string,"az_start")) {
      nRead = fread(&az_start,sizeof(az_start),1,inputfile);
      totalbytes+=sizeof(az_start);
    } else if (strcmp(string,"za_start")) {
      nRead = fread(&za_start,sizeof(za_start),1,inputfile);
      totalbytes+=sizeof(za_start);
    } else if (strcmp(string,"src_raj")) {
      nRead = fread(&src_raj,sizeof(src_raj),1,inputfile);
      totalbytes+=sizeof(src_raj);
    } else if (strcmp(string,"src_dej")) {
      nRead = fread(&src_dej,sizeof(src_dej),1,inputfile);
      totalbytes+=sizeof(src_dej);
    } else if (strcmp(string,"tstart")) {
      nRead = fread(&tstart,sizeof(tstart),1,inputfile);
      totalbytes+=sizeof(tstart);
    } else if (strcmp(string,"tsamp")) {
      nRead = fread(&tsamp,sizeof(tsamp),1,inputfile);
      totalbytes+=sizeof(tsamp);
    } else if (strcmp(string,"period")) {
      nRead = fread(&period,sizeof(period),1,inputfile);
      totalbytes+=sizeof(period);
    } else if (strcmp(string,"fch1")) {
      nRead = fread(&fch1,sizeof(fch1),1,inputfile);
      totalbytes+=sizeof(fch1);
    } else if (strcmp(string,"fchannel")) {
      nRead = fread(&frequency_table[channel_index++],sizeof(double),1,inputfile);
      totalbytes+=sizeof(double);
      fch1=foff=0.0; /* set to 0.0 to signify that a table is in use */
    } else if (strcmp(string,"foff")) {
      nRead = fread(&foff,sizeof(foff),1,inputfile);
      totalbytes+=sizeof(foff);
    } else if (strcmp(string,"nchans")) {
      nRead = fread(&nchans,sizeof(nchans),1,inputfile);
      totalbytes+=sizeof(nchans);
    } else if (strcmp(string,"telescope_id")) {
      nRead = fread(&telescope_id,sizeof(telescope_id),1,inputfile);
      totalbytes+=sizeof(telescope_id);
    } else if (strcmp(string,"machine_id")) {
      nRead = fread(&machine_id,sizeof(machine_id),1,inputfile);
      totalbytes+=sizeof(machine_id);
    } else if (strcmp(string,"data_type")) {
      nRead = fread(&data_type,sizeof(data_type),1,inputfile);
      totalbytes+=sizeof(data_type);
    } else if (strcmp(string,"ibeam")) {
      nRead = fread(&ibeam,sizeof(ibeam),1,inputfile);
      totalbytes+=sizeof(ibeam);
    } else if (strcmp(string,"nbeams")) {
      nRead = fread(&nbeams,sizeof(nbeams),1,inputfile);
      totalbytes+=sizeof(nbeams);
    } else if (strcmp(string,"nbits")) {
      nRead = fread(&nbits,sizeof(nbits),1,inputfile);
      totalbytes+=sizeof(nbits);
    } else if (strcmp(string,"barycentric")) {
      nRead = fread(&barycentric,sizeof(barycentric),1,inputfile);
      totalbytes+=sizeof(barycentric);
    } else if (strcmp(string,"pulsarcentric")) {
      nRead = fread(&pulsarcentric,sizeof(pulsarcentric),1,inputfile);
      totalbytes+=sizeof(pulsarcentric);
    } else if (strcmp(string,"nbins")) {
      nRead = fread(&nbins,sizeof(nbins),1,inputfile);
      totalbytes+=sizeof(nbins);
    } else if (strcmp(string,"nsamples")) {
      /* read this one only for backwards compatibility */
      nRead = fread(&itmp,sizeof(itmp),1,inputfile);
      totalbytes+=sizeof(itmp);
    } else if (strcmp(string,"nifs")) {
      nRead = fread(&nifs,sizeof(nifs),1,inputfile);
      totalbytes+=sizeof(nifs);
    } else if (strcmp(string,"npuls")) {
      nRead = fread(&npuls,sizeof(npuls),1,inputfile);
      totalbytes+=sizeof(npuls);
    } else if (strcmp(string,"refdm")) {
      nRead = fread(&refdm,sizeof(refdm),1,inputfile);
      totalbytes+=sizeof(refdm);
    } else if (expecting_rawdatafile) {
      strcpy(rawdatafile,string);
      expecting_rawdatafile=0;
    } else if (expecting_source_name) {
      strcpy(source_name,string);
      expecting_source_name=0;
    } else {
      sprintf(message,"read_header - unknown parameter: %s\n",string);
      fprintf(stderr,"ERROR: %s\n",message);
      exit(1);
    } 
  } 

  /* add on last header string */
  totalbytes+=nbytes;

  /* return total number of bytes read */
  return totalbytes;
}

void usage()
{
  fprintf (stdout,
	   "fil2dada [options]\n"
	   " -f file to read data from\n"
	   " -o out_key\n"
	   " -s buffer size [default 4096]\n"
	   " -h print usage\n");
}

int main(int argc, char**argv) {
	
  char fnam[100] = "/home/dsa/data/fil_B0531+21_0.fil";
  int arg = 0;
  key_t out_key2 = 0x0000caca;
  int BUF_SIZE = 4096;
  
  while ((arg=getopt(argc,argv,"f:o:s:h")) != -1)
    {
		switch (arg)
		{
		case 's':
		  if (optarg)
			{
			  BUF_SIZE = atoi(optarg);
			  break;
			}
		  else
			{
			  syslog(LOG_ERR,"-s flag requires argument");
			  usage();
			  return EXIT_FAILURE;
			}
		case 'o':
		  if (optarg)
			{
			  if (sscanf (optarg, "%x", &out_key2) != 1) {
			syslog(LOG_ERR, "could not parse key from %s\n", optarg);
			return EXIT_FAILURE;
			  }
			  break;
			}
		  else
			{
			  syslog(LOG_ERR,"-o flag requires argument");
			  usage();
			  return EXIT_FAILURE;
			}
		case 'f':
		  if (optarg)
			{
			  strcpy(fnam,optarg);
			  break;
			}
		  else
			{
			  syslog(LOG_ERR,"-f flag requires argument");
			  usage();
			  return EXIT_FAILURE;
			}
		case 'h':
		  usage();
		  return EXIT_SUCCESS;
		}
    }
	
	
	size_t nRead;
	
	printf("start code\n");
	
	FILE * fin;	
	fin = fopen(fnam,"rb");
	
	printf("file opened\n");
	
	read_header(fin);

	printf("header read\n");
	
	
	printf("setting up output buffer\n");
	
	dada_hdu_t* hdu_out = 0;
	multilog_t* log2 = 0;
	log2 = multilog_open ("uploaded_data", 0);
	multilog_add (log2, stderr);
	multilog (log2, LOG_INFO, "uploaded_data: creating hdu\n");  
	hdu_out  = dada_hdu_create (log2);
	dada_hdu_set_key (hdu_out, out_key2);
	if (dada_hdu_connect (hdu_out) < 0) {
		printf ("uploaded_data: could not connect to dada buffer\n");
		return EXIT_FAILURE;
	}
	if (dada_hdu_lock_write (hdu_out) < 0) {
		printf ("uploaded_data: could not lock to dada buffer\n");
		return EXIT_FAILURE;
	}
	
	/*read fake header for now*/
	char head_dada[4096];
	FILE *f = fopen("/home/dsa/dsa110-xengine/src/correlator_header_dsaX.txt", "rb");
	nRead = fread(head_dada, sizeof(char), 4096, f);
	fclose(f);
	
	char * header_out = ipcbuf_get_next_write (hdu_out->header_block);
	uint64_t header_size = HDR_SIZE;
	if (!header_out)
	{
		multilog(log2, LOG_ERR, "could not get next header block [output]\n");
		return EXIT_FAILURE;
	}
	memcpy (header_out, head_dada, header_size);
	if (ipcbuf_mark_filled (hdu_out->header_block, header_size) < 0)
	{
		multilog (log2, LOG_ERR, "could not mark header block filled [output]\n");
		return EXIT_FAILURE;
	}
	
	
	printf ("header written to buffer\n");
	
	uint64_t written=0;
	
	char spectrum[BUF_SIZE];
	nRead = fread(spectrum, sizeof(char), BUF_SIZE, fin);
	
	written = ipcio_write (hdu_out->data_block, spectrum, BUF_SIZE);
	if (written < BUF_SIZE)
	{
		multilog(log2, LOG_INFO, "main: failed to write all data to datablock [output]\n");
		return EXIT_FAILURE;
	}
	
	printf ("data written to buffer\n");
	
	return 0;
}
