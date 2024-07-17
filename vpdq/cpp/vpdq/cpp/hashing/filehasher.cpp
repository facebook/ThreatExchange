// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <iostream>
#include <memory>
#include <string>

#include <vpdq/cpp/hashing/ffmpegutils.h>
#include <vpdq/cpp/hashing/ffmpegwrapper.h>
#include <vpdq/cpp/hashing/filehasher.h>
#include <vpdq/cpp/hashing/hasher.h>

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

namespace {

using ffmpeg::AVFramePtr;
using ffmpeg::AVPacketPtr;
using ffmpeg::FFmpegFrame;
using ffmpeg::FFmpegVideo;

// Class that decodes FFmpeg frames and hashes them.
class FFmpegHasher {
 public:
  FFmpegHasher(
      std::unique_ptr<FFmpegVideo> video,
      unsigned int thread_count,
      double secondsPerHash)
      : m_video(std::move(video)),
        m_vpdqhasher(
            thread_count,
            VideoMetadata{
                static_cast<float>(m_video->frameRate),
                static_cast<uint32_t>(m_video->width),
                static_cast<uint32_t>(m_video->height)}) {
    m_frameMod = static_cast<int>(secondsPerHash * m_video->frameRate);
    if (m_frameMod == 0) {
      // Avoid truncate to zero on corner-case where
      // secondsPerHash = 1 and frameRate < 1.
      m_frameMod = 1;
    }

    m_decodeFrame = AVFramePtr(av_frame_alloc());
    if (m_decodeFrame.get() == nullptr) {
      throw std::bad_alloc();
    }
  }

  bool run(std::vector<hashing::vpdqFeature>& pdqHashes) {
    // Create packet used to read frames
    // The packet is moved into processPacket() in order
    // to reuse the same packet for each frame to avoid allocs
    AVPacketPtr packet(av_packet_alloc());
    if (packet.get() == nullptr) {
      std::cerr << "Failed to allocate frame packet." << '\n';
      return false;
    }

    // Read frames in a loop and process them
    bool failed = false;
    while (av_read_frame(m_video->formatContext.get(), packet.get()) == 0) {
      // Check if the packet belongs to the video stream
      try {
        processPacket(*packet);
      } catch (const std::runtime_error& e) {
        std::cerr << "Processing frame failed: " << e.what() << '\n';
        failed = true;
        break;
      }
    }

    if (!failed) {
      // Flush decode buffer
      // See for more information:
      // https://github.com/FFmpeg/FFmpeg/blob/6a9d3f46c7fc661b86192e922ab932495d27f953/doc/examples/decode_video.c#L182

      try {
        processPacket(*packet);
      } catch (const std::runtime_error& e) {
        std::cerr << "Flushing frame buffer failed: " << e.what() << '\n';
        failed = true;
      }
    }

    // Signal to the threads that no more frames will be added to the queue
    pdqHashes = m_vpdqhasher.finish();

    return !failed;
  }

  // Decode and add vpdqFeature to the hashes vector
  // Increments the passed frame number
  // Returns back the processed packet
  void processPacket(AVPacket& packet) {
    if (static_cast<unsigned int>(packet.stream_index) !=
        m_video->videoStreamIndex) {
      // This must be called to free the packet buffer filled by av_read_frame
      av_packet_unref(&packet);
      return;
    }

    // Send the packet to the decoder
    auto const send_packet_err =
        avcodec_send_packet(m_video->codecContext.get(), &packet);
    if (send_packet_err < 0) {
      throw std::runtime_error("Cannot send packet to decoder");
    }

    // Receive the decoded frame
    int receive_frame_err{};
    while (receive_frame_err >= 0) {
      receive_frame_err = avcodec_receive_frame(
          m_video->codecContext.get(), m_decodeFrame.get());

      // Check for receiving errors
      if (receive_frame_err == AVERROR(EAGAIN) ||
          receive_frame_err == AVERROR_EOF) {
        break;
      } else if (receive_frame_err < 0) {
        throw std::runtime_error("Cannot receive frame from decoder");
      } else {
        // no error. we're good.
      }

// AVCodecContext::frame_number was deprecated in FFmpeg 6.0
// in favor of AVCodecContext::frame_num
#if LIBAVCODEC_VERSION_MAJOR >= 60
      const auto codecFrameNumber = m_video->codecContext->frame_num;
#else
      const auto codecFrameNumber = m_video->codecContext->frame_number;
#endif
      const int64_t frameNumber{int64_t{codecFrameNumber} - 1};

      if (frameNumber % m_frameMod == 0) {
        AVFramePtr targetFrame{};
        try {
          targetFrame =
              ffmpeg::createRGB24Frame(m_video->width, m_video->height);
        } catch (const std::runtime_error& e) {
          std::cerr << e.what() << '\n';
          throw;
        }
        // Resize the frame and convert to RGB24
        sws_scale(
            m_video->swsContext.get(),
            m_decodeFrame->data,
            m_decodeFrame->linesize,
            0,
            m_video->codecContext->height,
            targetFrame->data,
            targetFrame->linesize);

        /*
        // Example of how hashing looks for GenericFrame:
        GenericFrame frame{{}, get_frame_number()};
        frame.m_buffer.reserve(3 * m_video->width * m_video->height);
        std::copy_n(targetFrame->data[0], 3 * m_video->width * m_video->height,
        std::back_inserter(frame.m_buffer));
        // This is not used here, because it requires copying the entire frame
        // to the GenericFrame buffer, which is slow.
        */

        FFmpegFrame frame{
            std::move(targetFrame), static_cast<uint64_t>(frameNumber)};
        m_vpdqhasher.push_back(std::move(frame));
      }
    }

    // This must be called to free the packet buffer filled by av_read_frame
    av_packet_unref(&packet);
  }

 private:
  std::unique_ptr<FFmpegVideo> m_video;
  VpdqHasher<FFmpegFrame> m_vpdqhasher;
  AVFramePtr m_decodeFrame;
  int m_frameMod{};
};

} // namespace

// Get pdq hashes for selected frames every secondsPerHash
bool hashVideoFile(
    const std::string& inputVideoFileName,
    std::vector<hashing::vpdqFeature>& pdqHashes,
    bool verbose,
    const double secondsPerHash,
    const int downsampleWidth,
    const int downsampleHeight,
    const unsigned int num_threads) {
  // These are lavu_log_constants from "libavutil/log.h"
  // It can be helpful for debugging to
  // set this to AV_LOG_DEBUG or AV_LOG_VERBOSE
  //
  // Default is AV_LOG_INFO, but that sometimes prints ugly
  // random messages like "[libdav1d @ 0x5576493b62c0] libdav1d 1.2.1"
  if (verbose) {
    // "Something somehow does not look correct."
    av_log_set_level(AV_LOG_WARNING);
  } else {
    // "Something went wrong and recovery is not possible."
    av_log_set_level(AV_LOG_FATAL);
  }

  std::unique_ptr<FFmpegVideo> video{};
  try {
    video = std::make_unique<FFmpegVideo>(inputVideoFileName);
  } catch (const std::runtime_error& e) {
    std::cerr << "Error while attempting to read video file: " << e.what()
              << '\n';
    return false;
  }

  // If downsampleWidth or downsampleHeight is 0,
  // then use the video's original dimensions
  if (downsampleWidth > 0) {
    video->width = downsampleWidth;
  }
  if (downsampleHeight > 0) {
    video->height = downsampleHeight;
  }

  // Create image rescaler context
  if (!video->createSwsContext()) {
    std::cerr << "Error while attempting to create sws context.\n";
    return false;
  }

  // Create frame hasher
  FFmpegHasher hasher(std::move(video), num_threads, secondsPerHash);

  return hasher.run(pdqHashes);
}

} // namespace hashing
} // namespace vpdq
} // namespace facebook
