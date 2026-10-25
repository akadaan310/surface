#pragma once
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <span>
#include <vector>

namespace surface {
struct CheckpointRecord {
  std::uint64_t generation{};
  std::vector<std::uint8_t> payload;
};

// Payload bytes are opaque. The owning physics/view serializer must perform
// finite-value, dimension, and schema validation before applying a loaded state.
class CheckpointStore {
public:
  explicit CheckpointStore(std::filesystem::path directory,
                           std::size_t maxPayloadBytes = 10 * 1024 * 1024);
  void save(std::span<const std::uint8_t> payload, std::uint64_t generation);
  void save(std::span<const std::byte> payload, std::uint64_t generation);
  // A replacement runtime acquires a fresh durable owner token once. Every
  // subsequent save must carry that fixed token; stale owners fail closed.
  std::uint64_t acquireLease();
  void saveOwned(std::span<const std::uint8_t> payload, std::uint64_t generation,
                 std::uint64_t lease);
  void saveOwned(std::span<const std::byte> payload, std::uint64_t generation,
                 std::uint64_t lease);
  std::optional<CheckpointRecord> load() const;
  // At most two CRC-valid records, newest first. A state owner can reject a
  // semantically invalid payload and atomically restore the previous record.
  std::vector<CheckpointRecord> loadCandidates() const;
private:
  std::filesystem::path directory_;
  std::size_t maxPayloadBytes_;
};
} // namespace surface
