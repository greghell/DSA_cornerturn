#include"stdio.h"  
#include"stdlib.h"  
#include"sys/types.h"  
#include"sys/socket.h"  
#include"string.h"  
#include"netinet/in.h"  
#include"netdb.h"
#include <unistd.h>
#include <pthread.h>
#include <arpa/inet.h>
  
#define PORT 4444 

#define NTIMES 4096	// # of time samples (assuming 1ms sampling period)
#define NCHAN 256	// # of channels on BF node side
#define NBEAMS 256	// # of beams on BF side
#define NBEAMSTOSEND 64	// # of beams sent to the search node
#define NTHREADS NBEAMS/NBEAMSTOSEND

#define BUF_SIZE NTIMES*NCHAN*NBEAMSTOSEND // size of TCP packet

typedef struct
{
	int idx;
	char* arr;
}conn_thread;

void *myThreadFun(void *vargp) {

	conn_thread * conn = (conn_thread *) vargp;
	printf("value index = %d\n",conn->idx);
	char *string = (char *) vargp;
	struct sockaddr_in addr;  
	int sockfd, ret;  
	struct hostent * server;
	char * serverAddr;

// CREATE SOCKET
	sockfd = socket(AF_INET, SOCK_STREAM, 0);  
	if (sockfd < 0) {  
		printf("Error creating socket!\n");  
		exit(1);  
	}  
	printf("Socket created...\n");   

// LIST OF SERVERS TO SEND DATA TO AND FORMATTING ADDRESSES (DEPENDING ON BEAM NUMBERS)
//	serverAddr = "131.215.193.190";
//	serverAddr = "127.0.0.1";
	serverAddr = "192.168.40.11";
	memset(&addr, 0, sizeof(struct sockaddr_in));  
	addr.sin_family = AF_INET;  
	addr.sin_addr.s_addr = inet_addr(serverAddr);
	addr.sin_port = PORT;     

// CONNECT SOCKET
	ret = connect(sockfd, (struct sockaddr *) &addr, sizeof(struct sockaddr_in));  
	if (ret < 0) {  
		printf("Error connecting to the server!\n");  
		exit(1);  
	}  
	printf("Connected to the server...\n");  
	
// SEND DATA
	ret = sendto(sockfd, string, BUF_SIZE, 0, (struct sockaddr *) &addr, sizeof(struct sockaddr_in));  
	if (ret < 0) {  
		printf("Error sending data!\n\t");  
	}

    return NULL; 
}

  
int main(int argc, char**argv) {  

	int nSearchNode;
	char *string_reordered = malloc(NTIMES*NCHAN*NBEAMS + 1);	// reshuffle data array to conveniently send data
	pthread_t tid;
	conn_thread* co;

// HERE IS A WHILE(1) -> keep reading new buffers as they come
	

// THIS IS THE DATA SUPPOSED TO BE READ FROM THE DADA BUFFER
	FILE *f = fopen("/home/ghellbourg/test_tcp/multi_test/file.dat", "rb");
	fseek(f, 0, SEEK_END);
	long fsize = ftell(f);
	fseek(f, 0, SEEK_SET);  /* same as rewind(f); */
	char *string = malloc(fsize + 1);
	fread(string, 1, fsize, f);
	fclose(f);
	
	for (int i = 0; i < NBEAMS; i++) {
		for (int j = 0; j < NTIMES; j++) {
			for (int k = 0; k < NCHAN; k++) {
				
				string_reordered[i*(NCHAN*NTIMES) + j*NCHAN + k] = string[ j*(NCHAN*NBEAMS) + i*NCHAN + k ];
				
			}
		}
	}
	
	
// HERE PUT SEARCH SERVER TO SEND DATA TO (LIST OF ALL SEARCH SERVERS)
// SEND DATA TO EACH SEARCH SERVER THROUGH MULTIPLE THREADS
	for (int i = 0; i < NTHREADS; i++){
		co->idx = i;
		co->arr = string_reordered + BUF_SIZE*i;
		pthread_create(&tid, NULL, myThreadFun, (void *) co);
		pthread_join(tid, NULL);
	}
	
	return 0;    
}  