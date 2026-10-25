#include "surface/renderer.hpp"
#include "surface/physics.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <limits>
#include <stdexcept>

namespace surface {
namespace {
constexpr float pi=3.14159265358979323846f;
float unit(float x){return std::clamp(x,0.f,1.f);}
Color mix(Color a,Color b,float t){return {a.r+(b.r-a.r)*t,a.g+(b.g-a.g)*t,a.b+(b.b-a.b)*t};}
Color scale(Color a,float s){return {a.r*s,a.g*s,a.b*s};}
Color plus(Color a,Color b){return {a.r+b.r,a.g+b.g,a.b+b.b};}
bool finite(Color c){return std::isfinite(c.r)&&std::isfinite(c.g)&&std::isfinite(c.b);}
float fieldSample(std::span<const float> f,int w,int h,float x,float y){
    const float fx=unit(x)*(w-1),fy=unit(y)*(h-1);const int ix=int(fx),iy=int(fy),jx=std::min(w-1,ix+1),jy=std::min(h-1,iy+1);const float tx=fx-ix,ty=fy-iy;
    return ((1-tx)*f[iy*w+ix]+tx*f[iy*w+jx])*(1-ty)+((1-tx)*f[jy*w+ix]+tx*f[jy*w+jx])*ty;
}
}

void ViewState::validate()const{
    if(static_cast<std::uint32_t>(observation)>6||!std::isfinite(yaw)||!std::isfinite(pitch)||!std::isfinite(zoom)||std::abs(yaw)>1e6||std::abs(pitch)>pi/2||zoom<.5||zoom>7)throw std::invalid_argument("invalid view state");
}
void FieldView::validate()const{
    if(width<2||height<2||width>512||height>512||!std::isfinite(time)||time<0)throw std::invalid_argument("invalid field dimensions/time");
    const auto n=std::size_t(width)*height;
    for(auto f:{density,heat,pressure,potential,bx,by,ex,ey}){if(f.size()!=n)throw std::invalid_argument("field dimension mismatch");for(float v:f)if(!std::isfinite(v))throw std::invalid_argument("nonfinite render field");}
}
float Renderer::sample(std::span<const float> f,int w,int h,float x,float y){
    if(w<2||h<2||w>512||h>512||f.size()!=std::size_t(w)*h||!std::isfinite(x)||!std::isfinite(y))throw std::invalid_argument("invalid sampling domain");
    return fieldSample(f,w,h,x,y);
}
Color Renderer::spectralColor(double wavelength){
    if(!std::isfinite(wavelength)||wavelength<360||wavelength>830)throw std::invalid_argument("wavelength outside observer range");
    // Official CIE 1931 2-degree observer, pinned 1 nm table; explicit sRGB gamut clipping.
    const auto color=wavelengthToLinearRGB(wavelength);return {color[0],color[1],color[2]};
}
Renderer::Renderer(int w,int h,std::size_t count){
    if(count<1||count>30000)throw std::invalid_argument("tracer budget exceeded");
    tracers_.resize(count);for(auto& t:tracers_)spawn(t);
    for(std::size_t i=0;i<colors_.size();i++)colors_[i]=spectralColor(450+200.*i/(colors_.size()-1));
    for(std::size_t i=0;i<displayLut_.size();i++){
        const float linear=1-std::exp(-float(i)/(displayLut_.size()-1)*6.f);
        const float s=linear<=.0031308f?12.92f*linear:1.055f*std::pow(linear,1/2.4f)-.055f;
        displayLut_[i]=std::uint8_t(std::lround(unit(s)*255));
    }
    resize(w,h);
}
void Renderer::resize(int w,int h){
    if(w<16||h<16||w>4096||h>4096||std::size_t(w)*h>4194304)throw std::invalid_argument("framebuffer budget exceeded");
    width_=w;height_=h;ink_.assign(std::size_t(w)*h,{});rgba_.assign(std::size_t(w)*h,0xff090502);warmed_=false;
}
void Renderer::clear(){std::fill(ink_.begin(),ink_.end(),Color{});std::fill(rgba_.begin(),rgba_.end(),0xff090502);warmed_=false;}
float Renderer::random(){auto x=randomState_;x^=x<<13;x^=x>>17;x^=x<<5;randomState_=x;return float(x)/4294967296.f;}
void Renderer::spawn(Tracer& t,const FieldView* f){
    float x=.02f+random()*.96f,y=.02f+random()*.96f;
    if(f&&random()<.82f){for(int k=0;k<7;k++){float xx=.02f+random()*.96f,yy=.02f+random()*.96f;if(random()<std::min(.88f,fieldSample(f->density,f->width,f->height,xx,yy)*2)){x=xx;y=yy;break;}}}
    t={x,y,0,1.8f+random()*5.5f,random()<.5f?-1.f:1.f,random()};
}
void Renderer::wake(float x,float y,float radius){
    if(!std::isfinite(x)||!std::isfinite(y)||!std::isfinite(radius)||radius<=0||radius>.5)throw std::invalid_argument("invalid brush");
    for(int j=0;j<180;j++){auto& t=tracers_[(wakeIndex_++)%tracers_.size()];spawn(t);const float a=random()*2*pi,r=std::sqrt(random())*radius;t.x=unit(x+std::cos(a)*r);t.y=unit(y+std::sin(a)*r);}
}
void Renderer::add(int x,int y,Color c,float coverage){
    if(x<0||y<0||x>=width_||y>=height_||coverage<=0)return;
    auto& p=ink_[std::size_t(y)*width_+x];p.r=std::min(8.f,p.r+c.r*coverage);p.g=std::min(8.f,p.g+c.g*coverage);p.b=std::min(8.f,p.b+c.b*coverage);
}
void Renderer::line(float x0,float y0,float x1,float y1,Color c){
    if(!std::isfinite(x0)||!std::isfinite(y0)||!std::isfinite(x1)||!std::isfinite(y1)||!finite(c))throw std::invalid_argument("nonfinite line");
    // Liang-Barsky clipping bounds work even when a source is far offscreen.
    float t0=0,t1=1,dx=x1-x0,dy=y1-y0;
    if(!std::isfinite(dx)||!std::isfinite(dy))return;
    auto clip=[&](float p,float q){if(p==0)return q>=0;const float t=q/p;if(p<0){if(t>t1)return false;t0=std::max(t0,t);}else{if(t<t0)return false;t1=std::min(t1,t);}return true;};
    if(!clip(-dx,x0)||!clip(dx,width_-1-x0)||!clip(-dy,y0)||!clip(dy,height_-1-y0))return;
    const float ax=x0+t0*dx,ay=y0+t0*dy,bx=x0+t1*dx,by=y0+t1*dy;dx=bx-ax;dy=by-ay;
    const int steps=std::max(1,int(std::ceil(std::max(std::abs(dx),std::abs(dy)))));
    const float energy=std::min(1.f,std::hypot(dx,dy)/steps);
    for(int i=0;i<=steps;i++){
        const float t=float(i)/steps,x=ax+dx*t,y=ay+dy*t;const int ix=int(std::floor(x)),iy=int(std::floor(y));const float fx=x-ix,fy=y-iy;
        const float endpoint=(i==0||i==steps)?.5f:1.f;
        add(ix,iy,c,(1-fx)*(1-fy)*energy*endpoint);add(ix+1,iy,c,fx*(1-fy)*energy*endpoint);add(ix,iy+1,c,(1-fx)*fy*energy*endpoint);add(ix+1,iy+1,c,fx*fy*energy*endpoint);
    }
}
void Renderer::splat(float x,float y,float radius,Color c){
    if(!std::isfinite(x)||!std::isfinite(y)||!std::isfinite(radius)||!finite(c)||radius<0||radius>256)throw std::invalid_argument("invalid splat");
    if(x+radius<0||y+radius<0||x-radius>width_||y-radius>height_)return;
    const int l=std::max(0,int(std::floor(x-radius))),r=std::min(width_-1,int(std::ceil(x+radius))),t=std::max(0,int(std::floor(y-radius))),b=std::min(height_-1,int(std::ceil(y+radius)));
    const float rr=std::max(.1f,radius*radius);
    for(int yy=t;yy<=b;yy++)for(int xx=l;xx<=r;xx++){const float d=((xx-x)*(xx-x)+(yy-y)*(yy-y))/rr;add(xx,yy,c,std::exp(-d*5));}
}
void Renderer::trace(const FieldView& f,Observation mode,double delta){
    const float dt=float(delta),aspect=float(width_)/height_;auto sample=[&](std::span<const float> a,float x,float y){return fieldSample(a,f.width,f.height,x,y);};
    for(auto& t:tracers_){
        t.age+=dt;if(t.age>t.life||t.x<.012f||t.x>.988f||t.y<.012f||t.y>.988f)spawn(t,&f);
        const float x=t.x,y=t.y,bx=sample(f.bx,x,y),by=sample(f.by,x,y),ex=sample(f.ex,x,y),ey=sample(f.ey,x,y);
        const float bn=std::hypot(bx,by)+1e-15f,en=std::hypot(ex,ey)+1e-12f;
        float vx=bx/bn,vy=by/bn;
        const float density=sample(f.density,x,y),heat=sample(f.heat,x,y),pressure=sample(f.pressure,x,y),potential=sample(f.potential,x,y);
        if(mode==Observation::Electric){vx=ex/en;vy=ey/en;}
        else if(mode==Observation::Acoustic){const float gx=sample(f.pressure,x+1.f/f.width,y)-sample(f.pressure,x-1.f/f.width,y),gy=sample(f.pressure,x,y+1.f/f.height)-sample(f.pressure,x,y-1.f/f.height);const float g=std::hypot(gx,gy)+1e-8f;vx=-gy/g;vy=gx/g;}
        else if(mode!=Observation::Magnetic){vx=.84f*vx-.16f*ey/en;vy=.84f*vy+.16f*ex/en;}
        const float speed=(.045f+.025f*t.variation)*t.direction;
        t.x+=vx*speed*dt;t.y+=vy*speed*dt*aspect;
        const float fade=std::sin(pi*unit(t.age/t.life));
        const float strength=(.07f+std::min(1.f,density)*.72f+std::min(.25f,std::abs(pressure)))*fade;
        int index=potential<0?int(14+t.variation*18):int(95+t.variation*20);
        if(mode==Observation::Thermal)index=int(100+unit(heat/80)*27);
        if(mode==Observation::Acoustic)index=pressure>0?104:24;
        line(x*(width_-1),y*(height_-1),t.x*(width_-1),t.y*(height_-1),scale(colors_[std::clamp(index,0,127)],strength*.48f));
    }
    stats_.fieldSamples+=tracers_.size()*8;
}
std::uint32_t Renderer::encode(Color c)const{
    auto enc=[&](float f){return displayLut_[std::size_t(std::clamp(f,0.f,6.f)*(displayLut_.size()-1)/6)];};
    return 0xff000000u|std::uint32_t(enc(c.b))<<16|std::uint32_t(enc(c.g))<<8|enc(c.r);
}
void Renderer::shade(const FieldView& f,Observation mode,double delta){
    const float decay=std::exp(-float(delta)*.46f);const Color cold=spectralColor(484),warm=spectralColor(610),violet=spectralColor(447);
    for(int y=0;y<height_;y++){
        const float ny=float(y)/(height_-1),fy=ny*(f.height-1);const int iy=int(fy),jy=std::min(f.height-1,iy+1);const float ty=fy-iy;
        for(int x=0;x<width_;x++){
            const float nx=float(x)/(width_-1),fx=nx*(f.width-1);const int ix=int(fx),jx=std::min(f.width-1,ix+1);const float tx=fx-ix;
            auto at=[&](std::span<const float> a){return ((1-tx)*a[iy*f.width+ix]+tx*a[iy*f.width+jx])*(1-ty)+((1-tx)*a[jy*f.width+ix]+tx*a[jy*f.width+jx])*ty;};
            const float d=std::max(0.f,at(f.density)),h=std::max(0.f,at(f.heat))/35,pressure=at(f.pressure),potential=at(f.potential)/30;
            const float dn=d/(.7f+d),hn=h/(1+h),pn=potential/(1+std::abs(potential));
            Color spectrum=mix(cold,warm,unit(.5f+.65f*pn));
            Color glow=plus(scale(spectrum,dn*dn*.105f),scale(warm,hn*hn*.07f));
            glow=plus(glow,scale(pressure>=0?cold:violet,std::min(.2f,std::abs(pressure))*.08f));
            float pathGain=1;
            if(mode==Observation::Acoustic){glow=scale(pressure>0?cold:violet,std::abs(pressure)*.45f);pathGain=.24f;}
            if(mode==Observation::Thermal){glow=scale(mix(warm,{1,.78f,.4f},hn),std::sqrt(hn)*.3f);pathGain=.32f;}
            if(mode==Observation::Electric){glow=scale(spectrum,std::abs(pn)*.1f);pathGain=1.1f;}
            if(mode==Observation::Optical){
                // Explicit synthetic magneto-optical slab: V(lambda)=500*(550/lambda)^2 rad/(T m), L=.3 m, beta=1.35 rad.
                const float b=at(f.by);const float tc=std::pow(std::cos(1.35f-500.f*std::pow(550.f/484.f,2.f)*b*.3f),2.f),tw=std::pow(std::cos(1.35f-500.f*std::pow(550.f/610.f,2.f)*b*.3f),2.f);
                glow=plus(scale(cold,tc*dn*1.4f),scale(warm,tw*dn*1.4f));pathGain=.7f;
            }
            auto& ink=ink_[std::size_t(y)*width_+x];ink=scale(ink,decay);
            Color radiance=plus(scale(ink,pathGain*1.6f),glow);
            const float vignette=1-.3f*((nx-.5f)*(nx-.5f)+(ny-.5f)*(ny-.5f));radiance=scale(radiance,vignette);
            radiance=plus(radiance,{.0008f,.0022f,.0031f});rgba_[std::size_t(y)*width_+x]=encode(radiance);
        }
    }
}
void Renderer::render(const FieldView& f,const ViewState& view,double dt,bool advance){
    const auto start=std::chrono::steady_clock::now();view.validate();f.validate();
    if(!std::isfinite(dt)||dt<0||dt>1)throw std::invalid_argument("invalid display delta");
    if(view.observation!=previous_){clear();previous_=view.observation;}
    const double step=std::clamp(dt,.001,.05);
    if(!warmed_){for(int i=0;i<24;i++)trace(f,view.observation,.045);warmed_=true;}
    else if(advance)trace(f,view.observation,step);
    shade(f,view.observation,advance?step:0);
    ++stats_.frames;stats_.frameMilliseconds=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
}
void Renderer::renderSky(std::span<const SkyPoint> stars){
    const auto start=std::chrono::steady_clock::now();std::fill(ink_.begin(),ink_.end(),Color{});
    for(const auto& s:stars){
        if(!std::isfinite(s.x)||!std::isfinite(s.y)||!std::isfinite(s.magnitude)||!std::isfinite(s.colorIndex))continue;
        const float t=unit((s.colorIndex+.25f)/3),brightness=std::pow(10.f,-.3f*(s.magnitude-1.7f));
        // Gaia BP-RP to display tint is a declared descriptive mapping, not measured stellar spectral radiance.
        const Color color{.65f+.35f*t,.82f-.28f*t,1-.6f*t};
        const float radius=1.3f+brightness*8;
        splat(float(s.x),float(s.y),radius,scale(color,.3f+brightness*2));
        if(brightness>.4f){line(float(s.x-radius),float(s.y),float(s.x+radius),float(s.y),scale(color,brightness*.1f));line(float(s.x),float(s.y-radius),float(s.x),float(s.y+radius),scale(color,brightness*.1f));}
    }
    for(std::size_t i=0;i<ink_.size();i++)rgba_[i]=encode(plus(ink_[i],{.0004f,.0007f,.0013f}));
    stats_.drawnStars=stars.size();++stats_.frames;stats_.frameMilliseconds=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
}
void Renderer::writePPM(const std::string& path)const{
    std::ofstream out(path,std::ios::binary);if(!out)throw std::runtime_error("cannot write image");out<<"P6\n"<<width_<<' '<<height_<<"\n255\n";
    for(auto p:rgba_){const char rgb[]={char(p&255),char((p>>8)&255),char((p>>16)&255)};out.write(rgb,3);}if(!out)throw std::runtime_error("image write failed");
}
}
