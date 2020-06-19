#define N 16384
#define C 1.1f

int main(void) {
	float x = 1;
	for (int i = 0; i < N; i++) x *= C;
	for (int i = 0; i < N; i++) x /= C;
}
