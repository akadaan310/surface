#include "surface/acoustic.hpp"
#include <cmath>
#include <algorithm>
#include <fstream>
#include <stdexcept>
#include <vector>
#include <cstdint>
namespace surface {
constexpr double piAudio=3.14159265358979323846;
AcousticField::AcousticField(double rate,double width,double height):sampleRate_(rate),width_(width),height_(height){
 if(!std::isfinite(rate)||!std::isfinite(width)||!std::isfinite(height)||rate<8000||rate>192000||width<.1||height<.1||width>100||height>100)throw std::invalid_argument("invalid acoustic domain");
 std::size_t k=0;for(int ny=1;ny<=4;ny++)for(int nx=1;nx<=6;nx++){
  const double f=frequency(nx,ny);if(f>=rate*.45)throw std::invalid_argument("modal frequency violates Nyquist margin");
  auto& m=modes_[k++];m.nx=nx;m.ny=ny;m.c=std::cos(2*piAudio*f/rate);m.s=std::sin(2*piAudio*f/rate);m.decay=std::exp(-(1.2+.0008*f)/rate);m.observer=std::sin(piAudio*nx*.57)*std::sin(piAudio*ny*.51);
 }
}
double AcousticField::frequency(int nx,int ny)const{if(nx<1||ny<1||nx>100||ny>100)throw std::invalid_argument("invalid acoustic mode");return 343./2*std::sqrt(std::pow(nx/width_,2)+std::pow(ny/height_,2));}
void AcousticField::strike(double x,double y,double pressure){
 if(!std::isfinite(x)||!std::isfinite(y)||!std::isfinite(pressure)||x<0||x>1||y<0||y>1||std::abs(pressure)>20)throw std::invalid_argument("invalid acoustic impulse");
 for(auto& m:modes_)m.a=std::clamp(m.a+pressure*std::sin(piAudio*m.nx*x)*std::sin(piAudio*m.ny*y)/std::sqrt(double(m.nx*m.nx+m.ny*m.ny)),-8.,8.);
}
void AcousticField::render(std::span<float> pcm){
 if(pcm.size()>192000*30)throw std::invalid_argument("PCM budget exceeded");
 for(auto& sample:pcm){double p=0;for(auto& m:modes_){p+=m.a*m.observer;const double a=m.a*m.c-m.b*m.s,b=m.a*m.s+m.b*m.c;m.a=a*m.decay;m.b=b*m.decay;}sample=float(std::tanh(p*.12));}
}
double AcousticField::energyProxy()const{double v=0;for(const auto& m:modes_)v+=m.a*m.a+m.b*m.b;return v;}
void AcousticField::writeWav(const std::string& path,double seconds){
 if(!std::isfinite(seconds)||seconds<=0||seconds>30)throw std::invalid_argument("audio duration budget exceeded");
 std::vector<float> samples(std::size_t(sampleRate_*seconds));render(samples);
 std::ofstream out(path,std::ios::binary);if(!out)throw std::runtime_error("cannot write audio");auto le=[&](std::uint32_t v,int n){for(int i=0;i<n;i++)out.put(char((v>>(8*i))&255));};
 out.write("RIFF",4);le(36+std::uint32_t(samples.size()*2),4);out.write("WAVEfmt ",8);le(16,4);le(1,2);le(1,2);le(std::uint32_t(sampleRate_),4);le(std::uint32_t(sampleRate_*2),4);le(2,2);le(16,2);out.write("data",4);le(std::uint32_t(samples.size()*2),4);
 for(float s:samples){const auto v=std::int16_t(std::lround(std::clamp(s,-1.f,1.f)*32767));le(std::uint16_t(v),2);}if(!out)throw std::runtime_error("audio write failed");
}
}
