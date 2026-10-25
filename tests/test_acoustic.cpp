#include "surface/acoustic.hpp"
#include <cassert>
#include <cmath>
#include <iostream>
#include <vector>
int main(){
 surface::AcousticField field;assert(std::abs(field.frequency(1,1)-142.91666666666666)<1e-10);
 std::vector<float> pcm(48000);field.render(pcm);for(auto v:pcm)assert(v==0);
 field.strike(.37,.42,1);const auto before=field.energyProxy();field.render(pcm);assert(field.energyProxy()<before);
 double energy=0;for(float v:pcm){assert(std::isfinite(v)&&std::abs(v)<=1);energy+=v*v;}assert(energy>.001);
 bool bad=false;try{field.strike(NAN,0);}catch(...){bad=true;}assert(bad);
 std::cout<<"acoustic: analytical room mode, silence, passive decay, bounded PCM and input rejection passed\n";
}
