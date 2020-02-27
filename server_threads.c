/*
https://dzone.com/articles/parallel-tcpip-socket-server-with-multi-threading

gcc -o test_ipcbuf test_ipcbuf.c -I/usr/local/psrdada/src -I/usr/local/include -L/usr/local/lib -lpsrdada -lm -pthread -g -O2 -L/usr/lib/gcc/x86_64-linux-gnu/5 -lgfortran

*/

#include"stdio.h"
#include"stdlib.h"
#include"sys/types.h"
#include"sys/socket.h"
#include"string.h"
#include<pthread.h>
#include <arpa/inet.h>
#include <unistd.h>

#include "sock.h"
#include "tmutil.h"
#include "dada_client.h"
#include "dada_def.h"
#include "dada_hdu.h"
//#include "multilog.h"
#include "ipcio.h"
#include "ipcbuf.h"
#include "dada_affinity.h"
//#include "ascii_header.h"

#define PORT 4444
#define CLADDR_LEN 100
#define HDR_SIZE 4096	// size dada header

#define NTIMES 4096	// # of time samples (assuming 1ms sampling period)
#define NCHAN 256	// # of channels on BF node side
#define NBEAMSTOSEND 64	// # of beams sent to the search node
#define NCHANTOT NCHAN*8	// total number of channels per beam

#define BUF_SIZE NTIMES*NCHAN*NBEAMSTOSEND // size of TCP packet
#define DADA_BUF_SIZE NTIMES*NCHANTOT*NBEAMSTOSEND // size of TCP packet

char buff[DADA_BUF_SIZE];
int cnt_threads = 0;

typedef struct
{
	int sock;
	struct sockaddr_in address;
	socklen_t addr_len;
} connection_t;

void * process(void * ptr)
{
	char clientAddr[CLADDR_LEN];
	char * buffer;
	int len;
	connection_t * conn;
	long addr;

	if (!ptr) pthread_exit(0); 
	conn = (connection_t *)ptr;

	addr = (long)((struct sockaddr_in *)&conn->address)->sin_addr.s_addr;
	inet_ntop(AF_INET, &addr, clientAddr, CLADDR_LEN);
	printf("received data from %s\n",clientAddr);
	
	buffer = (char *)malloc((BUF_SIZE+1)*sizeof(char));
	
	/* read message */
	read(conn->sock, buffer, BUF_SIZE);
	
/* change global array */
	if (strcmp(clientAddr,"192.168.40.11")==0) {		
		int nBandNum = 0;
		for (int i = 0; i < NBEAMSTOSEND; i++) {
			for (int j = 0; j < NCHAN*NTIMES; j++) {
				buff[i*NTIMES*NCHANTOT + nBandNum*NCHAN + j] = buffer[i*NCHAN*NTIMES + j];
			}
		}
		printf("global array modified\n");
	}
	
	cnt_threads++;
	if (cnt_threads == 8){
		printf("\n~~~~~~~~~~~ WRITE TO BUFFER ~~~~~~~~~~~\n");
		cnt_threads = 0;

		// write to dada buffer
/*		FILE *f = fopen("/home/ghellbourg/test_tcp/multi_test/serverdata.bin", "wb");
		fwrite(buff, sizeof(char), DADA_BUF_SIZE, f);
		fclose(f);
*/		
// actually writing to dada buffer

		dada_hdu_t* hdu_out = 0;
		multilog_t* log = 0;
		key_t out_key = 0x0000caca;
		uint64_t blocksize = (uint64_t)DADA_BUF_SIZE;
		log = multilog_open ("server_thread", 0);
		multilog_add (log, stderr);
		multilog (log, LOG_INFO, "server_thread: creating hdu\n");  
		hdu_out  = dada_hdu_create (log);
		dada_hdu_set_key (hdu_out, out_key);
		if (dada_hdu_connect (hdu_out) < 0) {
			printf ("server_thread: could not connect to dada buffer\n");
			return EXIT_FAILURE;
		}
		if (dada_hdu_lock_write (hdu_out) < 0) {
			printf ("server_thread: could not lock to dada buffer\n");
			return EXIT_FAILURE;
		}
		
		/*read fake header for now*/
		char head_dada[4096];
		FILE *f = fopen("/home/vikram/correlator_header_dsaX.txt", "rb");
		fread(head_dada, sizeof(char), 4096, f);
		fclose(f);

		char * header_out = ipcbuf_get_next_write (hdu_out->header_block);
		uint64_t header_size = HDR_SIZE;
		if (!header_out)
		{
			multilog(log, LOG_ERR, "could not get next header block [output]\n");
			return EXIT_FAILURE;
		}
		memcpy (header_out, head_dada, header_size);
		if (ipcbuf_mark_filled (hdu_out->header_block, header_size) < 0)
		{
			multilog (log, LOG_ERR, "could not mark header block filled [output]\n");
			return EXIT_FAILURE;
		}
		uint64_t written=0;
		written = ipcio_write (hdu_out->data_block, buff, DADA_BUF_SIZE);
		if (written < DADA_BUF_SIZE)
		{
			multilog(log, LOG_INFO, "main: failed to write all data to datablock [output]\n");
			return EXIT_FAILURE;
		}
		if (dada_hdu_unlock_write (hdu_out) < 0)
		{
			multilog(log, LOG_ERR, "could not unlock write on hdu_out\n");
		}
		dada_hdu_destroy (hdu_out);
		
		
		
		
		
		
/*		
		dada_hdu_t* hdu_out = 0;
		multilog_t* log = 0;
		key_t out_key = 0x0000caca;
		uint64_t blocksize = DADA_BUF_SIZE;
		log = multilog_open ("dsaX_correlator_copy", 0);
		multilog_add (log, stderr);
		hdu_out  = dada_hdu_create (log);
		dada_hdu_set_key (hdu_out, out_key);
		if (dada_hdu_connect (hdu_out) < 0) {
			printf ("dsaX_correlator_copy: could not connect to output  buffer\n");
			return EXIT_FAILURE;
		}
		if (dada_hdu_lock_write(hdu_out) < 0) {
			fprintf (stderr, "dsaX_correlator_copy: could not lock to output buffer\n");
			return EXIT_FAILURE;
		}
//		if (core >= 0)
//		{
//			printf("binding to core %d\n", core);
//			if (dada_bind_thread_to_core(core) < 0)
//			printf("dsaX_correlator_copy: failed to bind to core %d\n", core);
//		}
		uint64_t written=0;
		char * header_out = ipcbuf_get_next_write (hdu_out->header_block);
		if (!header_out)
		{
			multilog(log, LOG_ERR, "could not get next header block [output]\n");
			return EXIT_FAILURE;
		}
// WRITE CUSTOM HEADER ???		
		memcpy (header_out, header_in, header_size);
		if (ipcbuf_mark_filled (hdu_out->header_block, header_size) < 0)
		{
			multilog (log, LOG_ERR, "could not mark header block filled [output]\n");
			return EXIT_FAILURE;
		}
		multilog(log, LOG_INFO, "main: starting read\n");
		written = ipcio_write (hdu_out->data_block, buff, blocksize);
		if (written < blocksize)
		{
			multilog(log, LOG_INFO, "main: failed to write all data to datablock [output]\n");
			return EXIT_FAILURE;
		}
/*		if (dada_hdu_unlock_write (hdu_out) < 0)
		{
			multilog(log, LOG_ERR, "could not unlock write on hdu_out\n");
		}
		dada_hdu_destroy (hdu_out);
*/

	}


	free(buffer);


	/* close socket and clean up */
	close(conn->sock);
	free(conn);
	pthread_exit(0);
}



int main(int argc, char ** argv)
{
	int sock = -1;
	struct sockaddr_in address;
	char clientAddr[CLADDR_LEN];
	connection_t * connection;
	pthread_t thread;

	/* create socket */
	sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
	if (sock <= 0)
	{
		fprintf(stderr, "error: cannot create socket\n");
		exit(1);
	}
	printf("socket created\n");

	memset(&address, 0, sizeof(struct sockaddr_in));
	address.sin_family = AF_INET;
//	address.sin_addr.s_addr = INADDR_ANY;
//	address.sin_addr.s_addr = inet_addr("131.215.193.190");
//	address.sin_addr.s_addr = inet_addr("127.0.0.1");
	address.sin_addr.s_addr = inet_addr("192.168.40.11");
	address.sin_port = PORT;
	if (bind(sock, (struct sockaddr *)&address, sizeof(struct sockaddr_in)) < 0)
	{
		fprintf(stderr, "error: cannot bind socket to port\n");
		exit(1);
	}
	printf("socket bound to port\n");

	if (listen(sock, 10) < 0)
	{
		fprintf(stderr, "error: cannot listen on port\n");
		exit(1);
	}
	printf("socket ready and listening\n");
	
	socklen_t cli_len=sizeof(struct sockaddr);
	
	while (1)
	{
		connection = (connection_t *)malloc(sizeof(connection_t));
		connection->sock = accept(sock, (struct sockaddr *) &connection->address, &cli_len);
		connection->addr_len = cli_len;
		
		if (connection->sock <= 0)
		{
			printf("Error accepting connection!\n");
			free(connection);
		}
		else
		{
			printf("Creating receive thread\n");
			pthread_create(&thread, 0, process, (void *)connection);
			pthread_join(thread, NULL);
		}
	}
	
	return 0;
}