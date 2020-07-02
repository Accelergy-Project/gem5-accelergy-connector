#include <stdio.h>

#define SIZE 1048576

int arr[SIZE];

int main(void) {
	for (int i = 0; i < SIZE; i++) {
		arr[i] += 1;
	}
}
