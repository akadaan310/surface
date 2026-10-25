#include "surface/engine_service.hpp"
#include "surface/checkpoint.hpp"
#include <mutex>
#include <condition_variable>
#include <atomic>
#include <deque>
#include <chrono>
#include <algorithm>
#include <stdexcept>
namespace surface {
using Clock=std::chrono::steady_clock;
static std::int64_t tickNow(){return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now().time_since_epoch()).count();}
struct EngineService::State {
 enum class Kind {Paint,View,Barrier};
 struct Command {Kind kind;InkInput input{};ViewState view{};std::shared_ptr<std::promise<Session>> promise;};
 explicit State(Session s,std::filesystem::path d):latest(std::move(s)),directory(std::move(d)){}
 Session latest;std::filesystem::path directory;mutable std::mutex mutex;std::condition_variable condition;std::deque<Command> commands;
 std::atomic<bool> running{true},closing{false},finished{false},save{false},active{true};std::atomic<std::int64_t> heartbeat{tickNow()};
 std::uint64_t sequence=0;std::string failure;
};
EngineService::EngineService(Session initial,std::filesystem::path directory):state_(std::make_shared<State>(std::move(initial),std::move(directory))){
 const auto state=state_;
 worker_=std::thread([state]{
  try {
   Session work=state->latest;CheckpointStore store(state->directory);const auto lease=store.acquireLease();
   if(state->running.load()){
    const auto candidates=store.loadCandidates();if(!candidates.empty())work.view.generation=std::max(work.view.generation,candidates.front().generation);
   }
   auto lastSave=Clock::now();
   while(state->running.load()){
    const auto target=Clock::now()+std::chrono::milliseconds(33);std::deque<State::Command> commands;
    {std::lock_guard lock(state->mutex);commands.swap(state->commands);}
    for(auto& command:commands){
     if(!state->running.load()){if(command.promise)command.promise->set_exception(std::make_exception_ptr(std::runtime_error("worker publication revoked")));continue;}
     if(command.kind==State::Kind::Paint)work.paint(command.input.x,command.input.y,command.input.dx,command.input.dy,command.input.pressure);
     else if(command.kind==State::Kind::View){const auto gen=work.view.generation,input=work.view.inputSequence;work.view=command.view;work.view.generation=gen;work.view.inputSequence=input;}
     else command.promise->set_value(work);
    }
    if(!state->running.load())break;
    const bool stopping=state->closing.load();
    if(state->active.load()&&!stopping)work.step(1./30.);
    if(!state->running.load())break;
    {std::lock_guard lock(state->mutex);state->latest=work;++state->sequence;}
    state->heartbeat.store(tickNow());
    if(stopping||state->save.exchange(false)||Clock::now()-lastSave>std::chrono::seconds(5)){
     try {
      // Generation is local to this lease; a retired owner cannot adopt a newer owner's counter.
      if(state->running.load()){++work.view.generation;const auto bytes=work.serialize();if(state->running.load())store.saveOwned(bytes,work.view.generation,lease);}
      lastSave=Clock::now();
     }catch(const std::exception& e){std::lock_guard lock(state->mutex);state->failure=std::string("checkpoint: ")+e.what();lastSave=Clock::now();}
    }
    if(stopping)break;
    std::unique_lock lock(state->mutex);state->condition.wait_until(lock,target,[&]{return state->closing.load()||!state->running.load();});
   }
  }catch(const std::exception& e){std::lock_guard lock(state->mutex);state->failure=e.what();}
  {
   std::lock_guard lock(state->mutex);
   for(auto& command:state->commands)if(command.promise)command.promise->set_exception(std::make_exception_ptr(std::runtime_error("worker unavailable")));
   state->commands.clear();state->running.store(false);state->finished.store(true);
  }
  state->condition.notify_all();
 });
}
EngineService::~EngineService(){stop();}
bool EngineService::snapshot(Session& out,std::uint64_t& sequence){std::unique_lock lock(state_->mutex,std::try_to_lock);if(!lock||sequence==state_->sequence)return false;out=state_->latest;sequence=state_->sequence;return true;}
bool EngineService::inject(InkInput input){
 std::lock_guard lock(state_->mutex);if(state_->commands.size()>=256||!state_->running.load()||state_->closing.load())return false;state_->commands.push_back({State::Kind::Paint,input,{},{}});return true;
}
void EngineService::setView(ViewState view){
 view.validate();std::lock_guard lock(state_->mutex);if(!state_->running.load()||state_->closing.load())return;
 if(state_->commands.size()>=256)throw std::runtime_error("command budget exceeded");
 state_->commands.push_back({State::Kind::View,{},view,{}});
}
void EngineService::setActive(bool value){state_->active.store(value);}
void EngineService::requestCheckpoint(){state_->save.store(true);}
std::future<Session> EngineService::barrier(){
 auto promise=std::make_shared<std::promise<Session>>();auto future=promise->get_future();std::lock_guard lock(state_->mutex);
 if(!state_->running.load()||state_->closing.load()||state_->commands.size()>=256)promise->set_exception(std::make_exception_ptr(std::runtime_error("snapshot barrier unavailable")));
 else state_->commands.push_back({State::Kind::Barrier,{},{},promise});
 return future;
}
double EngineService::heartbeatAge()const{return (tickNow()-state_->heartbeat.load())/1e9;}
std::string EngineService::error()const{std::unique_lock lock(state_->mutex,std::try_to_lock);return lock?state_->failure:"";}
void EngineService::stop(){
 if(!worker_.joinable())return;
 state_->closing.store(true);state_->condition.notify_all();
 std::unique_lock lock(state_->mutex);state_->condition.wait_for(lock,std::chrono::milliseconds(1000),[&]{return state_->finished.load();});const bool done=state_->finished.load();
 if(!done){state_->running.store(false);state_->failure="graceful stop timed out; last committed generation retained";}lock.unlock();
 if(done)worker_.join();else worker_.detach(); // Shared state owns its memory; a new durable lease fences retired publication.
}
}
