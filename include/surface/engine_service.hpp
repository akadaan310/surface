#pragma once
#include "surface/session.hpp"
#include <memory>
#include <filesystem>
#include <thread>
#include <future>
namespace surface {
struct InkInput {float x=0,y=0,dx=0,dy=0,pressure=1;};
class EngineService {
public:
 EngineService(Session initial,std::filesystem::path checkpointDirectory);
 ~EngineService();
 EngineService(const EngineService&)=delete;
 EngineService& operator=(const EngineService&)=delete;
 bool snapshot(Session& destination,std::uint64_t& sequence);
 bool inject(InkInput);
 void setView(ViewState);
 void setActive(bool);
 void requestCheckpoint();
 std::future<Session> barrier();
 double heartbeatAge()const;
 std::string error()const;
 void stop();
private:
 struct State;
 std::shared_ptr<State> state_;
 std::thread worker_;
};
}
