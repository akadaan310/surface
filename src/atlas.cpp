#include "surface/atlas.hpp"
#include <algorithm>
#include <bit>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <unordered_set>

namespace surface::atlas {
namespace {
constexpr double pi=3.1415926535897932384626433832795,rad=pi/180;
[[noreturn]]void invalid(const char* message){throw std::invalid_argument(message);}
std::uint64_t little(std::span<const std::uint8_t> bytes,std::size_t at,unsigned count){
    if(at>bytes.size()||count>bytes.size()-at)invalid("truncated atlas");
    std::uint64_t value=0;for(unsigned i=0;i<count;i++)value|=std::uint64_t(bytes[at+i])<<(8*i);return value;
}
double f64(std::span<const std::uint8_t> bytes,std::size_t at){return std::bit_cast<double>(little(bytes,at,8));}
float f32(std::span<const std::uint8_t> bytes,std::size_t at){return std::bit_cast<float>(std::uint32_t(little(bytes,at,4)));}
std::uint32_t crc32(std::span<const std::uint8_t> bytes){
    std::uint32_t crc=0xffffffffU;for(auto byte:bytes){crc^=byte;for(unsigned k=0;k<8;k++)crc=(crc>>1)^(0xedb88320U&(0U-(crc&1U)));}return ~crc;
}
void validate(const Star& star){
    if(!star.id||!std::isfinite(star.ra)||star.ra<0||star.ra>=360||
       !std::isfinite(star.dec)||star.dec< -90||star.dec>90||!std::isfinite(star.mag)||
       !std::isfinite(star.colorIndex)||!std::isfinite(star.parallaxMas)||!std::isfinite(star.parallaxErrorMas)||
       (star.flags&~7U))invalid("invalid catalogue measurement");
    if(!(star.flags&ColorPresent)&&star.colorIndex!=0)invalid("absent color must have zero storage");
    if(!(star.flags&ParallaxPresent)&&star.parallaxMas!=0)invalid("absent parallax must have zero storage");
    if(!(star.flags&ParallaxErrorPresent)&&star.parallaxErrorMas!=0)invalid("absent uncertainty must have zero storage");
    if((star.flags&ParallaxErrorPresent)&&star.parallaxErrorMas<0)invalid("negative parallax uncertainty");
}
}

Catalogue loadCatalogue(std::span<const std::uint8_t> bytes){
    static_assert(sizeof(double)==8&&sizeof(float)==4&&std::numeric_limits<double>::is_iec559&&std::numeric_limits<float>::is_iec559);
    constexpr std::uint8_t magic[]{'S','G','A','I','A','0','0','1'};
    if(bytes.size()<72||!std::equal(std::begin(magic),std::end(magic),bytes.begin()))invalid("atlas magic/header mismatch");
    if(little(bytes,8,4)!=1||little(bytes,12,4)!=72||little(bytes,16,4)!=56||little(bytes,68,4)!=0)invalid("unsupported atlas schema");
    const auto count=little(bytes,20,4);
    if(count>20000||bytes.size()!=72+count*56)invalid("atlas count/length outside budget");
    if(crc32(bytes.subspan(72))!=little(bytes,64,4))invalid("atlas payload checksum mismatch");
    Catalogue out;out.epochJulianYear=f64(bytes,24);
    if(out.epochJulianYear!=2016.0)invalid("unexpected catalogue epoch");
    out.stars.reserve(count);std::unordered_set<std::uint64_t> ids;ids.reserve(count);
    for(std::size_t i=0;i<count;i++){
        const std::size_t at=72+i*56;
        Star star{little(bytes,at,8),f64(bytes,at+8),f64(bytes,at+16),f32(bytes,at+24),f32(bytes,at+28),
            f64(bytes,at+32),f64(bytes,at+40),std::uint32_t(little(bytes,at+48,4))};
        if(little(bytes,at+52,4)!=0)invalid("nonzero reserved atlas field");
        validate(star);
        if(!ids.insert(star.id).second)invalid("duplicate Gaia source ID");
        out.stars.push_back(star);
    }
    return out;
}
Vec3 equatorialToCartesian(double raDeg,double decDeg,double distance){
    if(!std::isfinite(raDeg)||!std::isfinite(decDeg)||!std::isfinite(distance)||decDeg< -90||decDeg>90||distance<0)invalid("invalid equatorial coordinate");
    const double ra=std::fmod(raDeg,360.0)*rad,dec=decDeg*rad,c=std::cos(dec);
    return {distance*c*std::cos(ra),distance*c*std::sin(ra),distance*std::sin(dec)};
}
std::vector<ProjectedStar> projectStars(std::span<const Star> stars,double yaw,double pitch,double zoom,
    int width,int height,float maxMagnitude){
    if(stars.size()>20000||!std::isfinite(yaw)||!std::isfinite(pitch)||!std::isfinite(zoom)||!std::isfinite(maxMagnitude)||
       pitch< -pi/2||pitch>pi/2||zoom<=0||zoom>1000||width<=0||height<=0||width>32768||height>32768)invalid("invalid bounded atlas camera");
    const double radius=std::min(width,height)*.5*zoom,sp=std::sin(pitch),cp=std::cos(pitch);
    std::vector<ProjectedStar> out;out.reserve(stars.size()/2);
    for(const auto& star:stars){
        validate(star);if(star.mag>maxMagnitude)continue;
        const double d=star.dec*rad,a=star.ra*rad-yaw,cd=std::cos(d),sd=std::sin(d),ca=std::cos(a),depth=cd*ca*cp+sd*sp;
        if(depth< -1e-12)continue;
        out.push_back({star.id,float(width*.5+radius*cd*std::sin(a)),float(height*.5-radius*(sd*cp-cd*ca*sp)),
            float(std::max(0.,depth)),star.mag,star.colorIndex,star.flags});
    }
    return out;
}
} // namespace surface::atlas
