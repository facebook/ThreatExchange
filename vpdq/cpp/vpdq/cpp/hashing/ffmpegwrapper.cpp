// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <vpdq/cpp/hashing/ffmpegwrapper.h>

#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/avutil.h>
#include <libavutil/imgutils.h>
#include <libswscale/swscale.h>
}

namespace facebook {
namespace vpdq {
namespace hashing {
namespace ffmpeg {

void AVFrameDeleter::operator()(AVFrame* ptr) const {
  if (ptr) {
    av_frame_free(&ptr);
  }
}

void AVPacketDeleter::operator()(AVPacket* ptr) const {
  av_packet_free(&ptr);
}

void SwsContextDeleter::operator()(SwsContext* ptr) const {
  sws_freeContext(ptr);
}

void AVFormatContextDeleter::operator()(AVFormatContext* ptr) const {
  avformat_close_input(&ptr);
}

void AVCodecContextDeleter::operator()(AVCodecContext* ptr) const {
  avcodec_free_context(&ptr);
}

FFmpegVideo::FFmpegVideo(const std::string& filename) : videoStreamIndex{-1U} {
  // Open the input file
  AVFormatContext* formatContextRawPtr{nullptr};
  if (avformat_open_input(
          &formatContextRawPtr, filename.c_str(), nullptr, nullptr) != 0) {
    throw std::runtime_error("Cannot open video");
  }
  formatContext = AVFormatContextPtr(formatContextRawPtr);

  // Retrieve stream information
  if (avformat_find_stream_info(formatContext.get(), nullptr) < 0) {
    throw std::runtime_error("Cannot find video stream info");
  }

  // Find the first video stream
  for (unsigned int stream_idx{0U}; stream_idx < formatContext->nb_streams;
       ++stream_idx) {
    if (formatContext->streams[stream_idx]->codecpar->codec_type ==
        AVMEDIA_TYPE_VIDEO) {
      videoStreamIndex = stream_idx;
      break;
    }
  }

  if (videoStreamIndex == -1U) {
    throw std::runtime_error("No video stream found");
  }

  // Get the video codec parameters
  const AVCodecParameters* const codecParameters{
      formatContext->streams[videoStreamIndex]->codecpar};

  width = codecParameters->width;
  height = codecParameters->height;
  if (width == 0 || height == 0) {
    throw std::runtime_error("Width or height equals 0");
  }

  // Find the video decoder
  const AVCodec* const codec{avcodec_find_decoder(codecParameters->codec_id)};
  if (!codec) {
    throw std::runtime_error("Video codec id not found");
  }

  // Create the codec context
  codecContext = AVCodecContextPtr(avcodec_alloc_context3(codec));
  if (codecContext.get() == nullptr) {
    throw std::runtime_error("Failed to allocate video codec context.");
  }
  if (avcodec_parameters_to_context(codecContext.get(), codecParameters) < 0) {
    throw std::runtime_error(
        "Failed to copy codec parameters to codec context.");
  }

  // Determine the number of threads to use and multithreading type
  codecContext->thread_count = 0;

  if (codec->capabilities & AV_CODEC_CAP_SLICE_THREADS) {
    codecContext->thread_type = FF_THREAD_SLICE;
  } else {
    codecContext->thread_count = 1;
  }

  // Open the codec context
  if (avcodec_open2(codecContext.get(), codec, nullptr) < 0) {
    throw std::runtime_error("Failed to open video codec context");
  }

  // Get the framerate
  AVRational avframeRate{
      formatContext->streams[videoStreamIndex]->avg_frame_rate};
  // if avg_frame_rate is 0, fall back to r_frame_rate which is the
  // lowest framerate with which all timestamps can be represented accurately
  if (avframeRate.num == 0 || avframeRate.den == 0) {
    avframeRate = formatContext->streams[videoStreamIndex]->r_frame_rate;
  }

  frameRate = static_cast<double>(avframeRate.num) /
      static_cast<double>(avframeRate.den);
  if (frameRate == 0) {
    throw std::runtime_error("Video framerate was detected to be zero.");
  }
}

bool FFmpegVideo::createSwsContext() {
  swsContext = SwsContextPtr(sws_getContext(
      codecContext->width,
      codecContext->height,
      codecContext->pix_fmt,
      width,
      height,
      get_pixel_format(),
      get_downsample_method(),
      nullptr,
      nullptr,
      nullptr));

  return (swsContext.get() != nullptr);
}

FFmpegFrame::FFmpegFrame(AVFramePtr frame, uint64_t frameNumber, int linesize)
    : m_frame(std::move(frame)),
      m_frameNumber(frameNumber),
      m_linesize(linesize) {}

uint64_t FFmpegFrame::get_frame_number() const {
  return m_frameNumber;
}

unsigned char* FFmpegFrame::get_buffer_ptr() {
  return m_frame->data[0];
}

int FFmpegFrame::get_linesize() const {
  return m_linesize;
}

void saveFrameToFile(AVFramePtr frame, const std::string& filename) {
  if (!frame) {
    throw std::invalid_argument("Cannot save frame to file. Frame is null.");
  }

  std::ofstream outfile(filename, std::ios::out | std::ios::binary);
  if (!outfile) {
    throw std::runtime_error("Cannot save frame to file " + filename);
  }

  for (int y = 0; y < frame->height; y++) {
    outfile.write(
        reinterpret_cast<const char*>(frame->data[0] + y * frame->linesize[0]),
        frame->width * 3);
  }
  outfile.close();
}

AVFramePtr createRGB24Frame(size_t const width, size_t const height) {
  AVFramePtr frame(av_frame_alloc());
  if (frame == nullptr) {
    throw std::bad_alloc();
  }

  frame->format = get_pixel_format();
  frame->width = width;
  frame->height = height;

  int ret = av_frame_get_buffer(frame.get(), 0);
  if (ret < 0) {
    char errbuf[AV_ERROR_MAX_STRING_SIZE];
    int strerr = av_strerror(ret, errbuf, sizeof(errbuf));
    if (strerr != 0) {
      throw std::runtime_error("av_frame_get_buffer failed.");
    }
    throw std::runtime_error(
        std::string("av_frame_get_buffer failed: ") + errbuf);
  }
  return frame;
}

} // namespace ffmpeg
} // namespace hashing
} // namespace vpdq
} // namespace facebook
