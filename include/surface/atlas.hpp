#pragma once
#include <cstdint>
#include <span>
#include <vector>

namespace surface::atlas {
enum StarFlag : std::uint32_t { ColorPresent=1, ParallaxPresent=2, ParallaxErrorPresent=4 };
struct Star {
    std::uint64_t id{};
    double ra{}, dec{};                  // ICRS degrees, catalogue epoch.
    float mag{}, colorIndex{};           // Gaia G and BP-RP magnitudes.
    double parallaxMas{}, parallaxErrorMas{};
    std::uint32_t flags{};               // Absent measurements have zero storage + no flag.
};
struct Catalogue {
    std::vector<Star> stars;
    double epochJulianYear{};
};
struct Vec3 { double x{},y{},z{}; };
struct ProjectedStar {
    std::uint64_t id{};
    float x{},y{},depth{},mag{},colorIndex{};
    std::uint32_t flags{};
};
// Throws std::invalid_argument for malformed/oversized bytes; no native struct casts.
Catalogue loadCatalogue(std::span<const std::uint8_t> bytes);
Vec3 equatorialToCartesian(double raDeg,double decDeg,double distance=1.0);
// Yaw/pitch in radians. North up, increasing RA right. Unit-sphere orthographic
// projection. depth is camera direction cosine, never an inferred distance.
std::vector<ProjectedStar> projectStars(std::span<const Star> stars,double yaw,double pitch,
    double zoom,int width,int height,float maxMagnitude=99.0F);
} // namespace surface::atlas
