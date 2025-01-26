// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef HASHER_H
#define HASHER_H

#include <algorithm>
#include <atomic>
#include <cmath>
#include <condition_variable>
#include <cstdio>
#include <fstream>
#include <functional>
#include <iostream>
#include <memory>
#include <mutex>
#include <queue>
#include <string>
#include <thread>
#include <vector>

#include <vpdq/cpp/hashing/bufferhasher.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>

namespace facebook {
namespace vpdq {
namespace hashing {

/** @brief Generic class for video frames. Stores pixels in its buffer which are
 *         used by PDQ for hashing.
 **/
class GenericFrame {
 public:
  /** @brief Constructor
   *
   *  @param buffer The pixel buffer used for PDQ hashing
   *  @param frameNumber The frame number in the video.
   **/
  GenericFrame(std::vector<unsigned char> buffer, uint64_t frameNumber)
      : m_buffer(std::move(buffer)), m_frameNumber(frameNumber){};

  /** @brief Get the frame number.
   *
   *  @return The frame number.
   **/
  uint64_t get_frame_number() const { return m_frameNumber; }

  /** @brief Get the pointer to the frame data buffer to be used for hashing.
   *
   *  @return Pointer to the frame data buffer.
   **/
  unsigned char* get_buffer_ptr() { return m_buffer.data(); }

  std::vector<unsigned char> m_buffer;
  uint64_t m_frameNumber;
};

struct VideoMetadata {
  float framerate{};
  uint32_t width{};
  uint32_t height{};
};

template <typename TFrame>
class VpdqHasher {
 public:
  /** @brief Construct hasher to hash frames and return a full Vpdq hash.
   *
   *  @param thread_count Number of threads to be used for hashing. 0 is use
   *                      auto.
   *  @param video_metadata Video characteristics for hashing.
   *
   *  @note Spawns hashing threads and begins hashing. Frames are hashed as they
   *        are added to the queue.
   **/
  VpdqHasher(size_t thread_count, VideoMetadata video_metadata);

  /** @brief Add a frame to the hashing queue.
   *
   * @param frame Frame to be hashed.
   **/
  void push_back(TFrame&& frame);

  /** @brief Stop and join all hashing threads.
   *
   * @note Not thread safe.
   **/
  void stop_hashing();

  /** @brief Block until all frames are finished hashing and get the final
   *         result.
   *
   * @return The vpdq hash for the whole video.
   *
   * @note Not thread safe.
   **/
  std::vector<vpdqFeature> finish();

  VpdqHasher() = delete;
  VpdqHasher(VpdqHasher const&) = delete;
  VpdqHasher& operator=(VpdqHasher const&) = delete;
  VpdqHasher(VpdqHasher&&) = delete;
  VpdqHasher& operator=(VpdqHasher&&) = delete;

  ~VpdqHasher() { stop_hashing(); }

 private:
  /** @brief True if hashing is multithreaded, false if singlethreaded.
   **/
  bool m_multithreaded;

  /** @brief Collection of hashing threads.
   **/
  std::vector<std::thread> consumer_threads;

  /** @brief Condition variable to signal queue processing.
   **/
  std::condition_variable m_queue_condition;

  /** @brief Mutex for the hash queue. Must be taken before touching the queue.
   **/
  std::mutex m_queue_mutex;

  /** @brief Queue of frames to be hashed.
   **/
  std::queue<TFrame> m_queue;

  /** @brief Mutex for the hash result. Must be taken before touching the
   *         result.
   **/
  std::mutex m_result_mutex;

  /** @brief PDQ hashes from the frame queue.
   **/
  std::vector<vpdqFeature> m_result;

  /** @brief State of video hashing.
   **/
  bool m_done_hashing;

  /** @brief Video metadata.
   **/
  VideoMetadata m_video_metadata;

  /** @brief Hashes frames from the queue and inserts the PDQ hash into the
   *         result.
   **/
  void hasher(TFrame& frame);

  /** @brief Runs the hasher in a loop. Hashes frames as they are added to the
   *         queue.
   **/
  void consumer();
};

/** @brief Hash a frame using PDQ.
 *
 *  @param frame The frame to be hashed.
 *  @param frameNumber The metadata from the video the frame is from.
 *
 *  @return The vdpdq hash of the frame.
 **/
template <typename TFrame>
vpdqFeature hashFrame(TFrame& frame, const VideoMetadata& video_metadata) {
  auto phasher = FrameBufferHasherFactory::createFrameHasher(
      video_metadata.height, video_metadata.width);

  int quality;
  pdq::hashing::Hash256 pdqHash;
  auto const is_hashing_successful =
      phasher->hashFrame(frame.get_buffer_ptr(), pdqHash, quality);
  if (!is_hashing_successful) {
    throw std::runtime_error(
        std::string{"Failed to hash frame buffer. Frame: "} +
        std::to_string(frame.get_frame_number()) +
        " Frame width or height smaller than the minimum hashable dimension");
  }
  return vpdqFeature{
      pdqHash,
      static_cast<int>(frame.get_frame_number()),
      quality,
      static_cast<float>(frame.get_frame_number()) / video_metadata.framerate};
}

template <typename TFrame>
VpdqHasher<TFrame>::VpdqHasher(
    size_t thread_count, VideoMetadata video_metadata)
    : m_done_hashing(false), m_video_metadata(video_metadata) {
  // Set thread count if specified
  if (thread_count == 0) {
    thread_count = std::thread::hardware_concurrency();
    // Some platforms may return 0 for hardware_concurrency(), per the standard.
    // If that occurs, set it to single-threaded.
    if (thread_count == 0) {
      thread_count = 1;
    }
  }

  m_multithreaded = (thread_count != 1);

  // Create consumer hasher threads if multithreading
  if (m_multithreaded) {
    consumer_threads.reserve(thread_count);
    for (size_t thread_idx{0}; thread_idx < thread_count; ++thread_idx) {
      consumer_threads.emplace_back(std::thread(&VpdqHasher::consumer, this));
    }
  }
}

template <typename TFrame>
void VpdqHasher<TFrame>::push_back(TFrame&& frame) {
  if (m_multithreaded) {
    {
      std::lock_guard<std::mutex> lock(m_queue_mutex);
      m_queue.push(std::move(frame));
      m_queue_condition.notify_one();
    }
  } else {
    hasher(frame);
  }
}

template <typename TFrame>
void VpdqHasher<TFrame>::stop_hashing() {
  if (m_multithreaded) {
    {
      std::lock_guard<std::mutex> lock(m_queue_mutex);
      if (m_done_hashing) {
        return;
      }

      m_done_hashing = true;
    }

    m_queue_condition.notify_all();
    for (auto& thread : consumer_threads) {
      thread.join();
    }
  }
}

template <typename TFrame>
std::vector<vpdqFeature> VpdqHasher<TFrame>::finish() {
  this->stop_hashing();

  // Sort out of order frames by frame number
  std::sort(
      std::begin(m_result),
      std::end(m_result),
      [](const vpdqFeature& a, const vpdqFeature& b) {
        return a.frameNumber < b.frameNumber;
      });

  return m_result;
}

template <typename TFrame>
void VpdqHasher<TFrame>::hasher(TFrame& frame) {
  auto hashedFrame = hashFrame(frame, m_video_metadata);
  {
    std::lock_guard<std::mutex> lock(m_result_mutex);
    m_result.push_back(std::move(hashedFrame));
  }
}

template <typename TFrame>
void VpdqHasher<TFrame>::consumer() {
  while (true) {
    std::unique_lock<std::mutex> lock(m_queue_mutex);
    m_queue_condition.wait(
        lock, [this] { return !m_queue.empty() || m_done_hashing; });
    if (m_queue.empty() && m_done_hashing) {
      break;
    }
    auto frame = std::move(m_queue.front());
    m_queue.pop();
    lock.unlock();
    hasher(frame);
  }
}

} // namespace hashing
} // namespace vpdq
} // namespace facebook

#endif // HASHER_H
