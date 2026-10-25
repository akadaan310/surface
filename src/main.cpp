#include "surface/session.hpp"
#include "surface/acoustic.hpp"
#include "surface/atlas.hpp"
#include <algorithm>
#include <charconv>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <optional>
#include <span>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
using Clock=std::chrono::steady_clock;
struct Options {
    int width=720,height=1280,frames=120,mode=0;
    bool demo=false,modeSpecified=false;
    std::filesystem::path output="build/previews/surface.ppm",save,load,audio,report,atlas="data/gaia.bin";
};
int parseInt(std::string_view text,const char* name,int low,int high){
    int value=0;const auto result=std::from_chars(text.data(),text.data()+text.size(),value);
    if(result.ec!=std::errc{}||result.ptr!=text.data()+text.size()||value<low||value>high)
        throw std::invalid_argument(std::string(name)+" outside "+std::to_string(low)+".."+std::to_string(high));
    return value;
}
void usage(){
    std::cout<<"Surface native headless runner\n"
        "  --output image.ppm   CPU-rasterized P6 image (default build/previews/surface.ppm)\n"
        "  --width 720 --height 1280   Each 16..4096; total at most 4,194,304 pixels\n"
        "  --frames 120        Deterministic 1/60 s steps; 1..10000 frames\n"
        "  --mode 0..6         Coupled, magnetic, acoustic, thermal, electric, optical, cosmos\n"
        "  --demo              Inject a deterministic curved touch sequence; pan sky in cosmos\n"
        "  --save state.surface --load state.surface   Portable session bytes, max 10 MiB\n"
        "  --audio audio.wav   Three-second native modal acoustic reference, mono PCM16\n"
        "  --report run.json   Host timing, parameters and numerical diagnostics\n"
        "  --atlas data/gaia.bin   Local real Gaia DR3 source table for mode 6\n";
}
Options parse(int argc,char** argv){
    Options out;
    for(int i=1;i<argc;i++){
        const std::string_view key=argv[i];
        if(key=="--help"||key=="-h"){usage();std::exit(0);}
        if(key=="--demo"){out.demo=true;continue;}
        if(i+1==argc)throw std::invalid_argument("missing option value");
        const std::string_view value=argv[++i];
        if(key=="--width")out.width=parseInt(value,"width",16,4096);
        else if(key=="--height")out.height=parseInt(value,"height",16,4096);
        else if(key=="--frames")out.frames=parseInt(value,"frames",1,10000);
        else if(key=="--mode"){out.mode=parseInt(value,"mode",0,6);out.modeSpecified=true;}
        else if(key=="--output")out.output=value;
        else if(key=="--save")out.save=value;
        else if(key=="--load")out.load=value;
        else if(key=="--audio")out.audio=value;
        else if(key=="--report")out.report=value;
        else if(key=="--atlas")out.atlas=value;
        else throw std::invalid_argument("unknown argument: "+std::string(key));
    }
    if(std::uint64_t(out.width)*out.height>4194304)throw std::invalid_argument("framebuffer exceeds four-million-pixel budget");
    std::vector<std::filesystem::path> outputs;
    for(const auto& path:{out.output,out.save,out.audio,out.report})if(!path.empty()){
        const auto normalized=std::filesystem::absolute(path).lexically_normal();
        if(std::find(outputs.begin(),outputs.end(),normalized)!=outputs.end())throw std::invalid_argument("output paths must be distinct");
        outputs.push_back(normalized);
    }
    return out;
}
std::vector<std::uint8_t> readBounded(const std::filesystem::path& path,std::size_t limit){
    const auto size=std::filesystem::file_size(path);if(size>limit)throw std::invalid_argument("input file exceeds byte budget");
    std::ifstream stream(path,std::ios::binary);if(!stream)throw std::runtime_error("cannot open input file");
    std::vector<std::uint8_t> bytes(size);if(size&&!stream.read(reinterpret_cast<char*>(bytes.data()),std::streamsize(size)))throw std::runtime_error("input read failed");
    if(stream.peek()!=std::char_traits<char>::eof())throw std::runtime_error("input grew while being read");
    return bytes;
}
void parentDirectory(const std::filesystem::path& path){if(path.has_parent_path())std::filesystem::create_directories(path.parent_path());}
void saveBytes(const std::filesystem::path& path,std::span<const std::byte> bytes){
    if(bytes.size()>10*1024*1024)throw std::invalid_argument("save file exceeds 10 MiB");
    parentDirectory(path);auto temporary=path;temporary+=".writing";
    std::ofstream output(temporary,std::ios::binary|std::ios::trunc);
    if(!output)throw std::runtime_error("cannot create session file");
    output.write(reinterpret_cast<const char*>(bytes.data()),std::streamsize(bytes.size()));output.flush();
    if(!output)throw std::runtime_error("session write failed");
    output.close();std::filesystem::rename(temporary,path);
}
template<class S>auto exportSession(const S& session){
    if constexpr(requires {session.exportFile();})return session.exportFile();
    else return session.serialize();
}
std::string quote(std::string_view text){
    std::string result="\"";constexpr char hex[]="0123456789abcdef";
    for(unsigned char c:text){
        if(c=='"'||c=='\\'){result+='\\';result+=char(c);}
        else if(c<32){result+="\\u00";result+=hex[c>>4];result+=hex[c&15];}
        else result+=char(c);
    }
    return result+'"';
}
double percentile(const std::vector<double>& sorted,double fraction){
    const double index=(sorted.size()-1)*fraction;const auto lower=std::size_t(index),upper=std::min(lower+1,sorted.size()-1);
    return sorted[lower]+(sorted[upper]-sorted[lower])*(index-lower);
}
double milliseconds(Clock::duration duration){return std::chrono::duration<double,std::milli>(duration).count();}
}

int main(int argc,char** argv){
    try{
        const auto options=parse(argc,argv);const auto start=Clock::now();
        surface::Session session(128,160,0x51FACE);
        if(!options.load.empty()){
            const auto bytes=readBounded(options.load,10*1024*1024);
            session.restore(std::span(reinterpret_cast<const std::byte*>(bytes.data()),bytes.size()));
        }
        if(options.modeSpecified||options.load.empty())session.view.observation=static_cast<surface::Observation>(options.mode);
        session.view.validate();
        surface::Renderer renderer(options.width,options.height);
        surface::AcousticField acoustic;
        std::optional<surface::atlas::Catalogue> catalogue;
        if(session.view.observation==surface::Observation::Cosmos)catalogue=surface::atlas::loadCatalogue(readBounded(options.atlas,2*1024*1024));
        const double initialSimulationTime=session.physics.time;
        const std::uint64_t initialInputSequence=session.view.inputSequence;
        std::vector<double> times;times.reserve(options.frames);
        float lastX=.5f,lastY=.6f;
        for(int frame=0;frame<options.frames;frame++){
            const auto frameStart=Clock::now();
            if(catalogue){
                if(options.demo)session.view.yaw+=.0015;
                const auto points=surface::atlas::projectStars(catalogue->stars,session.view.yaw,session.view.pitch,session.view.zoom,options.width,options.height);
                std::vector<surface::SkyPoint> sky;sky.reserve(points.size());
                for(const auto& point:points)sky.push_back({point.x,point.y,point.mag,point.colorIndex,point.id});
                renderer.renderSky(sky);
            }else{
                if(options.demo){
                    constexpr double pi=3.14159265358979323846;
                    const double phase=2*pi*double(frame)/std::max(1,options.frames-1);
                    const float x=float(.5+.255*std::sin(phase)),y=float(.51+.275*std::sin(phase*.74+.35));
                    const float dx=frame?x-lastX:0,dy=frame?y-lastY:0;
                    session.paint(x,y,dx,dy,float(.75+.25*std::cos(phase*2)));
                    renderer.wake(x,y,.04f);lastX=x;lastY=y;
                    if(frame%24==0)acoustic.strike(x,y,.8);
                }
                session.step(1./60.);
                renderer.render(session.fields(),session.view,1./60.,!session.view.paused);
            }
            times.push_back(milliseconds(Clock::now()-frameStart));
        }
        parentDirectory(options.output);renderer.writePPM(options.output.string());
        if(!options.save.empty()){++session.view.generation;saveBytes(options.save,exportSession(session));}
        if(!options.audio.empty()){
            if(!options.demo||catalogue)acoustic.strike(.41,.58,1.);
            parentDirectory(options.audio);acoustic.writeWav(options.audio.string(),3.);
        }
        const double total=milliseconds(Clock::now()-start),sum=std::accumulate(times.begin(),times.end(),0.);
        std::sort(times.begin(),times.end());const auto& diagnostics=session.physics.diagnostics;
        std::ostringstream report;report<<std::setprecision(12);
        report<<"{\n  \"schema\": \"SURFACE-HEADLESS-RUN/1\",\n"
            <<"  \"renderer\": \"Surface original CPU rasterizer\",\n"
            <<"  \"execution\": \"native host headless; not Android device timing\",\n"
            <<"  \"width\": "<<options.width<<", \"height\": "<<options.height<<",\n"
            <<"  \"frames\": "<<options.frames<<", \"fixedStepSeconds\": "<<1./60.<<",\n"
            <<"  \"observation\": "<<quote(surface::observationName(session.view.observation))<<",\n"
            <<"  \"deterministicDemo\": "<<(options.demo?"true":"false")<<",\n"
            <<"  \"frameTimingMilliseconds\": {\"mean\": "<<sum/options.frames<<", \"p50\": "<<percentile(times,.5)
            <<", \"p95\": "<<percentile(times,.95)<<", \"maximum\": "<<times.back()<<", \"sum\": "<<sum<<"},\n"
            <<"  \"timingScope\": \"Injection + physics + render, or sky projection + render. Includes first-frame warmup. Excludes output I/O.\",\n"
            <<"  \"totalWallMilliseconds\": "<<total<<",\n"
            <<"  \"simulationTimeBefore\": "<<initialSimulationTime<<", \"simulationTimeAfter\": "<<session.physics.time<<",\n"
            <<"  \"inputSequenceBefore\": "<<initialInputSequence<<", \"inputSequenceAfter\": "<<session.view.inputSequence<<",\n"
            <<"  \"physicsGrid\": ["<<session.physics.w<<","<<session.physics.h<<"],\n"
            <<"  \"diagnostics\": {\"finiteValid\": "<<(session.physics.validate()?"true":"false")
            <<", \"waveEnergy\": "<<diagnostics.waveEnergy<<", \"thermalIntegral\": "<<diagnostics.thermalIntegral
            <<", \"maxE\": "<<diagnostics.maxE<<", \"maxB\": "<<diagnostics.maxB<<"},\n"
            <<"  \"catalogueSources\": "<<(catalogue?catalogue->stars.size():0)<<", \"projectedStars\": "<<renderer.stats().drawnStars<<",\n"
            <<"  \"output\": "<<quote(options.output.string())<<", \"savedSession\": "<<quote(options.save.string())
            <<", \"loadedSession\": "<<quote(options.load.string())<<", \"audio\": "<<quote(options.audio.string())<<"\n}\n";
        if(!options.report.empty()){
            parentDirectory(options.report);std::ofstream file(options.report);file<<report.str();if(!file)throw std::runtime_error("cannot write run report");
        }
        std::cout<<report.str();return 0;
    }catch(const std::exception& error){std::cerr<<"Surface: "<<error.what()<<'\n';return 2;}
}
