#define N 524288
#define PI 3.14159f

int main(void) {
	float x;
	for (int i = 0; i < N; i++) x += i * PI;
	for (int i = 0; i < N; i++) x -= i / PI;
}
