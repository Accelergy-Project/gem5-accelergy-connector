#include <stdio.h>

#define SIZE 262144
#define N SIZE / 4
#define M 4
#define C 1.1f

int arr[N * M];

int main(void) {
	for (int i = 0; i < M; i++) {
		for (int j = 0; j < 2; j++) {
			for (int k = 0; k < N; k++) {
				arr[k + i*N] += 1;
			}
		}
	}
	float x = 1;
	for (int i = 0; i < N; i++) x *= C;
	for (int i = 0; i < N; i++) x /= C;
}
