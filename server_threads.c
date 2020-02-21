/*
https://dzone.com/articles/parallel-tcpip-socket-server-with-multi-threading
*/

#include"stdio.h"
#include"stdlib.h"
#include"sys/types.h"
#include"sys/socket.h"
#include"string.h"
#include<pthread.h>
#include <arpa/inet.h>
#include <unistd.h>

#define PORT 4444
#define CLADDR_LEN 100

#define NTIMES 4096	// # of time samples (assuming 1ms sampling period)
#define NCHAN 256	// # of channels on BF node side
#define NBEAMSTOSEND 64	// # of beams sent to the search node
#define NCHANTOT NCHAN*8

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

//	addr = (&conn->address)->sin_addr.s_addr;
	addr = (long)((struct sockaddr_in *)&conn->address)->sin_addr.s_addr;
	printf("addr = %ld\n",addr);
	inet_ntop(AF_INET, &addr, clientAddr, CLADDR_LEN);
	printf("received data from %s\n",clientAddr);
	
	buffer = (char *)malloc((BUF_SIZE+1)*sizeof(char));
	
	/* read message */
	read(conn->sock, buffer, BUF_SIZE);
//	printf("Received data from %s : %s\n", clientAddr, buffer);
	
/* change global array */
	if (strcmp(clientAddr,"131.215.193.190")==0) {		
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
		// write to dada buffer
		FILE *f = fopen("/home/ghellbourg/test_tcp/multi_test/serverdata.bin", "wb");
		fwrite(buff, sizeof(char), DADA_BUF_SIZE, f);
		fclose(f);
		cnt_threads = 0;
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
		
//		inet_ntop(AF_INET, &(connection->address.sin_addr), clientAddr, CLADDR_LEN);
//		printf("Receiving data from %s\n", clientAddr);
		
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
//			pthread_detach(thread);
		}
	}
	
	return 0;
}