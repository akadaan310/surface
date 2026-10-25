#include "surface/engine_service.hpp"
#include "surface/checkpoint.hpp"
#include <cassert>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <thread>
#include <unistd.h>
using namespace surface;
using namespace std::chrono_literals;
int main(){
 auto root=std::filesystem::temp_directory_path()/("surface-engine-"+std::to_string(getpid()));std::filesystem::create_directories(root);
 Session initial(16,16);initial.view.paused=true;
 {
  EngineService engine(initial,root/"ordered");auto view=initial.view;view.observation=Observation::Thermal;engine.setView(view);assert(engine.inject({.4f,.6f,0,0,1}));view.observation=Observation::Cosmos;engine.setView(view);
  auto future=engine.barrier();assert(future.wait_for(2s)==std::future_status::ready);auto result=future.get();
  Session expected=initial;expected.view.observation=Observation::Thermal;expected.paint(.4f,.6f,0,0,1);expected.view.observation=Observation::Cosmos;
  assert(result.physics.heat==expected.physics.heat);assert(result.physics.pressure==expected.physics.pressure);assert(result.view.inputSequence==1);assert(result.view.observation==Observation::Cosmos);
  engine.stop();CheckpointStore store(root/"ordered");auto saved=store.load();assert(saved);Session cold;cold.restore(std::span<const std::byte>(reinterpret_cast<const std::byte*>(saved->payload.data()),saved->payload.size()));assert(cold.view.inputSequence==1);assert(cold.physics.heat==expected.physics.heat);
 }
 {
  const auto bad=root/"file";std::ofstream(bad)<<"not directory";EngineService engine(initial,bad);std::this_thread::sleep_for(100ms);assert(!engine.error().empty());engine.stop();
 }
 std::filesystem::remove_all(root);std::cout<<"engine: FIFO mode/paint ordering, acknowledged export, graceful final checkpoint and directory-failure isolation passed\n";
}
