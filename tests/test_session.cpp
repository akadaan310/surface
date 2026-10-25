#include "surface/session.hpp"
#include "surface/checkpoint.hpp"
#include <cassert>
#include <cmath>
#include <filesystem>
#include <iostream>
#include <limits>
#include <unistd.h>
int main(){
 surface::Session first(32,32,719);first.paint(.4,.6,.01,0,1);for(int i=0;i<12;i++)first.step(1./30.);first.view.observation=surface::Observation::Magnetic;first.view.yaw=1.1;first.view.generation=3;
 const auto bytes=first.serialize();surface::Session resumed(16,16);resumed.restore(bytes);assert(resumed.serialize()==bytes);
 auto exported=first.exportFile();surface::Session imported;imported.restore(exported);assert(imported.serialize()==bytes);
 exported.back()^=std::byte(1);bool corrupt=false;try{imported.restore(exported);}catch(...){corrupt=true;}assert(corrupt);assert(imported.serialize()==bytes);
 first.step(1./30.);resumed.step(1./30.);assert(first.serialize()==resumed.serialize());
 const auto good=resumed.serialize();auto malformed=good;malformed[16]=std::byte(255);for(int i=17;i<24;i++)malformed[i]=std::byte(255);
 bool rejected=false;try{resumed.restore(malformed);}catch(...){rejected=true;}assert(rejected);assert(resumed.serialize()==good);
 const auto directory=std::filesystem::temp_directory_path()/("surface-session-"+std::to_string(getpid()));
 {surface::CheckpointStore store(directory);store.save(good,1);const auto loaded=store.load();assert(loaded&&loaded->generation==1);surface::Session cold;const auto raw=std::span<const std::byte>(reinterpret_cast<const std::byte*>(loaded->payload.data()),loaded->payload.size());cold.restore(raw);assert(cold.serialize()==good);}
 std::filesystem::remove_all(directory);
 std::cout<<"session: full bytes, exact continued evolution, atomic corrupt rejection and cold checkpoint replay passed\n";
}
