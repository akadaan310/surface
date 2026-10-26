#pragma once
// UNISON/0.1 read-only typed Quran scene carrier for future native SURFACE adapters.
// This header is NOT a native Arabic shaper, font engine or verified Android UI.
// Do not alter legacy renderer/session state or derive Qur'anic interpretation.

#include <cmath>
#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

namespace surface::quran {

enum class Evidence : std::uint8_t {
    Source, DefinedMathematically, Modeled, Observed, Unknown
};
enum class Layer : std::uint8_t {
    ExactArabicText, LetterSkeletonResearch, MuqattaatFrame,
    PronunciationDeferred, QittAddressResearch, AstronomicalObservation
};

struct SourceWord {
    std::uint32_t startByte=0, endByte=0;
    std::string rawUtf8;
    std::string nodeId;
    void validate(const std::string& source) const {
        if (endByte < startByte || endByte > source.size()
            || source.substr(startByte,endByte-startByte) != rawUtf8
            || nodeId.empty()) {
            throw std::invalid_argument("Quran source word span mismatch");
        }
    }
};

struct StarObservation {
    std::string catalogueId, coordinateFrame, epoch, source;
    double raDegrees=0, decDegrees=0;
    // Optional uncertainty and distance must have their OWN units and evidence.
    void validate() const {
        if (catalogueId.empty()||coordinateFrame.empty()||epoch.empty()||source.empty()
            ||!std::isfinite(raDegrees)||!std::isfinite(decDegrees)
            ||raDegrees<0||raDegrees>=360||decDegrees< -90||decDegrees>90)
            throw std::invalid_argument("Invalid astronomical observation");
    }
};

struct Scene {
    std::uint16_t surah=0, ayah=0;
    std::uint64_t generation=0, logicalTimeNs=0;
    std::string edition, rawUtf8, sourceSha256;
    std::vector<SourceWord> words;
    std::vector<StarObservation> optInStars;
    bool experimentalNumberOverlay=false;
    void validate() const {
        if (surah<1||surah>114||ayah<1||edition.empty()||rawUtf8.empty()
            ||rawUtf8.size()>100000||sourceSha256.size()!=64||words.size()>20000
            ||optInStars.size()>512)
            throw std::invalid_argument("Invalid Quran scene metadata or resource budget");
        for (const auto& word:words) word.validate(rawUtf8);
        for (const auto& star:optInStars) star.validate();
        // A loader MUST also verify SHA-256, UTF-8 scalar boundaries, corpus
        // provenance, read permissions, and the source scene schema independently.
    }
};

struct ShapedGlyphRun {
    // Backend shaping output, never the unshaped Arabic source bytes.
    std::string sourceWordId;
    std::vector<std::uint32_t> glyphIndices;
    std::vector<float> xPixels,yPixels;
    bool rtl=true;
    void validate() const {
        if (sourceWordId.empty()||glyphIndices.size()!=xPixels.size()
            ||glyphIndices.size()!=yPixels.size()||glyphIndices.size()>8192)
            throw std::invalid_argument("Invalid shaped glyph run");
        for (float x:xPixels) if (!std::isfinite(x))
            throw std::invalid_argument("Nonfinite glyph position");
        for (float y:yPixels) if (!std::isfinite(y))
            throw std::invalid_argument("Nonfinite glyph position");
    }
};

} // namespace surface::quran
