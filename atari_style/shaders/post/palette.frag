#version 330 core
/*
 * Palette Reduction Shader
 *
 * Reduces color depth to simulate retro hardware limitations.
 * Supports optional Bayer dithering for smoother gradients.
 *
 * Uniforms:
 *   iChannel0    - Input texture
 *   iResolution  - Output resolution
 *   colorLevels  - Colors per channel (2=8 colors, 4=64, 8=512, 16=4096)
 *   dithering    - Enable Bayer dithering (0 or 1)
 *   ditherScale  - Dither pattern scale (1.0 = pixel-accurate)
 */

uniform sampler2D iChannel0;
uniform vec2 iResolution;
uniform float colorLevels;    // Colors per channel (2, 4, 8, 16, 32)
uniform int dithering;        // 0 = off, 1 = on
uniform float ditherScale;    // Scale of dither pattern

in vec2 fragCoord;
out vec4 fragColor;

// Bayer 8x8 dither matrix (normalized to 0-1)
// Provides 64 threshold levels for smooth dithering
float bayer8x8(ivec2 pos) {
    // 8x8 Bayer matrix values (0-63, normalized)
    const int matrix[64] = int[64](
         0, 32,  8, 40,  2, 34, 10, 42,
        48, 16, 56, 24, 50, 18, 58, 26,
        12, 44,  4, 36, 14, 46,  6, 38,
        60, 28, 52, 20, 62, 30, 54, 22,
         3, 35, 11, 43,  1, 33,  9, 41,
        51, 19, 59, 27, 49, 17, 57, 25,
        15, 47,  7, 39, 13, 45,  5, 37,
        63, 31, 55, 23, 61, 29, 53, 21
    );

    int x = pos.x % 8;
    int y = pos.y % 8;
    return float(matrix[y * 8 + x]) / 64.0;
}

// Quantize a color channel to discrete levels
float quantize(float value, float levels) {
    return floor(value * levels + 0.5) / levels;
}

// Quantize with dithering
float quantizeDithered(float value, float levels, float dither) {
    // Add dither offset before quantization
    float offset = (dither - 0.5) / levels;
    return quantize(value + offset, levels);
}

void main() {
    vec3 col = texture(iChannel0, fragCoord).rgb;

    // Ensure colorLevels is at least 2
    float levels = max(2.0, colorLevels);

    if (dithering == 1) {
        // Calculate dither threshold from Bayer matrix
        ivec2 pos = ivec2(gl_FragCoord.xy / ditherScale);
        float dither = bayer8x8(pos);

        // Apply dithered quantization
        col.r = quantizeDithered(col.r, levels, dither);
        col.g = quantizeDithered(col.g, levels, dither);
        col.b = quantizeDithered(col.b, levels, dither);
    } else {
        // Simple quantization without dithering
        col.r = quantize(col.r, levels);
        col.g = quantize(col.g, levels);
        col.b = quantize(col.b, levels);
    }

    fragColor = vec4(col, 1.0);
}
