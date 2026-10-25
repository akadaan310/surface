#pragma once
#include "surface/physics.hpp"
#include "surface/renderer.hpp"
#include <cstddef>
#include <span>
#include <vector>
namespace surface {
struct Session {
    Physics physics;
    ViewState view;
    Session(int w=128,int h=160,std::uint64_t seed=0x51FACE):physics(w,h,seed){}
    FieldView fields()const;
    std::vector<std::byte> serialize()const;
    std::vector<std::byte> exportFile()const;
    void restore(std::span<const std::byte> bytes);
    void paint(float x,float y,float dx,float dy,float pressure=1);
    void step(double dt);
    void nextObservation();
};
const char* observationName(Observation);
}
