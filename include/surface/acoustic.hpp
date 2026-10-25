#pragma once
#include <array>
#include <cstddef>
#include <span>
#include <string>
namespace surface {
// Rectangular pressure-release acoustic modes in homogeneous air, observed at a fixed microphone.
// Output is PCM from a declared 0.12 full-scale/Pa mapping, not calibrated speaker pressure.
class AcousticField {
public:
    explicit AcousticField(double sampleRate=48000,double widthMetres=2,double heightMetres=1.5);
    void strike(double x,double y,double pressurePa=1);
    void render(std::span<float> pcm);
    double frequency(int nx,int ny)const;
    double energyProxy()const;
    void writeWav(const std::string& path,double seconds);
private:
    struct Mode {double a=0,b=0,c=0,s=0,decay=0,observer=0;int nx=0,ny=0;};
    std::array<Mode,24> modes_{};
    double sampleRate_,width_,height_;
};
}
