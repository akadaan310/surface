#pragma once
#include <array>
#include <cstdint>
#include <span>
#include <string>
#include <vector>

namespace surface {
enum class Observation : std::uint32_t { Coupled, Magnetic, Acoustic, Thermal, Electric, Optical, Cosmos };
struct ViewState {
    Observation observation=Observation::Coupled;
    double yaw=4.65, pitch=-0.18, zoom=1.25;
    bool paused=false, sound=false;
    std::uint64_t generation=0, inputSequence=0;
    void validate() const;
};
struct FieldView {
    int width=0,height=0;
    double time=0;
    std::span<const float> density,heat,pressure,potential,bx,by,ex,ey;
    void validate() const;
};
struct Color {float r=0,g=0,b=0;};
struct SkyPoint {double x=0,y=0;float magnitude=0,colorIndex=.9f;std::uint64_t id=0;};
struct RasterStats {std::uint64_t frames=0;double frameMilliseconds=0;std::size_t fieldSamples=0,drawnStars=0;};

// All image formation below is Surface's own CPU implementation.
class Renderer {
public:
    Renderer(int width,int height,std::size_t tracerCount=6000);
    void resize(int width,int height);
    void clear();
    void wake(float x,float y,float radius=.035f);
    void render(const FieldView&,const ViewState&,double displayDelta,bool advance=true);
    void renderSky(std::span<const SkyPoint> stars);
    void line(float x0,float y0,float x1,float y1,Color radiance);
    void splat(float x,float y,float radius,Color radiance);
    void writePPM(const std::string& path) const;
    std::span<const std::uint32_t> pixels() const noexcept {return rgba_;}
    int width() const noexcept{return width_;}
    int height() const noexcept{return height_;}
    const RasterStats& stats() const noexcept{return stats_;}
    static float sample(std::span<const float>,int width,int height,float x,float y);
    static Color spectralColor(double wavelengthNm);
private:
    struct Tracer {float x,y,age,life,direction,variation;};
    int width_=0,height_=0;
    std::uint32_t randomState_=0x5a17c3;
    std::size_t wakeIndex_=0;
    bool warmed_=false;
    Observation previous_=Observation::Coupled;
    std::vector<Color> ink_;
    std::vector<std::uint32_t> rgba_;
    std::vector<Tracer> tracers_;
    std::array<Color,128> colors_;
    std::array<std::uint8_t,8192> displayLut_;
    RasterStats stats_;
    float random();
    void spawn(Tracer&,const FieldView* field=nullptr);
    void trace(const FieldView&,Observation,double dt);
    void shade(const FieldView&,Observation,double dt);
    void add(int x,int y,Color c,float coverage);
    std::uint32_t encode(Color)const;
};
}
