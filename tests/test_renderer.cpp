#include "surface/renderer.hpp"
#include <cassert>
#include <cmath>
#include <iostream>
#include <limits>
#include <vector>
using namespace surface;
template<class F> bool rejects(F f){try{f();return false;}catch(const std::exception&){return true;}}
int main(){
    std::vector<float> f{0,2,4,6};
    assert(std::abs(Renderer::sample(f,2,2,.5,.5)-3)<1e-7);
    assert(Renderer::sample(f,2,2,1,1)==6);
    assert(Renderer::sample(f,2,2,-3,2)==4);
    assert(rejects([]{Renderer r(100000,100000);}));
    ViewState v;v.zoom=std::numeric_limits<double>::infinity();assert(rejects([&]{v.validate();}));
    v={};v.observation=static_cast<Observation>(99);assert(rejects([&]{v.validate();}));
    Renderer r(64,64,50);r.line(-100,-100,200,200,{1,1,1});r.line(100000,0,100000,300,{1,1,1});
    r.splat(32,32,4,{1,1,1});r.renderSky(std::vector<SkyPoint>{{32,32,1,.4,1}});
    auto p=r.pixels();assert(p.size()==4096);
    assert((p[32*64+32]&0x00ffffff)!=(p[0]&0x00ffffff));
    assert((p[0]>>24)==255);
    assert(rejects([&]{r.line(NAN,0,2,2,{1,1,1});}));
    const auto green=Renderer::spectralColor(550);assert(green.g>green.r&&green.g>green.b);
    const auto red=Renderer::spectralColor(650);assert(red.r>red.g&&red.r>red.b);
    std::cout<<"renderer: interpolation, clipping, dimensions, view validation, star pixels, finite admission, spectral observer passed\n";
}
