#include "surface/input.hpp"
#include <cassert>
#include <iostream>
int main(){
 assert(surface::gestureIsTap(surface::gestureTravel(.001,.001,.2,.2),.3));
 assert(!surface::gestureIsTap(surface::gestureTravel(0,0,.2,.4),.3));
 assert(!surface::gestureIsTap(surface::gestureTravel(.1,0,.2,.2),.3));
 assert(!surface::gestureIsTap(0,.9));
 std::cout<<"input: stationary pinch and drag cannot become a tap; stationary short touch can\n";
}
