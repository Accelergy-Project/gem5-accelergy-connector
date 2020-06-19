#include <stdio.h>

#define SIZE 262144
#define N SIZE / 4
#define M 2
#define C 1.1f

int arr_a[N * M];
int arr_b[N * M];

int main(void) {
	for (int i = 0; i < M; i++) {
		for (int j = 0; j < 2; j++) {
			for (int k = 0; k < N; k++) {
				arr_a[k + i*N] += 1;
			}
		}
	}

	// int mul/div
	for (int i = 0; i < M; i++) {
		for (int j = 0; j < N; j++) {
			arr_b[j + i*N] = i * j / 3;
		}
	}

	// fp mul/div
	float x = 1;
	for (int i = 0; i < N; i++) x *= C;
	for (int i = 0; i < N; i++) x /= C;
}
