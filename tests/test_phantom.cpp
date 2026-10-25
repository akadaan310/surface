#include "surface/phantom.hpp"
#include <array>
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
void require(bool c,const char* m){if(!c)throw std::runtime_error(m);}
void near(double a,double b,double t=1e-12){require(std::abs(a-b)<t,"numerical fixture mismatch");}
template<class F>void rejects(F f){bool caught=false;try{f();}catch(const std::invalid_argument&){caught=true;}require(caught,"invalid input admitted");}
}
int main(){
    using namespace surface::phantom;
    const std::string abc="abc";
    require(sha256(std::span(reinterpret_cast<const std::uint8_t*>(abc.data()),abc.size()))=="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad","SHA256 independent known-answer fixture");
    require(sha256({})=="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","SHA256 empty fixture");
    const std::string blocks="abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq";
    require(sha256(std::span(reinterpret_cast<const std::uint8_t*>(blocks.data()),blocks.size()))=="248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1","SHA256 multi-block padding fixture");
    const std::array<double,2> signedValues{1,-2};
    auto le=encodeNumeric(signedValues,NumericType::I16,Endian::Little),be=encodeNumeric(signedValues,NumericType::I16,Endian::Big);
    require(le.bytes==std::vector<std::uint8_t>({1,0,254,255}),"little-endian bytes");
    require(be.bytes==std::vector<std::uint8_t>({0,1,255,254}),"big-endian bytes");
    const std::array<double,3> f64{-0.,1.,std::acos(-1.)};auto exact=encodeNumeric(f64);
    auto decoded=decodeNumeric(exact);require(std::signbit(decoded[0]),"negative zero lost");require(decoded[2]==f64[2],"binary64 roundtrip");
    auto broken=exact;broken.bytes[0]^=1;rejects([&]{decodeNumeric(broken);});
    broken=be;broken.endian=Endian::Little;rejects([&]{decodeNumeric(broken);});
    const std::array<double,1> third{1./3};rejects([&]{encodeNumeric(third,NumericType::F32);});
    auto quantized=encodeNumeric(third,NumericType::F32,Endian::Little,true);
    require(quantized.changedValues==1,"quantization unreported");require(numericSource(quantized)[0]==third[0],"source not retained");
    near(decodeNumeric(quantized)[0],double(float(third[0])));
    auto falseLoss=quantized;falseLoss.changedValues=0;rejects([&]{decodeNumeric(falseLoss);});
    for(double invalid:{std::numeric_limits<double>::quiet_NaN(),std::numeric_limits<double>::infinity()}){
        std::array<double,1> a{invalid};rejects([&]{encodeNumeric(a);});
    }
    for(double invalid:{256.,-1.,.5}){std::array<double,1>a{invalid};rejects([&]{encodeNumeric(a,NumericType::U8,Endian::Little,true);});}
    auto inject=wordTransition(7,8,WordOp::Inject),invert=wordTransition(7,8,WordOp::Invert);
    require(inject.after==8&&invert.after==6,"inject and invert conflated");
    require(inject.changedPlaces==std::vector<unsigned>({0,1,2,3}),"carry chain mismatch");
    require(wordTransition(255,8,WordOp::Inject).overflow,"wrap loss not declared");
    require(wordTransition(UINT64_MAX,64,WordOp::Inject).after==0,"64-bit boundary wrap");
    require(wordTransition(UINT64_MAX,64,WordOp::Inject).overflow,"64-bit carry missing");
    rejects([]{wordTransition(256,8,WordOp::Invert);});
    const std::array<std::uint8_t,6> bits{1,1,0,1,0,0};
    auto presence=encodePulse(bits),toggle=encodePulse(bits,PulseMode::Toggle);
    require(presence.events==std::vector<std::uint8_t>(bits.begin(),bits.end()),"presence mismatch");
    require(toggle.events==std::vector<std::uint8_t>({1,0,1,1,1,0}),"toggle fixture mismatch");
    require(decodePulse(toggle)==presence.events,"pulse replay mismatch");
    const std::array<Operation,2> bellOps{{{Gate::H,0},{Gate::CX,1,0}}};
    auto bell=simulateCircuit(2,bellOps);near(bell.probabilities[0],.5);near(bell.probabilities[1],0);near(bell.probabilities[2],0);near(bell.probabilities[3],.5);
    const std::array<Operation,3> interference{{{Gate::H,0},{Gate::Z,0},{Gate::H,0}}};
    near(simulateCircuit(1,interference).probabilities[1],1);
    const std::array<Operation,1> rotation{{{Gate::RX,0,0,std::acos(-1.)}}};near(simulateCircuit(1,rotation).probabilities[1],1);
    const std::array<Operation,1> invalidRotation{{{Gate::RX,0,0,std::numeric_limits<double>::quiet_NaN()}}};rejects([&]{simulateCircuit(1,invalidRotation);});
    const std::array<Operation,1> invalidControl{{{Gate::CX,0,0}}};rejects([&]{simulateCircuit(2,invalidControl);});
    const std::array<Operation,1> x0{{{Gate::X,0}}};auto msb=simulateCircuit(2,x0);
    near(msb.probabilities[2],1); // q0=1 is |10> in the inherited v0.1 convention.
    auto lsb=reorderQubits(msb.amplitudes,2,BasisOrder::QubitZeroMostSignificant,BasisOrder::QubitZeroLeastSignificant);
    near(std::norm(lsb[1]),1); // Explicit v3 convention conversion puts q0 at |01>.
    require(reorderQubits(lsb,2,BasisOrder::QubitZeroLeastSignificant,BasisOrder::QubitZeroMostSignificant)==msb.amplitudes,"basis conversion not reversible");
    auto stateRecord=serializeState(bell.amplitudes,2,BasisOrder::QubitZeroMostSignificant);
    require(deserializeState(stateRecord).amplitudes==bell.amplitudes,"complex binary roundtrip changed a bit");
    auto alteredOrder=stateRecord;alteredOrder.basisOrder=BasisOrder::QubitZeroLeastSignificant;rejects([&]{deserializeState(alteredOrder);});
    const std::array<std::complex<double>,2> basis{{{1,0},{0,0}}},phase{{{0,1},{0,0}}},orthogonal{{{0,0},{1,0}}};
    near(pureStateDistance(basis,phase),0);near(pureStateDistance(basis,orthogonal),std::acos(-1.)/2);
    const std::array<std::complex<double>,2> plus{{{std::sqrt(.5),0},{std::sqrt(.5),0}}},minus{{{std::sqrt(.5),0},{-std::sqrt(.5),0}}};
    near(pureStateDistance(plus,minus),std::acos(-1.)/2); // Equal probabilities can hide relative phase.
    rejects([]{simulateCircuit(7,{});});
    std::cout<<"phantom: SHA256, endian/signed-zero/loss records, finite admission, word carries, pulse semantics, Bell/interference passed\n";
}
