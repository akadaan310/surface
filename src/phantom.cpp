#include "surface/phantom.hpp"
#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <limits>
#include <stdexcept>

namespace surface::phantom {
namespace {
constexpr std::size_t numericLimit=65536;
[[noreturn]]void invalid(const char* message){throw std::invalid_argument(message);}
constexpr std::array<std::uint32_t,64> shaConstants{
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
unsigned typeBytes(NumericType type){
    switch(type){
        case NumericType::U8:case NumericType::I8:return 1;
        case NumericType::U16:case NumericType::I16:return 2;
        case NumericType::U32:case NumericType::I32:case NumericType::F32:return 4;
        case NumericType::F64:return 8;
    }
    invalid("unsupported numeric type");
}
void validEndian(Endian endian){if(endian!=Endian::Little&&endian!=Endian::Big)invalid("invalid byte order");}
void appendBits(std::vector<std::uint8_t>& out,std::uint64_t bits,unsigned count,Endian endian){
    for(unsigned i=0;i<count;i++)out.push_back(std::uint8_t(bits>>(8*(endian==Endian::Little?i:count-1-i))));
}
std::uint64_t readBits(std::span<const std::uint8_t> bytes,std::size_t at,unsigned count,Endian endian){
    if(at>bytes.size()||count>bytes.size()-at)invalid("truncated numeric bytes");
    std::uint64_t out=0;
    for(unsigned i=0;i<count;i++)out|=std::uint64_t(bytes[at+i])<<(8*(endian==Endian::Little?i:count-1-i));
    return out;
}
double interpreted(std::uint64_t bits,NumericType type){
    switch(type){
        case NumericType::U8:return std::uint8_t(bits);
        case NumericType::I8:return std::bit_cast<std::int8_t>(std::uint8_t(bits));
        case NumericType::U16:return std::uint16_t(bits);
        case NumericType::I16:return std::bit_cast<std::int16_t>(std::uint16_t(bits));
        case NumericType::U32:return std::uint32_t(bits);
        case NumericType::I32:return std::bit_cast<std::int32_t>(std::uint32_t(bits));
        case NumericType::F32:return std::bit_cast<float>(std::uint32_t(bits));
        case NumericType::F64:return std::bit_cast<double>(bits);
    }
    invalid("unsupported numeric type");
}
std::uint64_t represented(double value,NumericType type){
    if(!std::isfinite(value))invalid("finite numeric input required");
    if(type==NumericType::F64)return std::bit_cast<std::uint64_t>(value);
    if(type==NumericType::F32){
        if(std::abs(value)>std::numeric_limits<float>::max())invalid("float32 overflow");
        const float f=static_cast<float>(value);
        if(!std::isfinite(f))invalid("float32 overflow");
        return std::bit_cast<std::uint32_t>(f);
    }
    if(std::trunc(value)!=value)invalid("integer representation requires an integer");
    double low=0,high=0;
    switch(type){
        case NumericType::U8:high=255;break;
        case NumericType::I8:low=-128;high=127;break;
        case NumericType::U16:high=65535;break;
        case NumericType::I16:low=-32768;high=32767;break;
        case NumericType::U32:high=4294967295.;break;
        case NumericType::I32:low=-2147483648.;high=2147483647.;break;
        default:invalid("unsupported integer type");
    }
    if(value<low||value>high)invalid("integer outside representable range");
    return static_cast<std::uint64_t>(static_cast<std::int64_t>(value));
}
std::vector<double> readValues(std::span<const std::uint8_t> bytes,NumericType type,Endian endian){
    validEndian(endian);const unsigned stride=typeBytes(type);
    if(bytes.size()%stride||bytes.size()/stride>numericLimit)invalid("numeric array size outside budget");
    std::vector<double> out;out.reserve(bytes.size()/stride);
    for(std::size_t at=0;at<bytes.size();at+=stride){
        const double value=interpreted(readBits(bytes,at,stride,endian),type);
        if(!std::isfinite(value))invalid("nonfinite numeric payload");
        out.push_back(value);
    }
    return out;
}
bool exact(double a,double b){return a==b&&(a!=0||std::signbit(a)==std::signbit(b));}
void validateRecord(const NumericRecord& record){
    validEndian(record.endian);const auto stride=typeBytes(record.type);
    if(record.count>numericLimit||record.bytes.size()!=record.count*stride||record.sourceF64Little.size()!=record.count*8)
        invalid("numeric record count/size mismatch");
    if(record.sourceSha256.size()!=64||record.payloadSha256.size()!=64||sha256(record.bytes)!=record.payloadSha256||sha256(record.sourceF64Little)!=record.sourceSha256)
        invalid("numeric provenance digest mismatch");
    const auto source=readValues(record.sourceF64Little,NumericType::F64,Endian::Little);
    const auto rebuilt=encodeNumeric(source,record.type,record.endian,true);
    if(rebuilt.bytes!=record.bytes||rebuilt.changedValues!=record.changedValues||
       !exact(rebuilt.maximumAbsoluteError,record.maximumAbsoluteError)||rebuilt.signedZeroPreserved!=record.signedZeroPreserved)
        invalid("numeric conversion/loss declaration mismatch");
}
using Complex=std::complex<double>;
void validOrder(BasisOrder order){
    if(order!=BasisOrder::QubitZeroMostSignificant&&order!=BasisOrder::QubitZeroLeastSignificant)invalid("unknown basis order");
}
void validState(std::span<const Complex> amplitudes,unsigned qubits){
    if(qubits<1||qubits>6||amplitudes.size()!=(1U<<qubits))invalid("state dimensions outside budget");
    double norm=0;
    for(auto value:amplitudes){
        if(!std::isfinite(value.real())||!std::isfinite(value.imag()))invalid("nonfinite complex amplitude");
        norm+=std::norm(value);
    }
    if(!std::isfinite(norm)||std::abs(norm-1)>1e-10)invalid("normalized complex state required");
}
std::string stateDigest(const StateRecord& record){
    std::vector<std::uint8_t> bytes{'S','Q','S','T','A','T','E','1'};
    appendBits(bytes,record.qubits,4,Endian::Little);
    appendBits(bytes,record.basisOrder==BasisOrder::QubitZeroMostSignificant?0:1,4,Endian::Little);
    bytes.insert(bytes.end(),record.realImag.bytes.begin(),record.realImag.bytes.end());
    return sha256(bytes);
}
std::array<Complex,4> matrix(Gate gate,double theta){
    constexpr Complex one{1,0},zero{0,0},ii{0,1};
    const double s=std::sqrt(.5);
    switch(gate){
        case Gate::I:return {one,zero,zero,one};
        case Gate::X:return {zero,one,one,zero};
        case Gate::Y:return {zero,-ii,ii,zero};
        case Gate::Z:return {one,zero,zero,-one};
        case Gate::H:return {s,s,s,-s};
        case Gate::S:return {one,zero,zero,ii};
        case Gate::T:return {one,zero,zero,Complex{s,s}};
        case Gate::RX:case Gate::RZ:{
            if(!std::isfinite(theta))invalid("rotation angle must be finite");
            const double c=std::cos(theta/2),t=std::sin(theta/2);
            if(gate==Gate::RX)return {c,Complex{0,-t},Complex{0,-t},c};
            return {Complex{c,-t},zero,zero,Complex{c,t}};
        }
        default:invalid("unknown local gate");
    }
}
}

std::string sha256(std::span<const std::uint8_t> input){
    if(input.size()>16*1024*1024)invalid("SHA256 input exceeds bounded adapter budget");
    std::vector<std::uint8_t> data(input.begin(),input.end());
    data.push_back(0x80);while(data.size()%64!=56)data.push_back(0);
    appendBits(data,std::uint64_t(input.size())*8,8,Endian::Big);
    std::array<std::uint32_t,8> h{0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
    for(std::size_t offset=0;offset<data.size();offset+=64){
        std::array<std::uint32_t,64> w{};
        for(unsigned i=0;i<16;i++)w[i]=std::uint32_t(readBits(data,offset+i*4,4,Endian::Big));
        for(unsigned i=16;i<64;i++){
            const auto a=w[i-15],b=w[i-2];
            const auto s0=std::rotr(a,7)^std::rotr(a,18)^(a>>3),s1=std::rotr(b,17)^std::rotr(b,19)^(b>>10);
            w[i]=w[i-16]+s0+w[i-7]+s1;
        }
        auto a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],hh=h[7];
        for(unsigned i=0;i<64;i++){
            const auto s1=std::rotr(e,6)^std::rotr(e,11)^std::rotr(e,25),ch=(e&f)^(~e&g);
            const auto t1=hh+s1+ch+shaConstants[i]+w[i];
            const auto s0=std::rotr(a,2)^std::rotr(a,13)^std::rotr(a,22),maj=(a&b)^(a&c)^(b&c),t2=s0+maj;
            hh=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
        }
        h[0]+=a;h[1]+=b;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=hh;
    }
    constexpr char digits[]="0123456789abcdef";std::string out;out.reserve(64);
    for(auto v:h)for(int shift=28;shift>=0;shift-=4)out.push_back(digits[(v>>shift)&15]);
    return out;
}

NumericRecord encodeNumeric(std::span<const double> values,NumericType type,Endian endian,bool allowLoss){
    static_assert(sizeof(double)==8&&sizeof(float)==4&&std::numeric_limits<double>::is_iec559&&std::numeric_limits<float>::is_iec559);
    validEndian(endian);const auto stride=typeBytes(type);
    if(values.size()>numericLimit)invalid("numeric value budget exceeded");
    NumericRecord out;out.type=type;out.endian=endian;out.count=values.size();
    out.bytes.reserve(values.size()*stride);out.sourceF64Little.reserve(values.size()*8);
    for(double value:values){
        const auto bits=represented(value,type);appendBits(out.bytes,bits,stride,endian);
        appendBits(out.sourceF64Little,std::bit_cast<std::uint64_t>(value),8,Endian::Little);
        const double roundtrip=interpreted(bits,type);
        if(!exact(roundtrip,value)){
            if(!allowLoss)invalid("numeric representation would lose information");
            ++out.changedValues;out.maximumAbsoluteError=std::max(out.maximumAbsoluteError,std::abs(value-roundtrip));
        }
        if(value==0&&std::signbit(value)&&!std::signbit(roundtrip))out.signedZeroPreserved=false;
    }
    out.sourceSha256=sha256(out.sourceF64Little);out.payloadSha256=sha256(out.bytes);return out;
}
std::vector<double> decodeNumeric(const NumericRecord& record){validateRecord(record);return readValues(record.bytes,record.type,record.endian);}
std::vector<double> numericSource(const NumericRecord& record){validateRecord(record);return readValues(record.sourceF64Little,NumericType::F64,Endian::Little);}

WordTransition wordTransition(std::uint64_t before,unsigned width,WordOp operation,unsigned place,unsigned value,std::uint64_t operand){
    if(width<1||width>64)invalid("word width must be 1..64");
    const std::uint64_t mask=width==64?UINT64_MAX:(1ULL<<width)-1;
    if(before>mask)invalid("raw word outside width");
    if(operation!=WordOp::Add&&place>=width)invalid("place outside word");
    WordTransition out;out.width=width;out.operation=operation;out.before=before;
    if(operation==WordOp::Inject||operation==WordOp::Add){
        const std::uint64_t rhs=operation==WordOp::Inject?1ULL<<place:operand;
        if(rhs>mask)invalid("operand outside word");
        unsigned carry=0;out.trace.reserve(width);
        for(unsigned i=0;i<width;i++){
            const unsigned a=(before>>i)&1U,b=(rhs>>i)&1U,carryIn=carry,result=a^b^carry;
            carry=(a&b)|(a&carry)|(b&carry);out.after|=std::uint64_t(result)<<i;
            out.trace.push_back({i,a,b,carryIn,result,carry});
        }
        out.overflow=carry!=0;
    }else if(operation==WordOp::Invert||operation==WordOp::Assign){
        if(operation==WordOp::Assign&&value>1)invalid("assigned bit must be 0 or 1");
        const std::uint64_t bit=1ULL<<place;const unsigned prior=(before>>place)&1U,next=operation==WordOp::Invert?1U-prior:value;
        out.after=(before&~bit)|(std::uint64_t(next)<<place);out.trace.push_back({place,prior,0,0,next,0});
    }else invalid("unsupported word operation");
    for(unsigned i=0;i<width;i++)if(((before^out.after)>>i)&1U)out.changedPlaces.push_back(i);
    return out;
}

PulseRecord encodePulse(std::span<const std::uint8_t> bits,PulseMode mode,std::uint8_t initial){
    if(bits.size()>numericLimit||initial>1||(mode!=PulseMode::Presence&&mode!=PulseMode::Toggle))invalid("invalid bounded pulse input");
    PulseRecord out{mode,initial,{}};out.events.reserve(bits.size());auto previous=initial;
    for(auto bit:bits){if(bit>1)invalid("pulse alphabet must be 0/1");out.events.push_back(mode==PulseMode::Presence?bit:bit^previous);previous=bit;}
    return out;
}
std::vector<std::uint8_t> decodePulse(const PulseRecord& record){
    if(record.events.size()>numericLimit||record.initial>1||(record.mode!=PulseMode::Presence&&record.mode!=PulseMode::Toggle))invalid("invalid bounded pulse record");
    std::vector<std::uint8_t> bits;bits.reserve(record.events.size());auto previous=record.initial;
    for(auto event:record.events){if(event>1)invalid("pulse alphabet must be 0/1");const std::uint8_t bit=record.mode==PulseMode::Presence?event:event^previous;bits.push_back(bit);previous=bit;}
    return bits;
}

QuantumState simulateCircuit(unsigned qubits,std::span<const Operation> operations){
    if(qubits<1||qubits>6||operations.size()>256)invalid("bounded quantum reference supports 1..6 qubits and <=256 operations");
    QuantumState out;out.qubits=qubits;const std::size_t count=1U<<qubits;out.amplitudes.resize(count);out.amplitudes[0]=1.;
    for(const auto& op:operations){
        if(op.target>=qubits)invalid("target qubit outside state");
        const unsigned target=1U<<(qubits-1-op.target);
        if(op.gate==Gate::CX){
            if(op.control>=qubits||op.control==op.target)invalid("CNOT requires distinct in-range qubits");
            const unsigned control=1U<<(qubits-1-op.control);
            for(unsigned i=0;i<count;i++)if((i&control)&&!(i&target))std::swap(out.amplitudes[i],out.amplitudes[i|target]);
        }else{
            const auto u=matrix(op.gate,op.theta);
            for(unsigned i=0;i<count;i++)if(!(i&target)){
                const unsigned j=i|target;const auto a=out.amplitudes[i],b=out.amplitudes[j];
                out.amplitudes[i]=u[0]*a+u[1]*b;out.amplitudes[j]=u[2]*a+u[3]*b;
            }
        }
        double norm=0;for(const auto& amplitude:out.amplitudes)norm+=std::norm(amplitude);
        out.normError=std::abs(norm-1);
        if(!std::isfinite(norm)||out.normError>1e-10)invalid("quantum reference norm drift");
    }
    out.probabilities.reserve(count);for(const auto& amplitude:out.amplitudes)out.probabilities.push_back(std::norm(amplitude));
    return out;
}

StateRecord serializeState(std::span<const std::complex<double>> amplitudes,unsigned qubits,BasisOrder order){
    validOrder(order);validState(amplitudes,qubits);
    std::vector<double> components;components.reserve(amplitudes.size()*2);
    for(auto value:amplitudes){components.push_back(value.real());components.push_back(value.imag());}
    StateRecord out{qubits,order,encodeNumeric(components),{}};out.recordSha256=stateDigest(out);return out;
}
QuantumState deserializeState(const StateRecord& record){
    validOrder(record.basisOrder);
    if(record.qubits<1||record.qubits>6||record.realImag.type!=NumericType::F64||record.realImag.endian!=Endian::Little||
       record.realImag.count!=2U*(1U<<record.qubits))invalid("invalid complex representation");
    const auto components=decodeNumeric(record.realImag);
    if(record.recordSha256!=stateDigest(record))invalid("state/basis digest mismatch");
    QuantumState out;out.qubits=record.qubits;out.basisOrder=record.basisOrder;double norm=0;
    for(std::size_t i=0;i<components.size();i+=2){
        const Complex value{components[i],components[i+1]};out.amplitudes.push_back(value);
        out.probabilities.push_back(std::norm(value));norm+=std::norm(value);
    }
    validState(out.amplitudes,out.qubits);out.normError=std::abs(norm-1);return out;
}
std::vector<std::complex<double>> reorderQubits(std::span<const std::complex<double>> amplitudes,
    unsigned qubits,BasisOrder from,BasisOrder to){
    validOrder(from);validOrder(to);validState(amplitudes,qubits);
    std::vector<Complex> result(amplitudes.size());
    for(unsigned i=0;i<amplitudes.size();i++){
        unsigned j=i;
        if(from!=to){j=0;for(unsigned k=0;k<qubits;k++)j=(j<<1)|((i>>k)&1U);}
        result[j]=amplitudes[i];
    }
    return result;
}
double pureStateDistance(std::span<const std::complex<double>> left,std::span<const std::complex<double>> right){
    if(left.size()!=right.size()||left.size()<2||left.size()>64||(left.size()&(left.size()-1)))invalid("state dimensions differ");
    unsigned qubits=0;for(auto n=left.size();n>1;n>>=1)++qubits;
    validState(left,qubits);validState(right,qubits);Complex dot{};
    for(std::size_t i=0;i<left.size();i++)dot+=std::conj(left[i])*right[i];
    return std::acos(std::clamp(std::abs(dot),0.,1.));
}
} // namespace surface::phantom
