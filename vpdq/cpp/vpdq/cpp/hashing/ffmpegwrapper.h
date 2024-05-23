// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef FFMPEGWRAPPER_H
#define FFMPEGWRAPPER_H

#include <memory>

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/frame.h>
#include <libavutil/imgutils.h>
#include <libavutil/log.h>
#include <libavutil/mem.h>
#include <libswscale/swscale.h>
}

namespace facebook {
namespace vpdq {
namespace hashing {
namespace ffmpeg {

// Pixel format for the image passed to PDQ
constexpr AVPixelFormat PIXEL_FORMAT = AV_PIX_FMT_RGB24;

// Downsample method for the image passed to PDQ
constexpr int DOWNSAMPLE_METHOD = SWS_AREA;

struct AVFrameDeleter {
  void operator()(AVFrame* ptr) const {
    if (ptr) {
      if (ptr->data[0]) {
        // Free memory allocated by image_alloc
        // See createTargetFrame()
        av_freep(&ptr->data[0]);
      }
      av_frame_free(&ptr);
    }
  }
};

struct AVPacketDeleter {
  void operator()(AVPacket* ptr) const {
    if (ptr) {
      av_packet_unref(ptr);
      av_packet_free(&ptr);
    }
  }
};

struct SwsContextDeleter {
  void operator()(SwsContext* ptr) const { sws_freeContext(ptr); }
};

struct AVFormatContextDeleter {
  void operator()(AVFormatContext* ptr) const { avformat_close_input(&ptr); }
};

struct AVCodecContextDeleter {
  void operator()(AVCodecContext* ptr) const { avcodec_free_context(&ptr); }
};

using AVFramePtr = std::unique_ptr<AVFrame, AVFrameDeleter>;
using AVPacketPtr = std::unique_ptr<AVPacket, AVPacketDeleter>;
using SwsContextPtr = std::unique_ptr<SwsContext, SwsContextDeleter>;
using AVFormatContextPtr =
    std::unique_ptr<AVFormatContext, AVFormatContextDeleter>;
using AVCodecContextPtr =
    std::unique_ptr<AVCodecContext, AVCodecContextDeleter>;

/**
 * @brief Video wrapper that can open a video file.
 **/
class FFmpegVideo {
 public:
  FFmpegVideo(const std::string& filename);

  /**
   * @brief Create the SwsContext for resizing the video frames.
   *
   * @return True if the swscontext was successfully created otherwise false.
   *
   * @note If the SwsContext fails to be created the swsContext will be nullptr.
   */
  bool createSwsContext();

  AVCodecContextPtr codecContext;
  AVFormatContextPtr formatContext;
  SwsContextPtr swsContext;
  unsigned int videoStreamIndex;
  int width;
  int height;
  double frameRate;
};

/**
 * @brief AVFrame implementation of the Frame type class.
 **/
class FFmpegFrame {
 public:
  /** @brief Constructor
   *
   *  @param frame The AVFrame.
   *  @param frameNumber The frame number in the video.
   **/
  FFmpegFrame(AVFramePtr frame, uint64_t frameNumber);

  /** @brief Get the frame number.
   *
   *  @return The frame number.
   **/
  uint64_t get_frame_number() const;

  /** @brief Get the pointer to the frame data buffer to be used for hashing.
   *
   *  @return Pointer to the frame data buffer.
   **/
  unsigned char* get_buffer_ptr();

  // Copy
  FFmpegFrame(FFmpegFrame const&) = delete;
  FFmpegFrame& operator=(FFmpegFrame const&) = delete;

  // Move
  FFmpegFrame(FFmpegFrame&&) = default;
  FFmpegFrame& operator=(FFmpegFrame&&) = default;

  ~FFmpegFrame() = default;

 private:
  AVFramePtr m_frame;
  uint64_t m_frameNumber;
};

} // namespace ffmpeg
} // namespace hashing
} // namespace vpdq
} // namespace facebook

#endif // FFMPEGWRAPPER_H
