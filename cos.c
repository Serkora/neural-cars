#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>

int main(const int argc, const char **argv) {
	int iters = atoi(argv[1]);
	time_t start;
	time_t end;
	time(&start);
	//struct timespec tp;
	//clock_gettime(&tp);
	struct timeval tv;
	struct timezone tz;
	gettimeofday(&tv, &tz);
	printf("sec: %ld, usec: %d\n", tv.tv_sec,tv.tv_usec);
	int start_sec = tv.tv_sec;
	int start_usec = tv.tv_usec;
	int i = 0;
	for (i=0; i < iters; i++) {
		long double x = atan(2.52);
	}
	time(&end);
	time_t diff = end - start;
	gettimeofday(&tv, &tz);
	printf("sec: %ld, usec: %d\n", tv.tv_sec,tv.tv_usec);
	int difft = (tv.tv_sec - start_sec) * 1000000 + (tv.tv_usec - start_usec);
	//printf("iters: %d, spent: %ld seconds, %.2Lfns per iteration", iters, diff, (long double)(diff * 1000000000 / iters));
	printf("iters: %d, spent: %ld usecs, %.2Lfns per iteration", iters, difft, (long double)(difft * 1000 / iters));
	printf("\n");
	return 0;
}
