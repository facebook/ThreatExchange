// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <math.h>
#include <stdio.h>
#include <cassert>
#include <condition_variable>
#include <fstream>
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

struct FatFrame {
  AVFrame* frame;
  int frameNumber;
};

int num_consumers = std::thread::hardware_concurrency();

static std::mutex queue_mutex;
static std::queue<FatFrame> frame_queue;

static std::mutex pdqHashes_mutex;
static std::vector<hashing::vpdqFeature> pdqHashes1;

static AVCodecContext* codecContext;
static SwsContext* swsContext;
int width;
int height;

static double frameRate;
static int frameMod;

std::condition_variable queue_condition;

static std::mutex done_mutex;
bool done = false;

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

static AVFrame* createFrame(int width, int height) {
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

// Decode and add vpdqFeature to the hashes vector
// Returns the number of frames processed
static int processFrame(
    AVPacket* packet,
    // AVFrame* frame,
    // AVFrame* targetFrame,
    // SwsContext* swsContext,
    // AVCodecContext* codecContext,
    // std::unique_ptr<vpdq::hashing::AbstractFrameBufferHasher>& phasher,
    // std::vector<hashing::vpdqFeature>& pdqHashes,
    // double frameRate,
    int frameNumber
    // int frameMod)
) {
  AVFrame* frame = av_frame_alloc();
  assert(frame != nullptr);
  // TODO: check for frame good alloc
  AVFrame* targetFrame = createFrame(width, height);
  assert(targetFrame != nullptr);
  // Send the packet to the decoder
  int ret = avcodec_send_packet(codecContext, packet) < 0;
  std::cout << codecContext->frame_num << std::endl;
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
      FatFrame fatFrame = {targetFrame, frameNumber};

      frame_queue.push(fatFrame);
      lock.unlock();
      queue_condition.notify_one();
    }
    frameNumber += 1;
  }
  av_frame_free(&frame);
  return frameNumber;
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
  pdqHashes1.push_back(
      {pdqHash,
       frameNumber,
       quality,
       static_cast<double>(frameNumber) / frameRate});
  if (verbose) {
    std::cout << "PDQHash: " << pdqHash.format() << std::endl;
  }
}

void consumer() {
  while (true) {
    std::unique_lock<std::mutex> lock(queue_mutex);
    queue_condition.wait(lock, [] { return !frame_queue.empty() || done; });
    if (frame_queue.empty() && done)
      break;
    FatFrame fatFrame = frame_queue.front();
    frame_queue.pop();
    lock.unlock();
    AVFrame* frame = fatFrame.frame;
    int frameNumber = fatFrame.frameNumber;
    hasher(false, frame, frameNumber);
    av_freep(frame->data);
    av_frame_free(&frame);
  }
}

// Get pdq hashes for selected frames every secondsPerHash
bool hashVideoFile(
    const std::string& inputVideoFileName,
    std::vector<hashing::vpdqFeature>& pdqHashes,
    bool verbose,
    const double secondsPerHash,
    const int downsampleWidth,
    const int downsampleHeight) {
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
  width = downsampleWidth;
  height = downsampleHeight;
  if (width == 0) {
    width = codecParameters->width;
  }
  if (height == 0) {
    height = codecParameters->height;
  }

  if (width == 0 || height == 0) {
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
  codecContext = avcodec_alloc_context3(codec);
  if (avcodec_parameters_to_context(codecContext, codecParameters) < 0) {
    std::cerr << "Cannot copy codec parameters to context" << std::endl;
    avformat_close_input(&formatContext);
    return false;
  }

  // Determine the number of threads to use and multithreading type
  codecContext->thread_count = 0;

  if (codec->capabilities & AV_CODEC_CAP_FRAME_THREADS) {
    codecContext->thread_type = FF_THREAD_FRAME;
  } else if (codec->capabilities & AV_CODEC_CAP_SLICE_THREADS) {
    codecContext->thread_type = FF_THREAD_SLICE;
  } else {
    codecContext->thread_count = 1;
  }

  // Open the codec context
  if (avcodec_open2(codecContext, codec, nullptr) < 0) {
    std::cerr << "Cannot open codec context" << std::endl;
    avcodec_free_context(&codecContext);
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

  frameRate = static_cast<double>(avframeRate.num) /
      static_cast<double>(avframeRate.den);
  if (frameRate == 0) {
    std::cerr << "Framerate is zero" << std::endl;
    avcodec_free_context(&codecContext);
    avformat_close_input(&formatContext);
    return false;
  }

  // Pixel format for the image passed to PDQ
  constexpr AVPixelFormat pixelFormat = AV_PIX_FMT_RGB24;

  // Create the image rescaler context
  swsContext = sws_getContext(
      codecContext->width,
      codecContext->height,
      codecContext->pix_fmt,
      width,
      height,
      pixelFormat,
      SWS_LANCZOS,
      nullptr,
      nullptr,
      nullptr);

  if (swsContext == nullptr) {
    std::cerr << "Cannot create sws context" << std::endl;
    avcodec_free_context(&codecContext);
    avformat_close_input(&formatContext);
    return false;
  }

  AVPacket* base_packet = av_packet_alloc();
  if (base_packet == nullptr) {
    std::cerr << "Cannot allocate packet" << std::endl;
    sws_freeContext(swsContext);
    avcodec_free_context(&codecContext);
    avformat_close_input(&formatContext);
    return false;
  }

  frameMod = secondsPerHash * frameRate;
  if (frameMod == 0) {
    // Avoid truncate to zero on corner-case where
    // secondsPerHash = 1 and frameRate < 1.
    frameMod = 1;
  }

  std::vector<std::thread> consumer_threads;
  for (int i = 0; i < 4; ++i) {
    // for (int i = 0; i < num_consumers; ++i) {
    consumer_threads.push_back(std::thread(consumer));
  }

  // Read frames in a loop and process them
  int ret;
  int frameNumber = 0;
  bool failed = false;
  while (av_read_frame(formatContext, base_packet) == 0) {
    AVPacket* packet = av_packet_clone(base_packet);
    // Check if the packet belongs to the video stream
    if (packet->stream_index == videoStreamIndex) {
      try {
        ret = processFrame(packet, frameNumber);
      } catch (const std::runtime_error& e) {
        std::cerr << "Processing frame failed: " << e.what() << std::endl;
        failed = true;
        break;
      }
    }
    frameNumber = ret;
    av_packet_unref(packet);
  }

  if (!failed) {
    AVPacket* packet = av_packet_clone(base_packet);
    // Flush decode buffer
    // See for more information:
    //
    // https://github.com/FFmpeg/FFmpeg/blob/6a9d3f46c7fc661b86192e922ab932495d27f953/doc/examples/decode_video.c#L182

    try {
      ret = processFrame(packet, frameNumber);
    } catch (const std::runtime_error& e) {
      std::cerr << "Flushing frame buffer failed: " << e.what() << std::endl;
      failed = true;
    }

    av_packet_unref(base_packet);
  }

  std::unique_lock<std::mutex> lock(queue_mutex);
  std::cout << "Finished decoding frames" << std::endl;
  done = true;
  lock.unlock();
  queue_condition.notify_all();
  for (auto& thread : consumer_threads) {
    thread.join();
  }

  av_packet_free(&base_packet);
  sws_freeContext(swsContext);
  avcodec_free_context(&codecContext);
  avformat_close_input(&formatContext);

  if (failed) {
    return false;
  }

  pdqHashes.assign(pdqHashes1.begin(), pdqHashes1.end());
  return true;
}

} // namespace hashing
} // namespace vpdq
} // namespace facebook
