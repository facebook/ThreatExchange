// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <math.h>
#include <stdio.h>
#include <algorithm>
#include <cassert>
#include <condition_variable>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <memory>
#include <mutex>
#include <queue>
#include <string>
#include <thread>

#include <vpdq/cpp/hashing/bufferhasher.h>
#include <vpdq/cpp/hashing/filehasher.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>

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

class vpdqHasher {
 public:
  struct FatFrame {
    AVFrame* frame;
    int frameNumber;
  };

  std::condition_variable queue_condition;
  std::mutex queue_mutex;
  std::queue<FatFrame> frame_queue;
  std::mutex pdqHashes_mutex;
  std::vector<hashing::vpdqFeature> pdqHashes;
  std::mutex done_mutex;
  bool done = false;
  int num_consumers = std::thread::hardware_concurrency();
  AVCodecContext* codecContext;
  SwsContext* swsContext;
  int width;
  int height;
  double frameRate;
  int frameMod;

  // Decode and add vpdqFeature to the hashes vector
  // Returns the number of frames processed (this is can be more than 1!)
  int processFrame(AVPacket* packet, int frameNumber) {
    AVFrame* frame = av_frame_alloc();
    assert(frame != nullptr);
    // TODO: check for frame good alloc
    AVFrame* targetFrame = createFrame(width, height);
    assert(targetFrame != nullptr);
    // Send the packet to the decoder
    int ret = avcodec_send_packet(codecContext, packet) < 0;
    // std::cout << codecContext->frame_num << std::endl;
    if (ret < 0) {
      throw std::runtime_error("Cannot send packet to decoder");
    }

    // Receive the decoded frame
    while (ret >= 0) {
      ret = avcodec_receive_frame(codecContext, frame);
      if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
        break;
      } else if (ret < 0) {
        throw std::runtime_error("Cannot receive frame from decoder");
      }

      if (frameNumber % frameMod == 0) {
        // Resize the frame and convert to RGB24
        sws_scale(
            swsContext,
            frame->data,
            frame->linesize,
            0,
            codecContext->height,
            targetFrame->data,
            targetFrame->linesize);

        std::unique_lock<std::mutex> lock(queue_mutex);
        AVFrame* newTargetFrame = createFrame(width, height);
        av_frame_copy(newTargetFrame, targetFrame);
        FatFrame fatFrame = {newTargetFrame, frameNumber};

        frame_queue.push(fatFrame);
        lock.unlock();
        queue_condition.notify_one();
      }
      frameNumber += 1;
    }
    av_frame_free(&frame);
    av_freep(&targetFrame->data[0]);
    av_frame_free(&targetFrame);
    return frameNumber;
  }

  AVFrame* createFrame(int width, int height) {
    // Pixel format for the image passed to PDQ
    constexpr AVPixelFormat pixelFormat = AV_PIX_FMT_RGB24;

    // Create a frame for resizing and converting the decoded frame to RGB24
    AVFrame* targetFrame = av_frame_alloc();
    if (targetFrame == nullptr) {
      std::cerr << "Cannot allocate target frame" << std::endl;
      return nullptr;
    }

    targetFrame->format = pixelFormat;
    targetFrame->width = width;
    targetFrame->height = height;

    if (av_image_alloc(
            targetFrame->data,
            targetFrame->linesize,
            width,
            height,
            pixelFormat,
            1) < 0) {
      std::cerr << "Cannot fill target frame image" << std::endl;
      av_frame_free(&targetFrame);
      return nullptr;
    }
    return targetFrame;
  }

  void hasher(bool verbose, AVFrame* frame, int frameNumber) {
    assert(frame != nullptr);
    assert(frame->height != 0 && frame->width != 0);
    int quality;
    pdq::hashing::Hash256 pdqHash;

    std::unique_ptr<vpdq::hashing::AbstractFrameBufferHasher> phasher =
        vpdq::hashing::FrameBufferHasherFactory::createFrameHasher(
            frame->height, frame->width);

    if (phasher == nullptr) {
      throw std::runtime_error("phasher allocation failed");
    }

    bool ret = phasher->hashFrame(frame->data[0], pdqHash, quality);
    if (!ret) {
      throw std::runtime_error(
          "Failed to hash frame buffer." + std::string("Frame: ") +
          std::to_string(frameNumber) +
          std::string(
              " Frame width or height smaller than the minimum hashable dimension"));
    }

    // Write frame to file here for debugging:
    // saveFrameToFile(frame, "frame.rgb");

    // Append vpdq feature to pdqHashes vector
    std::lock_guard<std::mutex> lock(pdqHashes_mutex);
    vpdqFeature feature = {
        pdqHash,
        frameNumber,
        quality,
        static_cast<double>(frameNumber) / frameRate};
    pdqHashes.push_back(feature);
    if (verbose) {
      std::cout << "PDQHash: " << pdqHash.format() << std::endl;
    }
  }

  void consumer() {
    while (true) {
      std::unique_lock<std::mutex> lock(queue_mutex);
      queue_condition.wait(
          lock, [this] { return !frame_queue.empty() || done; });
      if (frame_queue.empty() && done)
        break;
      FatFrame fatFrame = frame_queue.front();
      frame_queue.pop();
      lock.unlock();
      AVFrame* frame = fatFrame.frame;
      int frameNumber = fatFrame.frameNumber;
      hasher(false, frame, frameNumber);
      av_freep(frame->data);
      if (frame != nullptr)
        av_frame_free(&frame);
    }
  }

  void start_hashing() {
    // Hash the frames
    std::vector<std::thread> consumer_threads;
    for (int i = 0; i < num_consumers; ++i) {
      consumer_threads.push_back(
          std::thread(std::bind(&vpdqHasher::consumer, this)));
    }

    std::unique_lock<std::mutex> lock(queue_mutex);
    // std::cout << "Finished decoding frames" << std::endl;
    done = true;
    lock.unlock();
    queue_condition.notify_all();
    for (auto& thread : consumer_threads) {
      thread.join();
    }
  }

  ~vpdqHasher() {
    if (codecContext != nullptr)
      avcodec_free_context(&codecContext);
    if (swsContext != nullptr)
      sws_freeContext(swsContext);
  }
};

/* @brief Writes an AVFrame to a file
 *
 * Useful for debugging.
 * Not used by any other functions.
 *
 * This can viewed using ffplay directly:
 * ffplay -f rawvideo -pixel_format rgb24 \
 * -video_size <WIDTH>x<HEIGHT> <filename>
 *
 * @param frame
 * @param filename
 * @return void
 */
static void saveFrameToFile(AVFrame* frame, const char* filename) {
  if (!frame) {
    throw std::invalid_argument("Cannot save frame to file. Frame is null.");
  }

  std::ofstream outfile(filename, std::ios::out | std::ios::binary);
  if (!outfile) {
    throw std::runtime_error(
        "Cannot save frame to file " + std::string(filename));
  }

  for (int y = 0; y < frame->height; y++) {
    outfile.write(
        reinterpret_cast<const char*>(frame->data[0] + y * frame->linesize[0]),
        frame->width * 3);
  }
  std::cout << "Saved frame to file " << filename << " with dimensions "
            << frame->width << "x" << frame->height << std::endl;
  outfile.close();
}
// Get pdq hashes for selected frames every secondsPerHash
bool hashVideoFile(
    const std::string& inputVideoFileName,
    std::vector<hashing::vpdqFeature>& pdqHashes,
    bool verbose,
    const double secondsPerHash,
    const int downsampleWidth,
    const int downsampleHeight) {
  vpdqHasher hasher;

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

  av_log_set_level(AV_LOG_DEBUG);
  // Open the input file
  AVFormatContext* formatContext = nullptr;
  if (avformat_open_input(
          &formatContext, inputVideoFileName.c_str(), nullptr, nullptr) != 0) {
    std::cerr << "Cannot open the video" << std::endl;
    return false;
  }

  // Retrieve stream information
  if (avformat_find_stream_info(formatContext, nullptr) < 0) {
    std::cerr << "Cannot find stream info" << std::endl;
    avformat_close_input(&formatContext);
    return false;
  }

  // Find the first video stream
  int videoStreamIndex = -1;
  for (unsigned int i = 0; i < formatContext->nb_streams; ++i) {
    if (formatContext->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_VIDEO) {
      videoStreamIndex = i;
      break;
    }
  }

  if (videoStreamIndex == -1) {
    std::cerr << "No video stream found" << std::endl;
    avformat_close_input(&formatContext);
    return false;
  }

  // Get the video codec parameters
  AVCodecParameters* codecParameters =
      formatContext->streams[videoStreamIndex]->codecpar;

  // Get the width and height
  // If downsampleWidth or downsampleHeight is 0,
  // then use the video's original dimensions
  hasher.width = downsampleWidth;
  hasher.height = downsampleHeight;
  if (hasher.width == 0) {
    hasher.width = codecParameters->width;
  }
  if (hasher.height == 0) {
    hasher.height = codecParameters->height;
  }

  if (hasher.width == 0 || hasher.height == 0) {
    std::cerr << "Width or height equals 0" << std::endl;
    avformat_close_input(&formatContext);
    return false;
  }

  // Find the video decoder
  const AVCodec* codec = avcodec_find_decoder(codecParameters->codec_id);
  if (!codec) {
    std::cerr << "Codec decoder not found" << std::endl;
    avformat_close_input(&formatContext);
    return false;
  }

  // Create the codec context
  hasher.codecContext = avcodec_alloc_context3(codec);
  if (avcodec_parameters_to_context(hasher.codecContext, codecParameters) < 0) {
    std::cerr << "Cannot copy codec parameters to context" << std::endl;
    avformat_close_input(&formatContext);
    return false;
  }

  // Determine the number of threads to use and multithreading type
  // TODO: MOVE TO CONSTRUCTOR
  hasher.codecContext->thread_count = 0;

  if (codec->capabilities & AV_CODEC_CAP_FRAME_THREADS) {
    hasher.codecContext->thread_type = FF_THREAD_FRAME;
  } else if (codec->capabilities & AV_CODEC_CAP_SLICE_THREADS) {
    hasher.codecContext->thread_type = FF_THREAD_SLICE;
  } else {
    hasher.codecContext->thread_count = 1;
  }

  // Open the codec context
  if (avcodec_open2(hasher.codecContext, codec, nullptr) < 0) {
    std::cerr << "Cannot open codec context" << std::endl;
    avformat_close_input(&formatContext);
    return false;
  }

  // Get the framerate
  AVRational avframeRate =
      formatContext->streams[videoStreamIndex]->avg_frame_rate;

  // if avg_frame_rate is 0, fall back to r_frame_rate which is the
  // lowest framerate with which all timestamps can be represented accurately
  if (avframeRate.num == 0 || avframeRate.den == 0) {
    avframeRate = formatContext->streams[videoStreamIndex]->r_frame_rate;
  }

  hasher.frameRate = static_cast<double>(avframeRate.num) /
      static_cast<double>(avframeRate.den);
  if (hasher.frameRate == 0) {
    std::cerr << "Framerate is zero" << std::endl;
    avformat_close_input(&formatContext);
    return false;
  }

  // Pixel format for the image passed to PDQ
  constexpr AVPixelFormat pixelFormat = AV_PIX_FMT_RGB24;

  // Create the image rescaler context
  hasher.swsContext = sws_getContext(
      hasher.codecContext->width,
      hasher.codecContext->height,
      hasher.codecContext->pix_fmt,
      hasher.width,
      hasher.height,
      pixelFormat,
      SWS_LANCZOS,
      nullptr,
      nullptr,
      nullptr);

  if (hasher.swsContext == nullptr) {
    std::cerr << "Cannot create sws context" << std::endl;
    avformat_close_input(&formatContext);
    return false;
  }

  AVPacket* packet = av_packet_alloc();
  if (packet == nullptr) {
    std::cerr << "Cannot allocate packet" << std::endl;
    avformat_close_input(&formatContext);
    return false;
  }

  hasher.frameMod = secondsPerHash * hasher.frameRate;
  if (hasher.frameMod == 0) {
    // Avoid truncate to zero on corner-case where
    // secondsPerHash = 1 and frameRate < 1.
    hasher.frameMod = 1;
  }

  // Read frames in a loop and process them
  int ret = 0;
  int frameNumber = 0;
  bool failed = false;
  while (av_read_frame(formatContext, packet) == 0) {
    // Check if the packet belongs to the video stream
    if (packet->stream_index == videoStreamIndex) {
      try {
        ret = hasher.processFrame(packet, frameNumber);
        frameNumber = ret;
      } catch (const std::runtime_error& e) {
        std::cerr << "Processing frame failed: " << e.what() << std::endl;
        failed = true;
        av_packet_unref(packet);
        break;
      }
    }
    av_packet_unref(packet);
  }

  if (!failed) {
    // Flush decode buffer
    // See for more information:
    //
    // https://github.com/FFmpeg/FFmpeg/blob/6a9d3f46c7fc661b86192e922ab932495d27f953/doc/examples/decode_video.c#L182

    try {
      ret = hasher.processFrame(packet, frameNumber);
    } catch (const std::runtime_error& e) {
      std::cerr << "Flushing frame buffer failed: " << e.what() << std::endl;
      failed = true;
      av_packet_unref(packet);
    }
    frameNumber = ret;
    av_packet_unref(packet);
  }

  if (!failed) {
    hasher.start_hashing();
  }

  av_packet_free(&packet);
  avformat_close_input(&formatContext);

  if (failed) {
    return false;
  }

  std::sort(
      hasher.pdqHashes.begin(),
      hasher.pdqHashes.end(),
      [](const vpdqFeature& a, const vpdqFeature& b) {
        return a.frameNumber < b.frameNumber;
      });
  pdqHashes.assign(hasher.pdqHashes.begin(), hasher.pdqHashes.end());
  std::cout << "Hashed " << hasher.pdqHashes.size() << " frameNumber "
            << frameNumber << std::endl;
  if (static_cast<size_t>(frameNumber) != pdqHashes.size()) {
    throw std::runtime_error(
        "pdqhashes is different than frameNumber: " +
        std::to_string(frameNumber) + " " + std::to_string(pdqHashes.size()));
  }
  return true;
}

} // namespace hashing
} // namespace vpdq
} // namespace facebook
