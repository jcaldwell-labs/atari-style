/*
 * Trigonometric Color Palette Functions (GLSL)
 *
 * Based on Inigo Quilez's cosine palette technique.
 * Include this file in your shaders for smooth, cyclic color gradients.
 *
 * Usage:
 *   vec3 color = trig_palette(t, a, b, c, d);
 *   vec3 color = trig_palette_rainbow(t);
 *
 * Reference: https://iquilezles.org/articles/palettes/
 */

#ifndef TRIG_PALETTE_GLSL
#define TRIG_PALETTE_GLSL

// Core palette function
// t: input value (0.0-1.0 for one cycle, can exceed for repetition)
// a: DC offset (base color)
// b: amplitude (color range)
// c: frequency (cycle speed per unit t)
// d: phase offset (shifts R, G, B independently)
vec3 trig_palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(6.28318 * (c * t + d));
}

// ============================================================================
// Preset Palettes
// ============================================================================

// Rainbow - smooth cycling through all hues
const vec3 RAINBOW_A = vec3(0.500, 0.500, 0.500);
const vec3 RAINBOW_B = vec3(0.500, 0.500, 0.500);
const vec3 RAINBOW_C = vec3(1.000, 1.000, 1.000);
const vec3 RAINBOW_D = vec3(0.000, 0.330, 0.670);

vec3 trig_palette_rainbow(float t) {
    return trig_palette(t, RAINBOW_A, RAINBOW_B, RAINBOW_C, RAINBOW_D);
}

// Sunset - warm oranges to cool purples
const vec3 SUNSET_A = vec3(0.500, 0.500, 0.500);
const vec3 SUNSET_B = vec3(0.500, 0.500, 0.500);
const vec3 SUNSET_C = vec3(1.000, 1.000, 0.500);
const vec3 SUNSET_D = vec3(0.800, 0.900, 0.300);

vec3 trig_palette_sunset(float t) {
    return trig_palette(t, SUNSET_A, SUNSET_B, SUNSET_C, SUNSET_D);
}

// Ocean - deep blues to cyan
const vec3 OCEAN_A = vec3(0.500, 0.500, 0.500);
const vec3 OCEAN_B = vec3(0.500, 0.500, 0.500);
const vec3 OCEAN_C = vec3(1.000, 0.700, 0.400);
const vec3 OCEAN_D = vec3(0.000, 0.150, 0.200);

vec3 trig_palette_ocean(float t) {
    return trig_palette(t, OCEAN_A, OCEAN_B, OCEAN_C, OCEAN_D);
}

// Fire - black to red to orange to yellow
const vec3 FIRE_A = vec3(0.500, 0.500, 0.500);
const vec3 FIRE_B = vec3(0.500, 0.500, 0.500);
const vec3 FIRE_C = vec3(1.000, 1.000, 1.000);
const vec3 FIRE_D = vec3(0.000, 0.100, 0.200);

vec3 trig_palette_fire(float t) {
    return trig_palette(t, FIRE_A, FIRE_B, FIRE_C, FIRE_D);
}

// Neon - vibrant 80s aesthetic
const vec3 NEON_A = vec3(0.500, 0.500, 0.500);
const vec3 NEON_B = vec3(0.500, 0.500, 0.500);
const vec3 NEON_C = vec3(1.000, 1.000, 1.000);
const vec3 NEON_D = vec3(0.300, 0.200, 0.200);

vec3 trig_palette_neon(float t) {
    return trig_palette(t, NEON_A, NEON_B, NEON_C, NEON_D);
}

// Cyberpunk - pink, cyan, purple
const vec3 CYBERPUNK_A = vec3(0.500, 0.500, 0.500);
const vec3 CYBERPUNK_B = vec3(0.500, 0.500, 0.500);
const vec3 CYBERPUNK_C = vec3(1.000, 1.000, 1.000);
const vec3 CYBERPUNK_D = vec3(0.500, 0.800, 0.900);

vec3 trig_palette_cyberpunk(float t) {
    return trig_palette(t, CYBERPUNK_A, CYBERPUNK_B, CYBERPUNK_C, CYBERPUNK_D);
}

// Heat - thermal imaging style
const vec3 HEAT_A = vec3(0.500, 0.500, 0.500);
const vec3 HEAT_B = vec3(0.500, 0.500, 0.500);
const vec3 HEAT_C = vec3(1.000, 1.000, 1.000);
const vec3 HEAT_D = vec3(0.000, 0.050, 0.100);

vec3 trig_palette_heat(float t) {
    return trig_palette(t, HEAT_A, HEAT_B, HEAT_C, HEAT_D);
}

// Ice - cold blues and whites
const vec3 ICE_A = vec3(0.600, 0.700, 0.800);
const vec3 ICE_B = vec3(0.400, 0.300, 0.200);
const vec3 ICE_C = vec3(1.000, 1.000, 1.000);
const vec3 ICE_D = vec3(0.500, 0.600, 0.700);

vec3 trig_palette_ice(float t) {
    return trig_palette(t, ICE_A, ICE_B, ICE_C, ICE_D);
}

// ============================================================================
// Utility Functions
// ============================================================================

// Interpolate between two palettes
vec3 trig_palette_mix(
    float t,
    vec3 a1, vec3 b1, vec3 c1, vec3 d1,
    vec3 a2, vec3 b2, vec3 c2, vec3 d2,
    float mix_amount
) {
    vec3 a = mix(a1, a2, mix_amount);
    vec3 b = mix(b1, b2, mix_amount);
    vec3 c = mix(c1, c2, mix_amount);
    vec3 d = mix(d1, d2, mix_amount);
    return trig_palette(t, a, b, c, d);
}

// Animate palette phase over time (creates moving color effect)
vec3 trig_palette_animated(float t, vec3 a, vec3 b, vec3 c, vec3 d, float time, float speed) {
    return trig_palette(t + time * speed, a, b, c, d);
}

#endif // TRIG_PALETTE_GLSL
