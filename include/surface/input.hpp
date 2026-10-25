#pragma once
#include <cmath>
#include <stdexcept>
namespace surface {
inline double gestureTravel(double dx,double dy,double previousSeparation,double separation){
 if(!std::isfinite(dx)||!std::isfinite(dy)||!std::isfinite(previousSeparation)||!std::isfinite(separation)||previousSeparation<0||separation<0)throw std::invalid_argument("invalid gesture sample");
 return std::hypot(dx,dy)+std::abs(separation-previousSeparation);
}
inline bool gestureIsTap(double travel,double seconds){return std::isfinite(travel)&&std::isfinite(seconds)&&travel>=0&&travel<.045&&seconds>=0&&seconds<.8;}
}
