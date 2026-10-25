#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <vector>

namespace surface {
inline constexpr std::uint32_t PHYSICS_VERSION = 1;
struct Source {
  std::uint32_t id = 0;
  float x = 0, y = 0;              // normalized domain coordinates
  double q = 0, mx = 0, my = 0;   // coulomb, ampere square metre
  float core = .055f;              // regularization radius, metre
  double life = -1, initialLife = -1; // seconds; -1 = maintained source
};
struct FieldSample { double potential = 0, ex = 0, ey = 0, bx = 0, by = 0; };
struct CircuitState {
  double i1 = 0, i2 = 0, q1 = 0, q2 = 0;
  double soc = .34, batteryEnergy = 146.88, drivePhase = 0, drive = 2.5;
  double harvestedEnergy = 0, dissipatedEnergy = 0;
};
struct MagneticMemory {
  std::array<std::int8_t, 15> relays{};
  double magnetization = 0, appliedField = 0;
};
struct Diagnostics {
  double waveEnergy = 0, thermalIntegral = 0, tracerIntegral = 0;
  double circuitStoredEnergy = 0, maxE = 0, maxB = 0;
  double discardedTime = 0;
  std::uint64_t steps = 0, injections = 0, limitedCells = 0;
  CircuitState circuit;
  MagneticMemory memory;
};

// fieldAt uses metre coordinates for Source::x/y; Physics uses normalized x/y.
FieldSample fieldAt(std::span<const Source> sources, double xMetres, double yMetres);
void updateMagneticMemory(MagneticMemory& memory, double appliedField);
std::array<double, 3> cieXYZ(double wavelengthNm);
std::array<float, 3> wavelengthToLinearRGB(double wavelengthNm);
double faradayRotation(double verdetRadPerTeslaMetre, double bTesla, double lengthMetres);
double malusTransmission(double angleRadians);
double zeemanShiftHz(double bTesla, double landeG = 1, double deltaM = 1);

class Physics {
public:
  int w, h;
  double time = 0;
  std::vector<float> density, heat, pressure, velocity, potential, bx, by, ex, ey;
  std::vector<Source> sources;
  Diagnostics diagnostics;
  Physics(int width = 128, int height = 96, std::uint64_t seed = 0x51FACE);
  void inject(float x, float y, float dx = 0, float dy = 0, float strength = 1,
              float radius = .035f, const std::string& mode = "coupled");
  void step(double dt);
  void reset(std::uint64_t seed = 0x51FACE);
  bool validate() const;
  std::vector<std::byte> serialize() const;
  void restore(std::span<const std::byte> data);
private:
  std::uint64_t seed_ = 0, rng_ = 0;
  std::uint32_t nextSourceId_ = 0;
  std::vector<float> pressureNext_, heatNext_, densityDiff_, densityNext_;
  void allocate();
  void refreshFields();
  void refreshDiagnostics();
  void integrate(double dt);
  void integrateCircuit(double dt);
  double random();
};
} // namespace surface
