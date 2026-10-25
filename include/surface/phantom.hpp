#pragma once
#include <complex>
#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <vector>

namespace surface::phantom {
enum class Endian { Little, Big };
enum class NumericType { U8,I8,U16,I16,U32,I32,F32,F64 };
struct NumericRecord {
    NumericType type{NumericType::F64};
    Endian endian{Endian::Little};
    std::size_t count{};
    std::vector<std::uint8_t> bytes;
    std::vector<std::uint8_t> sourceF64Little; // Always retain original finite doubles.
    std::size_t changedValues{};
    double maximumAbsoluteError{};
    bool signedZeroPreserved{true};
    std::string sourceSha256, payloadSha256;
};
std::string sha256(std::span<const std::uint8_t> bytes);
NumericRecord encodeNumeric(std::span<const double> values,NumericType type=NumericType::F64,
    Endian endian=Endian::Little,bool allowLoss=false);
std::vector<double> decodeNumeric(const NumericRecord& record);
std::vector<double> numericSource(const NumericRecord& record);

enum class WordOp { Inject,Invert,Assign,Add };
struct WordStep { unsigned place{},a{},b{},carryIn{},result{},carryOut{}; };
struct WordTransition {
    unsigned width{};WordOp operation{};std::uint64_t before{},after{};
    bool overflow{};std::vector<unsigned> changedPlaces;std::vector<WordStep> trace;
};
// Finite unsigned 1..64-bit state, wrap overflow. INJECT is addition of 2^place;
// INVERT flips one bit. These are distinct PHANTOM operations.
WordTransition wordTransition(std::uint64_t before,unsigned width,WordOp operation,
    unsigned place=0,unsigned value=0,std::uint64_t operand=0);

enum class PulseMode { Presence,Toggle };
struct PulseRecord { PulseMode mode{};std::uint8_t initial{};std::vector<std::uint8_t> events; };
PulseRecord encodePulse(std::span<const std::uint8_t> bits,PulseMode mode=PulseMode::Presence,
    std::uint8_t initial=0);
std::vector<std::uint8_t> decodePulse(const PulseRecord& record);

enum class Gate { I,X,Y,Z,H,S,T,RX,RZ,CX };
enum class BasisOrder { QubitZeroMostSignificant,QubitZeroLeastSignificant };
struct Operation { Gate gate{Gate::I};unsigned target{};unsigned control{};double theta{}; };
struct QuantumState {
    unsigned qubits{};std::vector<std::complex<double>> amplitudes;
    std::vector<double> probabilities;double normError{};
    BasisOrder basisOrder{BasisOrder::QubitZeroMostSignificant};
};
// Classical, ideal state-vector reference, 1..6 qubits and <=256 operations.
// Starts in |00...0>; qubit zero is the most significant basis-index bit.
QuantumState simulateCircuit(unsigned qubits,std::span<const Operation> operations);
struct StateRecord {
    unsigned qubits{};BasisOrder basisOrder{};NumericRecord realImag;
    std::string recordSha256;
};
// Exact binary64 LE real/imaginary interleave. All amplitudes finite, 1..6 qubits,
// norm tolerance 1e-10. Declares basis order; serialized numbers are not hardware qubits.
StateRecord serializeState(std::span<const std::complex<double>> amplitudes,unsigned qubits,BasisOrder order);
QuantumState deserializeState(const StateRecord& record);
std::vector<std::complex<double>> reorderQubits(std::span<const std::complex<double>> amplitudes,
    unsigned qubits,BasisOrder from,BasisOrder to);
double pureStateDistance(std::span<const std::complex<double>> left,std::span<const std::complex<double>> right);
} // namespace surface::phantom
