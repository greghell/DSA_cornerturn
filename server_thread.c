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
#define NBEAMS_REC 64
#define NCHANS 256
#define NTOTCHANS NCHANS*8
#define BUF_SIZE NCHANS*NBEAMS_REC
#define DADABUFSIZE NTOTCHANS*NBEAMS_REC

typedef struct
{
	int sock;
	struct sockaddr address;
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

	read(conn->sock, &len, sizeof(int));
	if (len > 0)
	{
		addr = (long)((struct sockaddr_in *)&conn->address)->sin_addr.s_addr;
		buffer = (char *)malloc((len+1)*sizeof(char));
		buffer[len] = 0;
		
		inet_ntop(AF_INET, &addr, clientAddr, CLADDR_LEN);
/*		if (strcmp(clientAddr,"131.215.193.190")==0) {
			printf("Received data from %s\n", clientAddr);
		}*/
		/* read message */
		read(conn->sock, buffer, len);
		printf("Received data from %s : %s\n", clientAddr, buffer);

		/* print message */
/*		printf("%d.%d.%d.%d: %s\n",
			(int)((addr      ) & 0xff),
			(int)((addr >>  8) & 0xff),
			(int)((addr >> 16) & 0xff),
			(int)((addr >> 24) & 0xff),
			buffer);*/
		free(buffer);
	}

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
		connection->sock = accept(sock, &connection->address, &connection->addr_len);
		if (connection->sock <= 0)
		{
			free(connection);
		}
		else
		{
			pthread_create(&thread, 0, process, (void *)connection);
			pthread_detach(thread);
		}
	}
	
	return 0;
}
