/*
https://dzone.com/articles/parallel-tcpip-socket-server-with-multi-threading
*/

#include"stdio.h"
#include"stdlib.h"
#include"sys/types.h"
#include"sys/socket.h"
#include"string.h"
#include <linux/in.h>
//#include"netinet/in.h"
#include<pthread.h>

#define PORT 4444
#define CLADDR_LEN 100

#define NTIMES 4096	// # of time samples (assuming 1ms sampling period)
#define NCHAN 256	// # of channels on BF node side
#define NBEAMSTOSEND 64	// # of beams sent to the search node

#define BUF_SIZE NTIMES*NCHAN*NBEAMSTOSEND // size of TCP packet

typedef struct
{
	int sock;
	struct sockaddr_in address;
	int addr_len;
} connection_t;

void * process(void * ptr)
{
	char clientAddr[CLADDR_LEN];
	char * buffer;
	int len;
	connection_t * conn;
	long addr = 0;

	if (!ptr) pthread_exit(0); 
	conn = (connection_t *)ptr;

	addr = (&conn->address)->sin_addr.s_addr;
	buffer = (char *)malloc((BUF_SIZE+1)*sizeof(char));
//	buffer[BUF_SIZE] = 0;
	
	inet_ntop(AF_INET, &addr, clientAddr, CLADDR_LEN);
/*		if (strcmp(clientAddr,"131.215.193.190")==0) {
		printf("Received data from %s\n", clientAddr);
	}*/
	
	
	/* read message */
	/*CHANGE LENGTH OF MESSAGE TO READ*/
	read(conn->sock, buffer, BUF_SIZE);
	printf("Received data from %s\n", clientAddr);

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

	memset(&address, 0, sizeof(address));
	address.sin_family = AF_INET;
	address.sin_addr.s_addr = INADDR_ANY;
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
	
	while (1)
	{
		connection = (connection_t *)malloc(sizeof(connection_t));
		connection->sock = accept(sock, (struct sockaddr *) &connection->address, &connection->addr_len);
		printf("soch number = %d\n",connection->sock);
		
		if (connection->sock <= 0)
		{
			printf("Error accepting connection!\n");
			free(connection);
		}
		else
		{
			printf("Creating receive thread\n");
			pthread_create(&thread, 0, process, (void *)connection);
			pthread_detach(thread);
		}
	}
	
	return 0;
}
