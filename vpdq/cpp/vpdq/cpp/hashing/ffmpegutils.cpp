// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <algorithm>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

#include <vpdq/cpp/hashing/ffmpegutils.h>
#include <vpdq/cpp/hashing/ffmpegwrapper.h>

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

  frame->format = PIXEL_FORMAT;
  frame->width = width;
  frame->height = height;

  // TODO: Alignment is forced to 1, but the alignment should be variable (0).
  // This requires updating PDQFrameBufferHasher and VpdqHasher to pass the
  // linesize as the row stride to PDQ (see GH #1918)
  int ret = av_frame_get_buffer(frame.get(), 1);
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
