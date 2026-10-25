#include "surface/session.hpp"
#include "surface/phantom.hpp"
#include <bit>
#include <cstring>
#include <stdexcept>
#include <algorithm>

namespace surface {
const char* observationName(Observation m){
    static constexpr const char* names[]={"coupled","magnetic","wave","heat","electric","light","cosmos"};
    const auto index=static_cast<unsigned>(m);if(index>6)throw std::invalid_argument("unknown observation");return names[index];
}
FieldView Session::fields()const{return {physics.w,physics.h,physics.time,physics.density,physics.heat,physics.pressure,physics.potential,physics.bx,physics.by,physics.ex,physics.ey};}
void Session::paint(float x,float y,float dx,float dy,float p){
    if(view.observation==Observation::Cosmos)return;
    physics.inject(x,y,dx,dy,p,.04f,observationName(view.observation));++view.inputSequence;
}
void Session::step(double dt){if(!view.paused&&view.observation!=Observation::Cosmos)physics.step(dt);}
void Session::nextObservation(){view.observation=static_cast<Observation>((static_cast<unsigned>(view.observation)+1)%7);}
std::vector<std::byte> Session::serialize()const{
    view.validate();if(!physics.validate())throw std::runtime_error("invalid physics snapshot");
    const auto state=physics.serialize();if(state.size()>10*1024*1024)throw std::runtime_error("state budget exceeded");
    std::vector<std::byte> out;out.reserve(state.size()+80);
    auto put=[&](std::uint64_t v,unsigned bytes){for(unsigned i=0;i<bytes;i++)out.push_back(std::byte((v>>(8*i))&255));};
    for(char c:std::string("SURFSES1"))out.push_back(std::byte(c));
    put(1,4);put(static_cast<unsigned>(view.observation),4);put(std::bit_cast<std::uint64_t>(view.yaw),8);put(std::bit_cast<std::uint64_t>(view.pitch),8);put(std::bit_cast<std::uint64_t>(view.zoom),8);
    put(view.paused,1);put(view.sound,1);put(0,2);put(view.generation,8);put(view.inputSequence,8);put(state.size(),8);out.insert(out.end(),state.begin(),state.end());return out;
}
void Session::restore(std::span<const std::byte> bytes){
    if(bytes.size()>=80&&std::memcmp(bytes.data(),"SURFEXP1",8)==0){
        std::uint64_t size=0;for(unsigned i=0;i<8;i++)size|=std::uint64_t(std::to_integer<unsigned>(bytes[8+i]))<<(8*i);
        if(size>10*1024*1024||size!=bytes.size()-80)throw std::invalid_argument("export length mismatch");
        const auto body=bytes.subspan(80);if(body.size()<8||std::memcmp(body.data(),"SURFSES1",8)!=0)throw std::invalid_argument("export payload schema");
        const auto digest=phantom::sha256(std::span<const std::uint8_t>(reinterpret_cast<const std::uint8_t*>(body.data()),body.size()));
        if(std::memcmp(bytes.data()+16,digest.data(),64)!=0)throw std::invalid_argument("export SHA256 mismatch");
        bytes=body;
    }
    if(bytes.size()<68||bytes.size()>10*1024*1024+80)throw std::invalid_argument("session length out of bounds");
    const char magic[]="SURFSES1";for(unsigned i=0;i<8;i++)if(bytes[i]!=std::byte(magic[i]))throw std::invalid_argument("session magic mismatch");
    std::size_t pos=8;auto read=[&](unsigned n){if(pos+n>bytes.size())throw std::invalid_argument("truncated session");std::uint64_t v=0;for(unsigned i=0;i<n;i++)v|=std::uint64_t(std::to_integer<unsigned>(bytes[pos++]))<<(8*i);return v;};
    if(read(4)!=1)throw std::invalid_argument("unsupported session schema");
    ViewState candidate;
    candidate.observation=static_cast<Observation>(read(4));candidate.yaw=std::bit_cast<double>(read(8));candidate.pitch=std::bit_cast<double>(read(8));candidate.zoom=std::bit_cast<double>(read(8));
    const auto paused=read(1),sound=read(1),reserved=read(2);if(paused>1||sound>1||reserved)throw std::invalid_argument("invalid session flags");candidate.paused=paused;candidate.sound=sound;candidate.generation=read(8);candidate.inputSequence=read(8);const auto length=read(8);
    if(length!=bytes.size()-pos)throw std::invalid_argument("session payload mismatch");
    candidate.validate();
    Physics next=physics;next.restore(bytes.subspan(pos));if(!next.validate())throw std::invalid_argument("physics admission failed");physics=std::move(next);view=candidate;
}
std::vector<std::byte> Session::exportFile()const{
    const auto body=serialize();std::vector<std::byte> out;out.reserve(body.size()+80);
    for(char c:std::string("SURFEXP1"))out.push_back(std::byte(c));
    for(unsigned i=0;i<8;i++)out.push_back(std::byte((std::uint64_t(body.size())>>(8*i))&255));
    const auto digest=phantom::sha256(std::span<const std::uint8_t>(reinterpret_cast<const std::uint8_t*>(body.data()),body.size()));
    for(char c:digest)out.push_back(std::byte(c));
    out.insert(out.end(),body.begin(),body.end());return out;
}
}
