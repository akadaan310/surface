#include <iostream>
#if __has_include("surface/checkpoint.hpp")
#include "surface/checkpoint.hpp"
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <sys/wait.h>
#include <unistd.h>

static void check(bool condition, const char* message) { if (!condition) throw std::runtime_error(message); }
template<class F> static void rejected(F fn, const char* message) { bool caught=false; try { fn(); } catch (const std::exception&) { caught=true; } check(caught,message); }
template<class T> static void checkCandidates(T& store) {
  if constexpr(requires {store.loadCandidates();}) {
    const auto candidates=store.loadCandidates();
    check(candidates.size()==2 && candidates[0].generation==2 && candidates[1].generation==1,"semantic restore needs both envelope-valid candidates newest first");
    const auto good=std::find_if(candidates.begin(),candidates.end(),[](const auto& candidate){return candidate.payload==std::vector<std::uint8_t>{0,1,127,128,255};});
    check(good!=candidates.end() && good->generation==1,"caller can reject a CRC-valid invalid payload and restore older valid state");
  } else throw std::runtime_error("checkpoint candidates are required for semantic fallback");
}

template<class T> static void checkOwnerLeases(T& store,const std::filesystem::path& path) {
  const std::vector<std::uint8_t> oldPayload{1,2,3},newPayload{4,5,6};
  if constexpr(requires {store.acquireLease();store.saveOwned(oldPayload,1,1);}) {
    const auto oldOwner=store.acquireLease();
    check(oldOwner==1,"first durable owner epoch is one");
    store.saveOwned(oldPayload,1,oldOwner);
    const auto newOwner=store.acquireLease();
    check(newOwner==2,"replacement owner must advance durable lease");
    rejected([&]{store.saveOwned(oldPayload,1000000000,oldOwner);},"retired owner cannot bypass fence by choosing a larger generation");
    check(store.load()->generation==1 && store.load()->payload==oldPayload,"rejected old owner must leave prior slot intact");
    store.saveOwned(newPayload,2,newOwner);
    rejected([&]{store.save(oldPayload,3);},"plain save must not bypass an acquired owner lease");
    rejected([&]{store.saveOwned(oldPayload,3,0);},"zero owner token rejected");
    const auto readBytes=[](const std::filesystem::path& file){std::ifstream stream(file,std::ios::binary);return std::vector<std::uint8_t>((std::istreambuf_iterator<char>(stream)),{});};
    const auto lease=readBytes(path/"lease.bin"),slot0=readBytes(path/"slot0.bin"),slot1=readBytes(path/"slot1.bin");
    check(lease.size()==32 && lease[8]==1 && lease[12]==2 && lease[13]==0,"owner lease uses exact bounded LE header");
    {
      std::fstream file(path/"lease.bin",std::ios::in|std::ios::out|std::ios::binary);file.seekp(8);const char bad=2;file.write(&bad,1);
    }
    rejected([&]{(void)store.acquireLease();},"invalid owner lease cannot silently reset ownership");
    rejected([&]{store.saveOwned(oldPayload,1000000001,newOwner);},"invalid owner lease fails closed before publication");
    {
      auto corruptOwner=lease;corruptOwner[12]=static_cast<std::uint8_t>(oldOwner);
      std::ofstream file(path/"lease.bin",std::ios::binary|std::ios::trunc);file.write(reinterpret_cast<const char*>(corruptOwner.data()),corruptOwner.size());
    }
    rejected([&]{(void)store.acquireLease();},"owner-counter CRC corruption cannot revive an earlier lease");
    rejected([&]{store.saveOwned(oldPayload,1000000002,oldOwner);},"corrupt owner counter cannot authorize an old writer");
    std::filesystem::resize_file(path/"lease.bin",5);
    rejected([&]{(void)store.acquireLease();},"truncated owner lease cannot reset ownership");
    rejected([&]{store.saveOwned(oldPayload,1000000002,newOwner);},"truncated owner lease fails closed before publication");
    check(readBytes(path/"slot0.bin")==slot0 && readBytes(path/"slot1.bin")==slot1,"invalid lease must never overwrite either slot");
    {
      std::ofstream file(path/"lease.bin",std::ios::binary|std::ios::trunc);file.write(reinterpret_cast<const char*>(lease.data()),lease.size());
    }
    check(store.acquireLease()==3,"valid persisted owner counter advances on a new acquisition");
    rejected([&]{store.saveOwned(oldPayload,1000000003,newOwner);},"previous current owner becomes stale after new acquisition");
    store.saveOwned(newPayload,3,3);
    check(store.load()->generation==3,"current owner can still save correctly");
    T shared(path/"cross-process",1024);
    const auto token=shared.acquireLease();shared.saveOwned(oldPayload,1,token);
    const auto child=::fork();check(child>=0,"owner-fence fork succeeds");
    if(child==0) { try { T replacement(path/"cross-process",1024);const auto next=replacement.acquireLease();replacement.saveOwned(newPayload,2,next);_exit(0); } catch(...) {_exit(1);} }
    int status=0;check(::waitpid(child,&status,0)==child && WIFEXITED(status) && WEXITSTATUS(status)==0,"independent replacement acquires durable ownership");
    rejected([&]{shared.saveOwned(oldPayload,1000000004,token);},"old owner is fenced by an independent process acquisition");
    check(shared.load()->payload==newPayload,"new owner's committed state remains authoritative");
  } else throw std::runtime_error("durable owner lease fencing is required");
}

int main() {
  const auto path=std::filesystem::temp_directory_path()/("surface-checkpoint-test-"+std::to_string(getpid()));
  std::filesystem::remove_all(path);
  try {
    surface::CheckpointStore store(path,1024);
    surface::CheckpointStore owned(path/"owned",1024);checkOwnerLeases(owned,path/"owned");
    check(!store.load(),"new store has no checkpoint");
    const std::vector<std::uint8_t> a{0,1,127,128,255};
    store.save(a,1);
    auto first=store.load();
    check(first && first->generation==1 && first->payload==a,"full exact payload must round trip");
    {
      std::ifstream file(path/"slot0.bin",std::ios::binary);
      std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(file)),{});
      check(bytes.size()==37 && bytes[8]==1 && bytes[9]==0 && bytes[12]==1 && bytes[13]==0 && bytes[20]==5 && bytes[21]==0,"header must use exact little-endian integers");
      check(bytes[28]==166 && bytes[29]==173 && bytes[30]==26 && bytes[31]==26,"CRC32 must match independent zlib fixture");
    }
    {
      surface::CheckpointStore shared(path/"process",1024);
      shared.save(a,5);
      const auto child=::fork();
      check(child>=0,"fork must succeed for cross-process fence test");
      if(child==0) { try { surface::CheckpointStore other(path/"process",1024); other.save(a,7); _exit(0); } catch(...) { _exit(1); } }
      int status=0; check(::waitpid(child,&status,0)==child && WIFEXITED(status) && WEXITSTATUS(status)==0,"child commits a later generation");
      rejected([&]{shared.save(a,6);},"independent process writes must fence older generations");
      check(shared.load()->generation==7,"shared store must observe committed child generation");
    }
    rejected([&]{store.save(a,1);},"equal generation must be fenced");
    rejected([&]{store.save(a,0);},"older generation must be fenced");
    const std::vector<std::uint8_t> b{9,8,7,6,5};
    store.save(b,2);
    check(store.load()->payload==b,"newest valid generation loads");
    checkCandidates(store);
    {
      std::fstream file(path/"slot1.bin",std::ios::in|std::ios::out|std::ios::binary);
      file.seekp(-1,std::ios::end); const char changed='!'; file.write(&changed,1);
    }
    check(store.load()->generation==1,"corrupt latest payload falls back to previous slot");
    store.save(b,3);
    check(store.load()->generation==3,"new commit replaces corrupt slot");
    std::filesystem::resize_file(path/"slot1.bin",12);
    check(store.load()->generation==1,"truncated header falls back to previous slot");
    rejected([&]{store.save(std::vector<std::uint8_t>(1025),4);},"oversize writes rejected");
    {
      std::fstream file(path/"slot0.bin",std::ios::in|std::ios::out|std::ios::binary);
      file.seekp(8); const char unsupported=2; file.write(&unsupported,1);
    }
    rejected([&]{(void)store.load();},"two corrupt slots do not silently look like an empty store");
    std::filesystem::remove_all(path);
    std::cout<<"checkpoint: exact LE bytes, CRC, size/version, two-slot and semantic fallback, cross-process generation and owner-lease fencing passed\n";
    return 0;
  } catch (const std::exception& error) { std::filesystem::remove_all(path); std::cerr<<error.what()<<'\n'; return 1; }
}
#else
int main() { std::cerr<<"checkpoint store behavior is not implemented\n"; return 1; }
#endif
