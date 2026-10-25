#include "surface/physics.hpp"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
using namespace surface;
namespace {
template<class F> bool rejects(F action) { try { action(); return false; } catch (const std::exception&) { return true; } }
Physics blank(int w=65,int h=33) {
  Physics p(w,h,123);
  for(auto* a : {&p.density,&p.heat,&p.pressure,&p.velocity})std::fill(a->begin(),a->end(),0);
  p.sources.clear();p.diagnostics.circuit={};p.diagnostics.circuit.drive=0;p.diagnostics.memory={};
  return p;
}
float maximum(const std::vector<float>& a) {float m=0;for(float x:a)m=std::max(m,std::abs(x));return m;}
}
int main() {
  {
    Physics a(128,96,55),b(128,96,55); assert(a.serialize()==b.serialize()); assert(a.validate());
    assert(maximum(a.density)>.2f);
    assert(*std::min_element(a.potential.begin(),a.potential.end())<-2);
    assert(*std::max_element(a.potential.begin(),a.potential.end())>2);
    assert(std::any_of(a.sources.begin(),a.sources.end(),[](auto s){return s.x<.35;}));
    assert(std::any_of(a.sources.begin(),a.sources.end(),[](auto s){return s.x>.65;}));
  }
  {
    auto e=blank(); for(int y=0;y<e.h;y++)for(int x=0;x<e.w;x++)e.pressure[y*e.w+x]=.4*std::cos(3.141592653589793*x/(e.w-1));
    for(int i=0;i<120;i++)e.step(1./120);
    const double gamma=.12,omega=.48*3.141592653589793/2,wd=std::sqrt(omega*omega-gamma*gamma/4);
    const double expected=.4*std::exp(-gamma/2)*(std::cos(wd)+gamma/(2*wd)*std::sin(wd));
    assert(std::abs(e.pressure[16*65]-expected)<.004);
    assert(std::abs(e.pressure[16*65+32])<1e-5);
  }
  {
    auto e=blank();const int center=16*65+32;e.heat[center]=100;e.step(.1);
    assert(e.heat[center]>0&&e.heat[center]<100&&e.heat[center-1]>0&&e.heat[center+65]>0);
    assert(std::all_of(e.heat.begin(),e.heat.end(),[](float v){return v>=0&&v<=100;}));
  }
  {
    Source q; q.q=1e-9;q.core=.1f;
    const auto a=fieldAt(std::span(&q,1),1,0),b=fieldAt(std::span(&q,1),-1,0);
    assert(std::abs(a.potential-8.942948280)<1e-6);assert(std::abs(a.ex-8.854404238)<1e-6);
    assert(a.ey==0&&a.ex==-b.ex&&a.potential==b.potential);
    q.q=0;q.mx=1;const auto axis=fieldAt(std::span(&q,1),1,0),equator=fieldAt(std::span(&q,1),0,1);
    assert(axis.bx>0&&equator.bx<0&&axis.by==0&&equator.by==0);
    assert(std::abs(axis.bx-1.9703706737e-7)<1e-14);
    assert(std::isfinite(fieldAt(std::span(&q,1),0,0).bx));
  }
  {
    MagneticMemory m;m.relays.fill(-1);m.magnetization=-1;
    updateMagneticMemory(m,2);assert(m.magnetization==1);
    updateMagneticMemory(m,0);assert(m.magnetization==1);
    updateMagneticMemory(m,-2);assert(m.magnetization==-1);
  }
  {
    auto e=blank();e.inject(.5,.5,.1,.05,1,.05,"coupled");const int center=16*65+32;
    assert(e.density[center]>.5&&e.heat[center]>1&&std::abs(e.pressure[center])>.05);assert(e.sources.size()==2);
  }
  {
    auto e=blank();e.inject(.5,.5,.1,0,1,.05,"light");
    assert(maximum(e.density)>.5&&maximum(e.heat)==0&&maximum(e.pressure)==0&&e.sources.empty());
  }
  {
    Physics e(16,16);const auto before=e.diagnostics.circuit.soc;
    for(int i=0;i<360;i++)e.step(1./60);
    const auto c=e.diagnostics.circuit;
    assert(c.harvestedEnergy>0&&c.soc>before&&c.soc<=1);
    assert(std::abs(c.batteryEnergy-c.soc*432)<1e-8);
    assert(e.diagnostics.circuitStoredEnergy>=0&&c.dissipatedEnergy>0);
  }
  {
    auto e=blank(16,16);e.diagnostics.circuit.i1=1;
    e.step(.001);assert(e.diagnostics.circuit.i2>0);
    for(int i=0;i<100;i++)e.step(.001);
    const auto c=e.diagnostics.circuit;
    assert(e.diagnostics.circuitStoredEnergy+c.harvestedEnergy+c.dissipatedEnergy<=.200000001);
  }
  {
    Physics e(16,16);auto s=e.serialize();
    // A legal large sequence number must not wrap into an invalid live source identifier.
    for(int i=44;i<48;i++)s[i]=std::byte{0xff};
    e.restore(s);
    e.inject(.5,.5,.1,0);assert(e.validate());
  }
  {
    Physics a(32,24,91);a.inject(.42,.6,.02,-.01);for(int i=0;i<20;i++)a.step(1./60);
    const auto s=a.serialize();Physics b;b.restore(s);assert(b.serialize()==s);
    for(int i=0;i<30;i++){a.step(1./60);b.step(1./60);}
    assert(a.serialize()==b.serialize());assert(a.potential==b.potential&&a.bx==b.bx);
    auto corrupted=s;corrupted[0]=std::byte{0};assert(rejects([&]{b.restore(corrupted);}));
    const auto original=b.serialize();assert(rejects([&]{b.restore(std::span(s.data(),s.size()-1));}));assert(b.serialize()==original);
    auto trailing=s;trailing.push_back(std::byte{0});assert(rejects([&]{b.restore(trailing);}));
    // Header contains width at byte 12; reject huge dimensions before allocation.
    auto huge=s;for(int i=12;i<16;i++)huge[i]=std::byte{0xff};assert(rejects([&]{b.restore(huge);}));assert(b.serialize()==original);
    // First primary field starts at byte 56; poison it with a quiet NaN.
    auto nonfinite=s;nonfinite[56]=std::byte{0};nonfinite[57]=std::byte{0};nonfinite[58]=std::byte{0xc0};nonfinite[59]=std::byte{0x7f};
    assert(rejects([&]{b.restore(nonfinite);}));assert(b.serialize()==original);
  }
  {
    Physics e(16,16);const auto original=e.serialize();
    assert(rejects([&]{e.inject(NAN,.5);}));assert(rejects([&]{e.inject(.5,.5,NAN);}));
    assert(rejects([&]{e.step(-1);}));assert(rejects([&]{e.step(INFINITY);}));assert(e.serialize()==original);
    assert(rejects([]{Physics e(1,16);}));assert(rejects([]{Physics e(16,512);}));
    e.heat.pop_back();assert(!e.validate());assert(rejects([&]{e.step(.01);}));
  }
  {
    Physics e(32,24);for(int i=0;i<200;i++)e.inject((i%20)/19.f,(i%13)/12.f,.2,-.2,3);
    const auto t=e.time;e.step(3600);assert(e.time-t<=.1000001&&e.diagnostics.discardedTime>3599&&e.sources.size()<=32);
    for(int i=0;i<180;i++)e.step(1./30);
    assert(e.validate());
  }
  {
    const auto xyz=cieXYZ(479);
    assert(std::abs(xyz[0]-.1042979)<1e-12&&std::abs(xyz[1]-.1334528)<1e-12&&std::abs(xyz[2]-.8566193)<1e-12);
    const auto half=cieXYZ(479.5);
    assert(std::abs(half[0]-.09996895)<1e-12&&std::abs(half[1]-.1362364)<1e-12&&std::abs(half[2]-.8347847)<1e-12);
    const auto blue=wavelengthToLinearRGB(450),green=wavelengthToLinearRGB(530),red=wavelengthToLinearRGB(650);
    assert(blue[2]>blue[0]&&blue[2]>blue[1]);assert(green[1]>green[0]&&green[1]>green[2]);assert(red[0]>red[1]&&red[0]>red[2]);
    for(int nm=360;nm<=830;nm++)for(auto v:wavelengthToLinearRGB(nm))assert(std::isfinite(v)&&v>=0&&v<=1);
    assert((wavelengthToLinearRGB(100)==std::array<float,3>{0,0,0}));assert(rejects([]{wavelengthToLinearRGB(NAN);}));
    assert(faradayRotation(40,.2,.125)==1&&faradayRotation(40,-.2,.125)==-1);
    assert(malusTransmission(0)==1&&malusTransmission(3.141592653589793/2)<1e-30);
    assert(std::abs(malusTransmission(3.141592653589793/4)-.5)<1e-14);
    assert(std::abs(zeemanShiftHz(1)-13.996244917e9)<10);assert(zeemanShiftHz(0)==0);
    assert(rejects([]{faradayRotation(1,1,-1);}));assert(rejects([]{zeemanShiftHz(INFINITY);}));
  }
  std::cout<<"physics: seed, analytic wave, heat maximum principle, E/B reference, hysteresis, injection, RLC/battery, exact continuation, atomic malformed admission, long-step bounds and spectral references passed\n";
}
