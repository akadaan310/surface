#include "surface/physics.hpp"
#include <algorithm>
#include <bit>
#include <cmath>
#include <limits>
#include <numbers>
#include <stdexcept>
#include <type_traits>

namespace surface {
static_assert(sizeof(float)==4&&sizeof(double)==8&&std::numeric_limits<float>::is_iec559&&std::numeric_limits<double>::is_iec559, "Physics checkpoint requires IEEE-754 binary32/binary64");
namespace {
constexpr double PI=std::numbers::pi, LX=2, SPEED=.48, DAMPING=.12;
constexpr double HEAT_DIFFUSIVITY=.0005, HEAT_COOLING=.025, TRACER_DIFFUSIVITY=.00008;
constexpr double COULOMB=8.9875517923e9, MU_OVER_4PI=1e-7, BATTERY_CAPACITY=432;
constexpr double L1=.4,L2=.25,M=.42*.31622776601683794,C1=.02,C2=.03,R1=1.2,R2=.8,RLOAD=2.2;
constexpr std::size_t MAX_SOURCES=32;
constexpr double CIE[471][3]={
#include "cie1931.inc"
};
bool finite(double x) { return std::isfinite(x); }
bool in(double x,double low,double high) { return finite(x)&&x>=low&&x<=high; }
void require(bool condition,const char* message) { if(!condition)throw std::invalid_argument(message); }
void dimensions(int w,int h) { require(w>=16&&w<=256&&h>=16&&h<=256&&std::size_t(w)*h<=65536,"physics dimensions outside bounded domain"); }
double ly(int w,int h) {return LX*double(h-1)/(w-1);}
double sample(const std::vector<float>& a,int w,int h,double x,double y) {
  x=std::clamp(x,0.,double(w-1));y=std::clamp(y,0.,double(h-1));
  const int ix=int(x),iy=int(y),jx=std::min(ix+1,w-1),jy=std::min(iy+1,h-1);
  const double tx=x-ix,ty=y-iy;
  return (a[iy*w+ix]*(1-tx)+a[iy*w+jx]*tx)*(1-ty)+(a[jy*w+ix]*(1-tx)+a[jy*w+jx]*tx)*ty;
}
void addSourceField(FieldSample& f,const Source& source,double x,double y) {
  const double rx=x-source.x,ry=y-source.y,a2=double(source.core)*source.core;
  const double r2=rx*rx+ry*ry,inv=1/std::sqrt(r2+a2),inv3=inv*inv*inv,inv5=inv3*inv*inv;
  const double weight=source.life<0?1:std::clamp(source.life/source.initialLife,0.,1.);
  const double kq=COULOMB*source.q*weight;
  f.potential+=kq*inv;f.ex+=kq*rx*inv3;f.ey+=kq*ry*inv3;
  // Curl in 3D of A=(mu0/4pi)(m cross r)/(r^2+a^2)^(3/2), sampled at z=0.
  const double dot=source.mx*rx+source.my*ry;
  f.bx+=MU_OVER_4PI*weight*(3*rx*dot+(2*a2-r2)*source.mx)*inv5;
  f.by+=MU_OVER_4PI*weight*(3*ry*dot+(2*a2-r2)*source.my)*inv5;
}
struct Writer {
  std::vector<std::byte> bytes;
  template<class T> void integer(T x) {static_assert(std::is_unsigned_v<T>);for(unsigned i=0;i<sizeof(T);i++)bytes.push_back(std::byte((x>>(8*i))&255));}
  void f32(float x){integer(std::bit_cast<std::uint32_t>(x));}
  void f64(double x){integer(std::bit_cast<std::uint64_t>(x));}
};
struct Reader {
  std::span<const std::byte> data;std::size_t pos=0;
  template<class T> T integer(){static_assert(std::is_unsigned_v<T>);require(pos<=data.size()&&sizeof(T)<=data.size()-pos,"truncated physics checkpoint");T x=0;for(unsigned i=0;i<sizeof(T);i++)x|=T(std::to_integer<unsigned char>(data[pos++]))<<(8*i);return x;}
  float f32(){return std::bit_cast<float>(integer<std::uint32_t>());}
  double f64(){return std::bit_cast<double>(integer<std::uint64_t>());}
};
}

FieldSample fieldAt(std::span<const Source> sources,double x,double y) {
  require(finite(x)&&finite(y)&&std::abs(x)<=1e6&&std::abs(y)<=1e6&&sources.size()<=MAX_SOURCES,"invalid field query");
  FieldSample f;
  for(const auto& s:sources){
    require(finite(s.x)&&finite(s.y)&&in(s.core,.001,10)&&in(s.q,-1,1)&&in(s.mx,-1e6,1e6)&&in(s.my,-1e6,1e6),"invalid regularized source");
    require(s.life==-1||(in(s.life,0,120)&&in(s.initialLife,.001,120)&&s.life<=s.initialLife),"invalid source lifetime");
    addSourceField(f,s,x,y);
  }
  return f;
}
void updateMagneticMemory(MagneticMemory& m,double applied) {
  require(in(applied,-1e6,1e6),"invalid magnetic drive");
  int total=0;
  for(std::size_t i=0;i<m.relays.size();i++){
    require(m.relays[i]>=-1&&m.relays[i]<=1,"invalid magnetic relay");
    const double hc=.15+.65*i/(m.relays.size()-1);
    if(applied>hc)m.relays[i]=1;else if(applied<-hc)m.relays[i]=-1;
    total+=m.relays[i];
  }
  m.appliedField=applied;m.magnetization=double(total)/m.relays.size();
}
std::array<double,3> cieXYZ(double nm) {
  require(finite(nm),"nonfinite wavelength");if(nm<360||nm>830)return {0,0,0};
  const int i=int(std::floor(nm))-360,j=std::min(i+1,470);const double t=nm-360-i;
  return {CIE[i][0]*(1-t)+CIE[j][0]*t,CIE[i][1]*(1-t)+CIE[j][1]*t,CIE[i][2]*(1-t)+CIE[j][2]*t};
}
std::array<float,3> wavelengthToLinearRGB(double nm) {
  const auto xyz=cieXYZ(nm);const auto x=xyz[0],y=xyz[1],z=xyz[2];
  double r=std::max(0.,3.2406*x-1.5372*y-.4986*z),g=std::max(0.,-.9689*x+1.8758*y+.0415*z),b=std::max(0.,.0557*x-.2040*y+1.0570*z);
  const double scale=std::max({1.,r,g,b});return {float(r/scale),float(g/scale),float(b/scale)};
}
double faradayRotation(double verdet,double b,double length){require(finite(verdet)&&finite(b)&&in(length,0,1e9),"invalid Faraday parameters");const double out=verdet*b*length;require(finite(out),"overflowing Faraday rotation");return out;}
double malusTransmission(double angle){require(finite(angle),"invalid polarizer angle");const double c=std::cos(angle);return c*c;}
double zeemanShiftHz(double b,double g,double deltaM){require(finite(b)&&finite(g)&&finite(deltaM),"invalid Zeeman parameters");const double out=1.39962449171e10*b*g*deltaM;require(finite(out),"overflowing Zeeman shift");return out;}

Physics::Physics(int width,int height,std::uint64_t seed):w(width),h(height){dimensions(w,h);allocate();reset(seed);}
void Physics::allocate(){
  const std::size_t n=std::size_t(w)*h;
  for(auto* a:{&density,&heat,&pressure,&velocity,&potential,&bx,&by,&ex,&ey,&pressureNext_,&heatNext_,&densityDiff_,&densityNext_})a->assign(n,0);
}
double Physics::random(){rng_^=rng_>>12;rng_^=rng_<<25;rng_^=rng_>>27;return double((rng_*2685821657736338717ULL)>>11)*(1./9007199254740992.);}
void Physics::reset(std::uint64_t seed){
  dimensions(w,h);allocate();time=0;seed_=seed;rng_=seed?seed:0x9e3779b97f4a7c15ULL;nextSourceId_=0;sources.clear();diagnostics={};
  const double height=ly(w,h),phase=random()*2*PI;
  for(int j=0;j<6;j++){
    const double a=phase+j*2*PI/6,sign=j%2?-1:1;
    Source s;s.id=nextSourceId_++;s.x=float(.5+.32*std::cos(a));s.y=float(.5+.30*std::sin(a));
    s.q=sign*(1.8+random()*.5)*1e-10;s.mx=.12*std::cos(a+PI*.5);s.my=.12*std::sin(a+PI*.5);s.core=.065f;sources.push_back(s);
  }
  for(int y=0;y<h;y++)for(int x=0;x<w;x++){
    const int i=y*w+x;const double px=double(x)/(w-1),py=double(y)/(h-1);
    for(std::size_t j=0;j<sources.size();j++){
      const double rx=(px-sources[j].x)*LX,ry=(py-sources[j].y)*height,r2=rx*rx+ry*ry;
      const double envelope=std::exp(-r2/.075),r=std::sqrt(r2),a=std::atan2(ry,rx);
      density[i]+=float(envelope*(.55+.45*std::pow(std::cos(3*a+14*r+phase),2)));
      heat[i]+=float((9+2*(j%3))*envelope);
      pressure[i]+=float((j%2?-1:1)*.25*std::cos(19*r)*envelope);
    }
  }
  for(std::size_t i=0;i<diagnostics.memory.relays.size();i++)diagnostics.memory.relays[i]=i%2?-1:1;
  updateMagneticMemory(diagnostics.memory,0);refreshFields();refreshDiagnostics();
}
void Physics::refreshFields(){
  std::array<Source,MAX_SOURCES> physical{};std::size_t count=0;const double height=ly(w,h);
  for(auto s:sources){s.x=float(s.x*LX);s.y=float(s.y*height);physical[count++]=s;}
  diagnostics.maxE=diagnostics.maxB=0;
  for(int y=0;y<h;y++)for(int x=0;x<w;x++){
    FieldSample f;for(std::size_t k=0;k<count;k++)addSourceField(f,physical[k],LX*x/(w-1),height*y/(h-1));
    const int i=y*w+x;potential[i]=float(f.potential);ex[i]=float(f.ex);ey[i]=float(f.ey);bx[i]=float(f.bx);by[i]=float(f.by);
    diagnostics.maxE=std::max(diagnostics.maxE,std::hypot(f.ex,f.ey));diagnostics.maxB=std::max(diagnostics.maxB,std::hypot(f.bx,f.by));
  }
}
void Physics::refreshDiagnostics(){
  const double dx=LX/(w-1),dy=ly(w,h)/(h-1);double energy=0,thermal=0,tracer=0;
  for(int y=0;y<h;y++)for(int x=0;x<w;x++){
    const int i=y*w+x;const double weight=(x==0||x==w-1?.5:1)*(y==0||y==h-1?.5:1);
    const double gx=(pressure[y*w+std::min(x+1,w-1)]-pressure[y*w+std::max(x-1,0)])/(2*dx);
    const double gy=(pressure[std::min(y+1,h-1)*w+x]-pressure[std::max(y-1,0)*w+x])/(2*dy);
    energy+=weight*.5*(double(velocity[i])*velocity[i]+SPEED*SPEED*(gx*gx+gy*gy));thermal+=weight*heat[i];tracer+=weight*density[i];
  }
  diagnostics.waveEnergy=energy*dx*dy;diagnostics.thermalIntegral=thermal*dx*dy;diagnostics.tracerIntegral=tracer*dx*dy;
  const auto& c=diagnostics.circuit;
  diagnostics.circuitStoredEnergy=.5*L1*c.i1*c.i1+.5*L2*c.i2*c.i2+M*c.i1*c.i2+c.q1*c.q1/(2*C1)+c.q2*c.q2/(2*C2);
}
void Physics::inject(float x,float y,float dx,float dy,float strength,float radius,const std::string& mode){
  require(finite(x)&&finite(y)&&finite(dx)&&finite(dy)&&finite(strength)&&finite(radius),"nonfinite injection");
  require(validate(),"invalid live physics state");
  x=std::clamp(x,0.f,1.f);y=std::clamp(y,0.f,1.f);dx=std::clamp(dx,-1.f,1.f);dy=std::clamp(dy,-1.f,1.f);
  strength=std::clamp(strength,-3.f,3.f);radius=std::clamp(radius,.005f,.2f);if(strength==0)return;
  const bool thermal=mode=="heat"||mode=="thermal",wave=mode=="wave"||mode=="acoustic",electric=mode=="electric",magnetic=mode=="magnetic",ink=mode=="ink"||mode=="optical"||mode=="light";
  const bool coupled=!(thermal||wave||electric||magnetic||ink);const double sigma=radius*LX,inv=1/(2*sigma*sigma),height=ly(w,h),amount=std::abs(strength);
  for(int iy=0;iy<h;iy++)for(int ix=0;ix<w;ix++){
    const double rx=(double(ix)/(w-1)-x)*LX,ry=(double(iy)/(h-1)-y)*height;
    const double g=std::exp(-(rx*rx+ry*ry)*inv);if(g<1e-6)continue;const int i=iy*w+ix;
    density[i]=float(std::min(64.,density[i]+.95*amount*g));
    if(coupled||thermal)heat[i]=float(std::min(2000.,heat[i]+22*amount*g));
    if(coupled||wave){pressure[i]=float(std::clamp(pressure[i]+.35*strength*g,-32.,32.));velocity[i]=float(std::clamp(velocity[i]+.35*strength*g,-4096.,4096.));}
  }
  if(coupled||electric||magnetic){
    // Source identifiers are local, so compact before a two-source insertion can wrap.
    if(nextSourceId_>std::numeric_limits<std::uint32_t>::max()-2){
      nextSourceId_=0;
      for(auto& source:sources)source.id=nextSourceId_++;
    }
    double vx=dx,vy=dy,mag=std::hypot(vx,vy);if(mag<1e-5){const double angle=random()*2*PI;vx=std::cos(angle);vy=std::sin(angle);}else{vx/=mag;vy/=mag;}
    for(int sign:{-1,1}){
      if(sources.size()>=MAX_SOURCES){auto it=std::find_if(sources.begin(),sources.end(),[](const auto& s){return s.life>=0;});sources.erase(it==sources.end()?sources.begin():it);}
      Source s;s.id=nextSourceId_++;s.x=float(std::clamp(x+sign*vx*radius*.7,0.,1.));s.y=float(std::clamp(y+sign*vy*radius*.7*LX/height,0.,1.));
      s.q=magnetic?0:sign*strength*2e-10;s.mx=electric?0:sign*strength*.09*vx;s.my=electric?0:sign*strength*.09*vy;
      s.core=float(std::max(.035,sigma*.65));s.life=s.initialLife=12;sources.push_back(s);
    }
  }
  diagnostics.circuit.drive=std::min(8.,diagnostics.circuit.drive+.08*amount);
  updateMagneticMemory(diagnostics.memory,std::clamp(diagnostics.memory.appliedField+.6*strength*(dx<0?-1:1),-4.,4.));
  diagnostics.injections++;refreshFields();refreshDiagnostics();
}
void Physics::integrateCircuit(double dt){
  auto& c=diagnostics.circuit;c.drivePhase=std::fmod(c.drivePhase+2*PI*1.5*dt,2*PI);
  const double a=L1/dt+R1+dt/C1,b=M/dt,d=L2/dt+R2+RLOAD+dt/C2;
  const double r1=c.drive*std::sin(c.drivePhase)+(L1*c.i1+M*c.i2)/dt-c.q1/C1,r2=(M*c.i1+L2*c.i2)/dt-c.q2/C2,det=a*d-b*b;
  c.i1=(r1*d-b*r2)/det;c.i2=(a*r2-b*r1)/det;c.q1+=dt*c.i1;c.q2+=dt*c.i2;
  const double loadEnergy=RLOAD*c.i2*c.i2*dt,accepted=std::min(BATTERY_CAPACITY-c.batteryEnergy,.82*loadEnergy);
  c.batteryEnergy+=accepted;c.soc=c.batteryEnergy/BATTERY_CAPACITY;c.harvestedEnergy+=accepted;
  c.dissipatedEnergy+=dt*(R1*c.i1*c.i1+R2*c.i2*c.i2)+loadEnergy-accepted;
  c.drive*=std::exp(-.008*dt);
}
void Physics::integrate(double dt){
  const double dx=LX/(w-1),dy=ly(w,h)/(h-1),ix2=1/(dx*dx),iy2=1/(dy*dy),heatDecay=std::exp(-HEAT_COOLING*dt),tracerDecay=std::exp(-.016*dt);
  for(int y=0;y<h;y++)for(int x=0;x<w;x++){
    const int i=y*w+x,l=y*w+(x==0?1:x-1),r=y*w+(x==w-1?w-2:x+1),u=(y==0?1:y-1)*w+x,d=(y==h-1?h-2:y+1)*w+x;
    const double lap=(pressure[l]+pressure[r]-2*pressure[i])*ix2+(pressure[u]+pressure[d]-2*pressure[i])*iy2;
    const double v=(velocity[i]+dt*SPEED*SPEED*lap)/(1+DAMPING*dt),p=pressure[i]+dt*v;
    const double vc=std::clamp(v,-4096.,4096.),pc=std::clamp(p,-32.,32.);if(v!=vc||p!=pc)diagnostics.limitedCells++;
    velocity[i]=float(vc);pressureNext_[i]=float(pc);
    const double hlap=(heat[l]+heat[r]-2*heat[i])*ix2+(heat[u]+heat[d]-2*heat[i])*iy2;
    heatNext_[i]=float(std::clamp((heat[i]+dt*HEAT_DIFFUSIVITY*hlap)*heatDecay,0.,2000.));
    const double dlap=(density[l]+density[r]-2*density[i])*ix2+(density[u]+density[d]-2*density[i])*iy2;
    densityDiff_[i]=float(std::clamp(density[i]+dt*TRACER_DIFFUSIVITY*dlap,0.,64.));
  }
  for(int y=0;y<h;y++)for(int x=0;x<w;x++){
    const int i=y*w+x;const double vx=-ey[i]*.00008,vy=ex[i]*.00008;
    densityNext_[i]=float(sample(densityDiff_,w,h,x-vx*dt/dx,y-vy*dt/dy)*tracerDecay);
  }
  pressure.swap(pressureNext_);heat.swap(heatNext_);density.swap(densityNext_);integrateCircuit(dt);
  updateMagneticMemory(diagnostics.memory,diagnostics.memory.appliedField*std::exp(-.7*dt));
}
void Physics::step(double dt){
  require(finite(dt)&&dt>=0,"invalid timestep");require(validate(),"invalid live physics state");if(dt==0)return;
  const double accepted=std::min(dt,.1);diagnostics.discardedTime=std::min(1e100,diagnostics.discardedTime+(dt-accepted));
  const double dx=LX/(w-1),dy=ly(w,h)/(h-1),sum=1/(dx*dx)+1/(dy*dy);
  const double bound=std::min({1./120,.65/(SPEED*std::sqrt(sum)),.24/(HEAT_DIFFUSIVITY*sum)});
  const int steps=int(std::ceil(accepted/bound));const double sub=accepted/steps;refreshFields();
  for(int i=0;i<steps;i++)integrate(sub);
  time+=accepted;diagnostics.steps+=std::uint64_t(steps);
  for(auto& s:sources)if(s.life>=0)s.life=std::max(0.,s.life-accepted);
  sources.erase(std::remove_if(sources.begin(),sources.end(),[](const auto& s){return s.life==0;}),sources.end());
  refreshFields();refreshDiagnostics();
}

bool Physics::validate() const {
  if(w<16||w>256||h<16||h>256||std::size_t(w)*h>65536||!in(time,0,1e100)||rng_==0||sources.size()>MAX_SOURCES)return false;
  const auto n=std::size_t(w)*h;
  auto field=[&](const auto& a,double lo,double hi){return a.size()==n&&std::all_of(a.begin(),a.end(),[&](auto x){return in(x,lo,hi);});};
  if(!field(density,0,64)||!field(heat,0,2000)||!field(pressure,-32,32)||!field(velocity,-4096,4096))return false;
  for(const auto* a:{&potential,&ex,&ey,&bx,&by})if(!field(*a,-1e12,1e12))return false;
  for(std::size_t i=0;i<sources.size();i++){
    const auto& s=sources[i];if(!in(s.x,0,1)||!in(s.y,0,1)||!in(s.q,-8e-9,8e-9)||!in(s.mx,-1,1)||!in(s.my,-1,1)||!in(s.core,.01,.5))return false;
    if(!(s.life==-1&&s.initialLife==-1)&&!(in(s.life,0,120)&&in(s.initialLife,.001,120)&&s.life<=s.initialLife))return false;
    if(s.id>=nextSourceId_)return false;
    for(std::size_t j=0;j<i;j++)if(sources[j].id==s.id)return false;
  }
  const auto& c=diagnostics.circuit;
  for(double x:{c.i1,c.i2,c.q1,c.q2})if(!in(x,-100,100))return false;
  if(!in(c.soc,0,1)||!in(c.batteryEnergy,0,BATTERY_CAPACITY)||std::abs(c.soc*BATTERY_CAPACITY-c.batteryEnergy)>1e-8||!in(c.drivePhase,0,2*PI)||!in(c.drive,0,8)||!in(c.harvestedEnergy,0,1e100)||!in(c.dissipatedEnergy,0,1e100))return false;
  const auto& m=diagnostics.memory;int relaySum=0;for(auto r:m.relays){if(r<-1||r>1)return false;relaySum+=r;}
  if(!in(m.magnetization,-1,1)||std::abs(m.magnetization-double(relaySum)/m.relays.size())>1e-12||!in(m.appliedField,-4,4))return false;
  for(double x:{diagnostics.waveEnergy,diagnostics.thermalIntegral,diagnostics.tracerIntegral,diagnostics.circuitStoredEnergy,diagnostics.maxE,diagnostics.maxB,diagnostics.discardedTime})if(!in(x,0,1e100))return false;
  return true;
}
std::vector<std::byte> Physics::serialize() const {
  require(validate(),"cannot serialize invalid physics state");Writer out;
  for(unsigned char c:std::array<unsigned char,8>{'S','F','P','H','Y','S','1',0})out.integer<std::uint8_t>(c);
  out.integer<std::uint32_t>(PHYSICS_VERSION);out.integer<std::uint32_t>(w);out.integer<std::uint32_t>(h);out.integer(seed_);out.integer(rng_);out.f64(time);out.integer(nextSourceId_);out.integer<std::uint32_t>(sources.size());out.integer<std::uint32_t>(density.size());
  for(const auto* a:{&density,&heat,&pressure,&velocity})for(float x:*a)out.f32(x);
  for(const auto& s:sources){out.integer(s.id);out.f32(s.x);out.f32(s.y);out.f64(s.q);out.f64(s.mx);out.f64(s.my);out.f32(s.core);out.f64(s.life);out.f64(s.initialLife);}
  const auto& c=diagnostics.circuit;for(double x:{c.i1,c.i2,c.q1,c.q2,c.soc,c.batteryEnergy,c.drivePhase,c.drive,c.harvestedEnergy,c.dissipatedEnergy})out.f64(x);
  for(auto r:diagnostics.memory.relays)out.integer<std::uint8_t>(std::uint8_t(r+1));
  out.f64(diagnostics.memory.magnetization);out.f64(diagnostics.memory.appliedField);
  out.f64(diagnostics.discardedTime);out.integer(diagnostics.steps);out.integer(diagnostics.injections);out.integer(diagnostics.limitedCells);return out.bytes;
}
void Physics::restore(std::span<const std::byte> data){
  require(data.size()>=56&&data.size()<=2*1024*1024,"invalid physics checkpoint size");Reader in{data};
  for(unsigned char c:std::array<unsigned char,8>{'S','F','P','H','Y','S','1',0})require(in.integer<std::uint8_t>()==c,"wrong physics checkpoint magic");
  require(in.integer<std::uint32_t>()==PHYSICS_VERSION,"unsupported physics version");
  const auto width=in.integer<std::uint32_t>(),height=in.integer<std::uint32_t>();require(width<=256&&height<=256,"oversized physics dimensions");dimensions(int(width),int(height));
  const auto seed=in.integer<std::uint64_t>(),rng=in.integer<std::uint64_t>();const double savedTime=in.f64();const auto next=in.integer<std::uint32_t>(),count=in.integer<std::uint32_t>(),cells=in.integer<std::uint32_t>();
  require(count<=MAX_SOURCES&&cells==width*height,"invalid physics array counts");
  Physics staged(int(width),int(height),seed);staged.rng_=rng;staged.time=savedTime;staged.nextSourceId_=next;staged.sources.clear();
  for(auto* a:{&staged.density,&staged.heat,&staged.pressure,&staged.velocity})for(float& x:*a)x=in.f32();
  for(std::size_t i=0;i<count;i++){Source s;s.id=in.integer<std::uint32_t>();s.x=in.f32();s.y=in.f32();s.q=in.f64();s.mx=in.f64();s.my=in.f64();s.core=in.f32();s.life=in.f64();s.initialLife=in.f64();staged.sources.push_back(s);}
  auto& c=staged.diagnostics.circuit;for(double* x:{&c.i1,&c.i2,&c.q1,&c.q2,&c.soc,&c.batteryEnergy,&c.drivePhase,&c.drive,&c.harvestedEnergy,&c.dissipatedEnergy})*x=in.f64();
  for(auto& r:staged.diagnostics.memory.relays){const auto encoded=in.integer<std::uint8_t>();require(encoded<=2,"invalid relay encoding");r=std::int8_t(encoded)-1;}
  staged.diagnostics.memory.magnetization=in.f64();staged.diagnostics.memory.appliedField=in.f64();staged.diagnostics.discardedTime=in.f64();staged.diagnostics.steps=in.integer<std::uint64_t>();staged.diagnostics.injections=in.integer<std::uint64_t>();staged.diagnostics.limitedCells=in.integer<std::uint64_t>();
  require(in.pos==data.size(),"trailing physics checkpoint bytes");require(staged.validate(),"invalid physics checkpoint values");staged.refreshFields();staged.refreshDiagnostics();require(staged.validate(),"invalid reconstructed physics fields");*this=std::move(staged);
}
} // namespace surface
