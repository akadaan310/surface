#include "surface/engine_service.hpp"
#include "surface/checkpoint.hpp"
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <thread>
#include <fcntl.h>
#include <sys/file.h>
#include <sys/wait.h>
#include <unistd.h>

// Compile with physics.cpp, renderer.cpp, session.cpp, checkpoint.cpp,
// engine_service.cpp, -std=c++20 -pthread -Iinclude. Review-only repro.
int main(int argc,char** argv) {
  using namespace surface;
  using namespace std::chrono_literals;
  if(argc!=2) return 2;
  const auto directory=std::filesystem::temp_directory_path()/
    ("surface-engine-review-"+std::to_string(getpid()));
  std::filesystem::create_directories(directory);
  const std::string mode=argv[1];
  if(mode=="late-write") {
    CheckpointStore store(directory);
    const int lockfd=open((directory/"lock").c_str(),O_RDWR|O_CREAT,0600);
    if(lockfd<0||flock(lockfd,LOCK_EX)) return 3;
    Session initial(16,16); initial.view.paused=true;
    EngineService engine(initial,directory);
    engine.requestCheckpoint();
    // Deliberately block the old worker at store.load, then cancel it.
    std::this_thread::sleep_for(200ms);
    engine.stop();
    const bool before=std::filesystem::exists(directory/"slot0.bin");
    flock(lockfd,LOCK_UN); close(lockfd);
    std::this_thread::sleep_for(200ms);
    const auto after=store.load();
    std::cout<<"exists at stop="<<before<<" exists after stop="<<bool(after)<<"\n";
    std::filesystem::remove_all(directory);
    return !before&&after ? 1 : 0;
  }
  if(mode=="bad-directory") {
    const auto file=directory/"regular-file";
    {std::ofstream out(file); out<<"not a directory";}
    const pid_t child=fork();
    if(child==0) {
      EngineService engine(Session(16,16),file);
      std::this_thread::sleep_for(200ms);
      engine.stop();
      _exit(0);
    }
    int status=0; waitpid(child,&status,0);
    std::cout<<"child signaled="<<bool(WIFSIGNALED(status))
      <<" signal="<<(WIFSIGNALED(status)?WTERMSIG(status):0)<<"\n";
    std::filesystem::remove_all(directory);
    return WIFSIGNALED(status)?1:0;
  }
  return 2;
}
