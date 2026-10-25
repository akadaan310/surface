#include "surface/atlas.hpp"
#include <cmath>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
void require(bool condition,const char* message){if(!condition)throw std::runtime_error(message);}
void near(double value,double wanted,double tolerance=1e-11){require(std::abs(value-wanted)<tolerance,"coordinate fixture mismatch");}
template<class F>void rejects(F f){bool caught=false;try{f();}catch(const std::invalid_argument&){caught=true;}require(caught,"invalid input was admitted");}
}
int main(int argc,char** argv){
    using namespace surface::atlas;
    auto x=equatorialToCartesian(0,0,2),y=equatorialToCartesian(90,0,3),z=equatorialToCartesian(0,90,4);
    near(x.x,2);near(x.y,0);near(x.z,0);near(y.x,0);near(y.y,3);near(z.z,4);
    rejects([]{equatorialToCartesian(0,91);});rejects([]{equatorialToCartesian(0,0,-1);});
    std::vector<Star> stars{{1,0,0,1,0,0,0,0},{2,90,0,2,0,0,0,0},{3,0,90,3,0,0,0,0},{4,180,0,4,0,0,0,0}};
    auto p=projectStars(stars,0,0,1,800,600);
    require(p.size()==3,"back hemisphere must be culled");near(p[0].x,400);near(p[0].y,300);near(p[1].x,700);near(p[2].y,0);
    auto rotated=projectStars(stars,std::acos(-1.0)/2,0,1,800,600);
    for(const auto& s:rotated)if(s.id==2)near(s.x,400);
    rejects([&]{projectStars(stars,0,0,1,0,600);});
    const std::string path=argc>1?argv[1]:"data/gaia.bin";
    std::ifstream stream(path,std::ios::binary);require(bool(stream),"catalogue file not found");
    std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(stream)),{});
    auto catalogue=loadCatalogue(bytes);require(catalogue.stars.size()==10000,"pinned count mismatch");near(catalogue.epochJulianYear,2016);
    require(catalogue.stars[0].id==1576683529448755328ULL,"64-bit Gaia ID changed");
    near(catalogue.stars[0].ra,193.50817846782095);near(catalogue.stars[0].dec,55.959784778923755);
    require(!(catalogue.stars[0].flags&ParallaxPresent),"missing parallax invented");
    auto corrupt=bytes;corrupt.back()^=1;rejects([&]{loadCatalogue(corrupt);});
    corrupt=bytes;corrupt[0]='x';rejects([&]{loadCatalogue(corrupt);});
    corrupt=bytes;corrupt.pop_back();rejects([&]{loadCatalogue(corrupt);});
    std::cout<<"atlas: cardinal bases, camera, 10000 IDs/coordinates, missingness, binary integrity passed\n";
}
