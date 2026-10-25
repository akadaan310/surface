#include "surface/checkpoint.hpp"
#include <algorithm>
#include <array>
#include <cerrno>
#include <cstring>
#include <fcntl.h>
#include <limits>
#include <stdexcept>
#include <string>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>

namespace surface {
namespace {
constexpr std::size_t headerSize = 32;
constexpr std::array<std::uint8_t,8> magic{'S','U','R','F','C','H','K',0};
constexpr std::array<std::uint8_t,8> leaseMagic{'S','U','R','F','O','W','N',0};
[[noreturn]] void ioError(const char* action) { throw std::runtime_error(std::string(action)+": "+std::strerror(errno)); }

struct Descriptor {
  int value{-1};
  explicit Descriptor(int fd):value(fd) { if(value<0) ioError("checkpoint open"); }
  ~Descriptor() { if(value>=0) ::close(value); }
  Descriptor(const Descriptor&) = delete;
  Descriptor& operator=(const Descriptor&) = delete;
};
struct Lock {
  Descriptor fd;
  explicit Lock(const std::filesystem::path& directory):fd(::open((directory/"lock").c_str(),O_CREAT|O_RDWR|O_CLOEXEC,0600)) {
    while(::flock(fd.value,LOCK_EX)<0) { if(errno!=EINTR) ioError("checkpoint lock"); }
  }
  ~Lock() { (void)::flock(fd.value,LOCK_UN); }
};

void appendLE(std::vector<std::uint8_t>& out,std::uint64_t value,unsigned count) { for(unsigned i=0;i<count;i++) out.push_back(static_cast<std::uint8_t>(value>>(8*i))); }
std::uint64_t readLE(std::span<const std::uint8_t> data,std::size_t offset,unsigned count) { std::uint64_t result=0; for(unsigned i=0;i<count;i++) result|=std::uint64_t(data[offset+i])<<(8*i); return result; }
std::uint32_t crc32(std::span<const std::uint8_t> data) {
  std::uint32_t crc=0xffffffffu;
  for(std::size_t i=0;i<data.size();++i) {
    if(i>=28 && i<32) continue; // Stored checksum is outside its own preimage.
    crc^=data[i];
    for(unsigned bit=0;bit<8;bit++) crc=(crc>>1)^(0xedb88320u&std::uint32_t(0-int(crc&1u)));
  }
  return ~crc;
}

struct Slot { bool exists=false; std::optional<CheckpointRecord> record; };
Slot readSlot(const std::filesystem::path& path,std::size_t limit) {
  int raw=::open(path.c_str(),O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
  if(raw<0) { if(errno==ENOENT) return {}; if(errno==ELOOP) return {true,{}}; ioError("checkpoint read open"); }
  Descriptor fd(raw); struct stat info{};
  if(::fstat(fd.value,&info)<0) ioError("checkpoint stat");
  if(!S_ISREG(info.st_mode) || info.st_size<static_cast<off_t>(headerSize) || static_cast<std::uint64_t>(info.st_size)>limit+headerSize) return {true,{}};
  std::vector<std::uint8_t> data(static_cast<std::size_t>(info.st_size)); std::size_t offset=0;
  while(offset<data.size()) { const auto n=::read(fd.value,data.data()+offset,data.size()-offset); if(n<0) { if(errno==EINTR) continue; ioError("checkpoint read"); } if(n==0) return {true,{}}; offset+=static_cast<std::size_t>(n); }
  if(!std::equal(magic.begin(),magic.end(),data.begin()) || readLE(data,8,4)!=1) return {true,{}};
  const auto generation=readLE(data,12,8), length=readLE(data,20,8);
  if(generation==0 || length>limit || length!=data.size()-headerSize || readLE(data,28,4)!=crc32(data)) return {true,{}};
  return {true,CheckpointRecord{generation,std::vector<std::uint8_t>(data.begin()+headerSize,data.end())}};
}

std::optional<std::uint64_t> readLease(const std::filesystem::path& directory) {
  const auto path=directory/"lease.bin";
  const int raw=::open(path.c_str(),O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
  if(raw<0) { if(errno==ENOENT) return std::nullopt; ioError("checkpoint owner lease open"); }
  Descriptor fd(raw);struct stat info{};
  if(::fstat(fd.value,&info)<0) ioError("checkpoint owner lease stat");
  if(!S_ISREG(info.st_mode) || info.st_size!=static_cast<off_t>(headerSize)) throw std::runtime_error("invalid checkpoint owner lease length");
  std::array<std::uint8_t,headerSize> data{};std::size_t offset=0;
  while(offset<data.size()) {
    const auto count=::read(fd.value,data.data()+offset,data.size()-offset);
    if(count<0) { if(errno==EINTR) continue;ioError("checkpoint owner lease read"); }
    if(count==0) throw std::runtime_error("truncated checkpoint owner lease");
    offset+=static_cast<std::size_t>(count);
  }
  if(!std::equal(leaseMagic.begin(),leaseMagic.end(),data.begin()) || readLE(data,8,4)!=1 || readLE(data,12,8)==0 || readLE(data,20,8)!=0 || readLE(data,28,4)!=crc32(data)) throw std::runtime_error("invalid checkpoint owner lease integrity or version");
  return readLE(data,12,8);
}

void syncDirectory(const std::filesystem::path& directory) { Descriptor fd(::open(directory.c_str(),O_RDONLY|O_DIRECTORY|O_CLOEXEC)); if(::fsync(fd.value)<0) ioError("checkpoint directory fsync"); }
void writeAtomic(const std::filesystem::path& directory,const std::string& name,std::span<const std::uint8_t> data) {
  std::string pattern=(directory/".checkpoint-XXXXXX").string();
  std::vector<char> path(pattern.begin(),pattern.end()); path.push_back(0);
  Descriptor fd(::mkstemp(path.data())); const std::filesystem::path temp(path.data());
  try {
    std::size_t offset=0;
    while(offset<data.size()) { const auto n=::write(fd.value,data.data()+offset,data.size()-offset); if(n<0) { if(errno==EINTR) continue; ioError("checkpoint write"); } if(n==0) throw std::runtime_error("checkpoint short write"); offset+=static_cast<std::size_t>(n); }
    if(::fsync(fd.value)<0) ioError("checkpoint file fsync");
    if(::rename(temp.c_str(),(directory/name).c_str())<0) ioError("checkpoint rename");
    syncDirectory(directory);
  } catch(...) { (void)::unlink(temp.c_str()); throw; }
}

void saveLocked(const std::filesystem::path& directory,std::size_t limit,std::span<const std::uint8_t> payload,std::uint64_t generation) {
  auto a=readSlot(directory/"slot0.bin",limit),b=readSlot(directory/"slot1.bin",limit);
  const auto newest=std::max(a.record?a.record->generation:0,b.record?b.record->generation:0);
  if(generation<=newest) throw std::runtime_error("stale checkpoint generation fenced");
  const int slot=!a.record?0:!b.record?1:a.record->generation<=b.record->generation?0:1;
  std::vector<std::uint8_t> data; data.reserve(headerSize+payload.size()); data.insert(data.end(),magic.begin(),magic.end());
  appendLE(data,1,4); appendLE(data,generation,8); appendLE(data,payload.size(),8); appendLE(data,0,4); data.insert(data.end(),payload.begin(),payload.end());
  const auto crc=crc32(data); for(unsigned i=0;i<4;i++) data[28+i]=static_cast<std::uint8_t>(crc>>(8*i));
  writeAtomic(directory,"slot"+std::to_string(slot)+".bin",data);
}
} // namespace

CheckpointStore::CheckpointStore(std::filesystem::path directory,std::size_t maxPayloadBytes):directory_(std::move(directory)),maxPayloadBytes_(maxPayloadBytes) {
  if(maxPayloadBytes_==0 || maxPayloadBytes_>10*1024*1024) throw std::invalid_argument("checkpoint payload limit must be in 1..10 MiB");
  std::filesystem::create_directories(directory_);
}

std::optional<CheckpointRecord> CheckpointStore::load() const {
  auto records=loadCandidates();
  if(records.empty()) return std::nullopt;
  return std::move(records.front());
}

std::vector<CheckpointRecord> CheckpointStore::loadCandidates() const {
  const Lock lock(directory_);
  auto a=readSlot(directory_/"slot0.bin",maxPayloadBytes_),b=readSlot(directory_/"slot1.bin",maxPayloadBytes_);
  std::vector<CheckpointRecord> records;
  if(a.record) records.push_back(std::move(*a.record));
  if(b.record) records.push_back(std::move(*b.record));
  if(!records.empty()) {
    std::sort(records.begin(),records.end(),[](const auto& left,const auto& right){return left.generation>right.generation;});
    return records;
  }
  if(a.exists || b.exists) throw std::runtime_error("no valid checkpoint: checksum, length or version rejected");
  return {};
}

void CheckpointStore::save(std::span<const std::uint8_t> payload,std::uint64_t generation) {
  if(payload.size()>maxPayloadBytes_) throw std::invalid_argument("checkpoint payload exceeds limit");
  if(generation==0) throw std::invalid_argument("checkpoint generation must be positive");
  const Lock lock(directory_);
  if(readLease(directory_)) throw std::runtime_error("checkpoint owner lease requires saveOwned");
  saveLocked(directory_,maxPayloadBytes_,payload,generation);
}

void CheckpointStore::save(std::span<const std::byte> payload,std::uint64_t generation) {
  save(std::span<const std::uint8_t>(reinterpret_cast<const std::uint8_t*>(payload.data()),payload.size()),generation);
}

std::uint64_t CheckpointStore::acquireLease() {
  const Lock lock(directory_);
  const auto previous=readLease(directory_).value_or(0);
  if(previous==std::numeric_limits<std::uint64_t>::max()) throw std::runtime_error("checkpoint owner lease exhausted");
  const auto lease=previous+1;
  std::vector<std::uint8_t> data(leaseMagic.begin(),leaseMagic.end());
  appendLE(data,1,4);appendLE(data,lease,8);appendLE(data,0,8);appendLE(data,0,4);
  const auto crc=crc32(data);for(unsigned i=0;i<4;i++) data[28+i]=static_cast<std::uint8_t>(crc>>(8*i));
  writeAtomic(directory_,"lease.bin",data);
  return lease;
}

void CheckpointStore::saveOwned(std::span<const std::uint8_t> payload,std::uint64_t generation,std::uint64_t lease) {
  if(payload.size()>maxPayloadBytes_) throw std::invalid_argument("checkpoint payload exceeds limit");
  if(generation==0 || lease==0) throw std::invalid_argument("checkpoint generation and owner lease must be positive");
  const Lock lock(directory_);
  const auto current=readLease(directory_);
  if(!current || *current!=lease) throw std::runtime_error("stale checkpoint owner lease fenced");
  // Keep the owner lock held throughout selection, fsync, rename, and directory
  // fsync. New-owner acquisition and publication therefore have one ordering.
  saveLocked(directory_,maxPayloadBytes_,payload,generation);
}

void CheckpointStore::saveOwned(std::span<const std::byte> payload,std::uint64_t generation,std::uint64_t lease) {
  saveOwned(std::span<const std::uint8_t>(reinterpret_cast<const std::uint8_t*>(payload.data()),payload.size()),generation,lease);
}
} // namespace surface
