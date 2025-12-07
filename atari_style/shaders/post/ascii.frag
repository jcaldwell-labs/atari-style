#version 330 core
/*
 * ASCII Art Post-Processing Shader
 *
 * Converts any input image to ASCII art aesthetic using GLSL.
 * This bridges GL visual quality with terminal aesthetic.
 *
 * Technique:
 *   1. Divide screen into character-sized cells
 *   2. Sample average brightness of each cell
 *   3. Map brightness to ASCII character from gradient
 *   4. Render character from glyph texture (or approximate with patterns)
 *
 * Uniforms:
 *   iChannel0       - Input texture from previous pass
 *   iResolution     - Output resolution
 *   iTime           - Animation time
 *   charWidth       - Character cell width in pixels (default 8)
 *   charHeight      - Character cell height in pixels (default 16)
 *   colorMode       - 0=monochrome, 1=colored, 2=neon
 *   bgBrightness    - Background darkness (0.0=black, 0.1=subtle)
 */

uniform sampler2D iChannel0;
uniform vec2 iResolution;
uniform float iTime;

// ASCII effect parameters
uniform float charWidth;      // 8.0 typical
uniform float charHeight;     // 16.0 typical
uniform int colorMode;        // 0=mono, 1=color, 2=neon
uniform float bgBrightness;   // 0.0 - 0.2

in vec2 fragCoord;
out vec4 fragColor;

// ASCII character brightness gradient (10 levels)
// From darkest to brightest: " .:-=+*#%@"
// We simulate this with pattern density

// Pattern functions that approximate ASCII characters
float getCharPattern(float brightness, vec2 cellUV) {
    // cellUV is 0-1 within the character cell

    // Quantize brightness to 10 levels
    int level = int(brightness * 9.99);

    // Simple patterns approximating ASCII density
    if (level == 0) {
        // ' ' - empty
        return 0.0;
    } else if (level == 1) {
        // '.' - single dot in center
        vec2 center = cellUV - 0.5;
        return step(length(center), 0.1) * 0.3;
    } else if (level == 2) {
        // ':' - two dots
        float d1 = length(cellUV - vec2(0.5, 0.3));
        float d2 = length(cellUV - vec2(0.5, 0.7));
        return (step(d1, 0.08) + step(d2, 0.08)) * 0.4;
    } else if (level == 3) {
        // '-' - horizontal line
        float inLine = step(abs(cellUV.y - 0.5), 0.08) * step(abs(cellUV.x - 0.5), 0.3);
        return inLine * 0.5;
    } else if (level == 4) {
        // '=' - double horizontal
        float line1 = step(abs(cellUV.y - 0.35), 0.06) * step(abs(cellUV.x - 0.5), 0.3);
        float line2 = step(abs(cellUV.y - 0.65), 0.06) * step(abs(cellUV.x - 0.5), 0.3);
        return (line1 + line2) * 0.55;
    } else if (level == 5) {
        // '+' - cross
        float h = step(abs(cellUV.y - 0.5), 0.08) * step(abs(cellUV.x - 0.5), 0.3);
        float v = step(abs(cellUV.x - 0.5), 0.08) * step(abs(cellUV.y - 0.5), 0.3);
        return max(h, v) * 0.6;
    } else if (level == 6) {
        // '*' - asterisk-like
        vec2 c = cellUV - 0.5;
        float d = length(c);
        float angle = atan(c.y, c.x);
        float star = step(d, 0.25) * (0.5 + 0.5 * sin(angle * 6.0 + 1.57));
        return star * 0.7;
    } else if (level == 7) {
        // '#' - grid pattern
        float h1 = step(abs(cellUV.y - 0.35), 0.05);
        float h2 = step(abs(cellUV.y - 0.65), 0.05);
        float v1 = step(abs(cellUV.x - 0.35), 0.05);
        float v2 = step(abs(cellUV.x - 0.65), 0.05);
        return max(max(h1, h2), max(v1, v2)) * 0.8;
    } else if (level == 8) {
        // '%' - dense diagonal
        float diag = sin((cellUV.x + cellUV.y) * 20.0) * 0.5 + 0.5;
        return step(0.4, diag) * 0.85;
    } else {
        // '@' - filled circle
        vec2 center = cellUV - 0.5;
        return smoothstep(0.35, 0.25, length(center));
    }
}

// Get luminance from color
float getLuma(vec3 color) {
    return dot(color, vec3(0.299, 0.587, 0.114));
}

void main() {
    // Default cell size
    float cw = charWidth > 0.0 ? charWidth : 8.0;
    float ch = charHeight > 0.0 ? charHeight : 16.0;

    // Calculate which character cell we're in
    vec2 pixelPos = fragCoord * iResolution;
    vec2 cellIndex = floor(pixelPos / vec2(cw, ch));
    vec2 cellUV = fract(pixelPos / vec2(cw, ch));

    // Sample center of the cell for color/brightness
    vec2 cellCenter = (cellIndex + 0.5) * vec2(cw, ch) / iResolution;
    vec3 sampleColor = texture(iChannel0, cellCenter).rgb;
    float brightness = getLuma(sampleColor);

    // Get character pattern value
    float pattern = getCharPattern(brightness, cellUV);

    // Apply color based on mode
    vec3 outputColor;

    if (colorMode == 0) {
        // Monochrome green terminal
        outputColor = vec3(0.2, 1.0, 0.3) * pattern;
    } else if (colorMode == 1) {
        // Colored - use original color
        outputColor = sampleColor * pattern;
    } else {
        // Neon - saturated with glow
        vec3 neonColor = normalize(sampleColor + 0.001) * 1.5;
        outputColor = neonColor * pattern;
        // Add subtle glow
        outputColor += sampleColor * 0.1;
    }

    // Add background
    outputColor = max(outputColor, vec3(bgBrightness));

    // Add subtle scanline effect for extra terminal feel
    float scanline = 0.95 + 0.05 * sin(pixelPos.y * 3.14159);
    outputColor *= scanline;

    fragColor = vec4(outputColor, 1.0);
}
