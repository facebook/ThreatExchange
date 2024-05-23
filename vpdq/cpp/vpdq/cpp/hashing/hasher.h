// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef HASHER_H
#define HASHER_H

#include <condition_variable>
#include <mutex>
#include <queue>
#include <thread>
#include <vector>

#include <vpdq/cpp/hashing/ffmpegwrapper.h>
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

// Explicit template instantiation for all frame types.
template class VpdqHasher<GenericFrame>;
template class VpdqHasher<ffmpeg::FFmpegFrame>;

} // namespace hashing
} // namespace vpdq
} // namespace facebook

#endif // HASHER_H
