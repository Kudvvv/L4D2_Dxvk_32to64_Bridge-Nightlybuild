#include "ReShade.fxh"

uniform float FogStart <
    ui_type = "slider";
    ui_min = 0.0; ui_max = 10000.0;
    ui_label = "Fog Start";
> = 500.0;

uniform float FogRange <
    ui_type = "slider";
    ui_min = 0.0; ui_max = 10000.0;
    ui_label = "Fog Range";
> = 500.0;

uniform float FogMaxDensity <
    ui_type = "slider";
    ui_min = 0.0; ui_max = 1.0;
    ui_label = "Max Density";
> = 1.0;

uniform float ZFar <
    ui_type = "slider";
    ui_min = 1000.0; ui_max = 50000.0;
    ui_label = "Z-Far";
> = 8192.0;

uniform float Factor <
    ui_type = "slider";
    ui_min = 0.1; ui_max = 10.0;
    ui_label = "Factor";
> = 1;

texture2D L4N_FrameBufferCopy { Width = BUFFER_WIDTH; Height = BUFFER_HEIGHT; Format = RGBA8; };
sampler2D SamplerSavedFrame { 
    Texture = L4N_FrameBufferCopy;
    //SRGBTexture = true;
};

float4 PS_SaveFrame(float4 pos : SV_Position, float2 texcoord : TEXCOORD) : SV_Target
{
    return tex2D(ReShade::BackBuffer, texcoord);
}

float4 PS_SourceEngineFog(float4 vpos : SV_Position, float2 texcoord : TexCoord) : SV_Target
{
    float4 finalColor = tex2D(ReShade::BackBuffer, texcoord);

    float depthNorm = ReShade::GetLinearizedDepth(texcoord);

    float worldDepth = depthNorm * ZFar;
    
    //float fogRange = max(FogEnd - FogStart, 0.0001); 
    
    float fogFactor = (worldDepth - FogStart) / FogRange;
    
    fogFactor = clamp(fogFactor, 0.0, FogMaxDensity);

    finalColor.rgb = lerp(finalColor.rgb, tex2D(SamplerSavedFrame, texcoord).rgb, saturate(fogFactor * Factor));

    return finalColor;
}

technique SpatialMask_Begin
< 
    ui_label = "L4N: Spatial Mask - Begin";
>
{
    pass 
    { 
        VertexShader = PostProcessVS;
        PixelShader = PS_SaveFrame;
        RenderTarget = L4N_FrameBufferCopy;
    }
}

technique SpatialMask_End
< 
    ui_label = "L4N: Spatial Mask - End";
>
{
    pass
    {
        VertexShader = PostProcessVS;
        PixelShader = PS_SourceEngineFog;
    }
}