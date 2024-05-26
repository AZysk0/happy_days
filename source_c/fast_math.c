#include <stdio.h>
#include <math.h>

float Q_rsqrt(float number)  // understand it later
{
    long i;
    float x2, y;
    const float threehalfs = 1.5F;

    x2 = number * 0.5F;
    y  = number;
    i  = * ( long * ) &y;                       // evil floating point bit level hacking
    i  = 0x5f3759df - ( i >> 1 );               // what the fuck?
    y  = * ( float * ) &i;
    y  = y * ( threehalfs - ( x2 * y * y ) );   // 1st iteration
    // y  = y * ( threehalfs - ( x2 * y * y ) );   // 2nd iteration, this can be removed

    return y;
}

float map_opengl_to_screen_2d(float x, float y, short int w, short int h, float* result) {
    result[0] = (x + 1) * 0.5 * w;
    result[1] = (-y + 1) * 0.5 * h;
}

float map_screen_to_opengl(float x, float y, short int w, short int h, float* result) {
    result[0] = -1 + x * (2.0 / w);
    result[1] = -y * (2.0 / h) + 1;
}


