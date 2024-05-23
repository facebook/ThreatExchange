// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

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

#include <vpdq/cpp/hashing/bufferhasher.h>
#include <vpdq/cpp/hashing/hasher.h>

namespace facebook {
namespace vpdq {
namespace hashing {

namespace {

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

} // namespace

template <typename TFrame>
VpdqHasher<TFrame>::VpdqHasher(
    size_t thread_count, VideoMetadata video_metadata)
    : m_done_hashing(false), m_video_metadata(video_metadata) {
  // Set thread count if specified
  if (thread_count == 0) {
    thread_count = std::thread::hardware_concurrency();
  } else {
    thread_count = thread_count;
  }

  m_multithreaded = (thread_count != 1);

  // Create consumer hasher threads if multithreading
  if (m_multithreaded) {
    consumer_threads.reserve(thread_count);
    for (size_t thread_idx{0}; thread_idx < thread_count; ++thread_idx) {
      consumer_threads.emplace_back(
          std::thread(std::bind(&VpdqHasher::consumer, this)));
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
std::vector<vpdqFeature> VpdqHasher<TFrame>::finish() {
  if (m_multithreaded) {
    {
      std::lock_guard<std::mutex> lock(m_queue_mutex);
      m_done_hashing = true;
    }

    m_queue_condition.notify_all();
    for (auto& thread : consumer_threads) {
      thread.join();
    }
  }

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
    if (m_queue.empty() && m_done_hashing)
      break;
    auto frame = std::move(m_queue.front());
    m_queue.pop();
    lock.unlock();
    hasher(frame);
  }
}

} // namespace hashing
} // namespace vpdq
} // namespace facebook
