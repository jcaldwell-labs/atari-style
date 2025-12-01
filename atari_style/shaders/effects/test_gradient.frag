#version 330 core

// Shadertoy-compatible uniforms
uniform float iTime;
uniform vec2 iResolution;
uniform vec2 iMouse;
uniform vec4 iParams;

// Input from vertex shader
in vec2 fragCoord;

// Output color
out vec4 fragColor;

void main() {
    // Normalized coordinates [0, 1]
    vec2 uv = fragCoord;

    // Animated color gradient
    // Uses cosine palette technique from Inigo Quilez
    vec3 col = 0.5 + 0.5 * cos(iTime + uv.xyx * 6.28318 + vec3(0.0, 2.0, 4.0));

    // Modulate with iParams for interactivity
    col *= 0.5 + 0.5 * iParams.x;  // Brightness
    col = mix(col, col.gbr, iParams.y);  // Color shift

    // Add subtle pattern based on resolution
    float pattern = sin(uv.x * iResolution.x * 0.1) * sin(uv.y * iResolution.y * 0.1);
    col += pattern * 0.05 * iParams.z;

    // Output with full alpha
    fragColor = vec4(col, 1.0);
}
