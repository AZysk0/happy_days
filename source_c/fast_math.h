extern "C" {
    __declspec(dllexport) float Q_rsqrt(float number);
    __declspec(dllexport) float map_opengl_to_screen_2d(float x, float y, short int w, short int h, float* result);
    __declspec(dllexport) float map_screen_to_opengl(float x, float y, short int w, short int h, float* result);
}
