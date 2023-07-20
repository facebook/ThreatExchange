// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <math.h>
#include <algorithm>
#include <cassert>
#include <condition_variable>
#include <cstdio>
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

// Pixel format for the image passed to PDQ
constexpr AVPixelFormat pixelFormat = AV_PIX_FMT_RGB24;

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
  // Create a frame for resizing and converting the decoded frame to RGB24
  AVFrame* targetFrame = av_frame_alloc();
  if (targetFrame == nullptr) {
    throw std::runtime_error("Cannot allocate target frame");
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
    av_frame_free(&targetFrame);
    throw std::runtime_error("Cannot fill target frame image");
  }
  return targetFrame;
}

class AVVideo {
 public:
  AVCodecContext* codecContext = nullptr;
  SwsContext* swsContext = nullptr;
  AVFormatContext* formatContext = nullptr;
  int videoStreamIndex = -1;
  int width;
  int height;
  double frameRate;

  AVVideo(const std::string filename) {
    // Open the input file
    if (avformat_open_input(
            &formatContext, filename.c_str(), nullptr, nullptr) != 0) {
      throw std::runtime_error("Cannot open video");
    }

    // Retrieve stream information
    if (avformat_find_stream_info(formatContext, nullptr) < 0) {
      avformat_close_input(&formatContext);
      throw std::runtime_error("Cannot find video stream info");
    }

    // Find the first video stream
    for (unsigned int i = 0; i < formatContext->nb_streams; ++i) {
      if (formatContext->streams[i]->codecpar->codec_type ==
          AVMEDIA_TYPE_VIDEO) {
        videoStreamIndex = i;
        break;
      }
    }

    if (videoStreamIndex == -1) {
      avformat_close_input(&formatContext);
      throw std::runtime_error("No video stream found");
    }

    // Get the video codec parameters
    AVCodecParameters* codecParameters =
        formatContext->streams[videoStreamIndex]->codecpar;

    width = codecParameters->width;
    height = codecParameters->height;
    if (width == 0 || height == 0) {
      avformat_close_input(&formatContext);
      throw std::runtime_error("Width or height equals 0");
    }

    // Find the video decoder
    const AVCodec* codec = avcodec_find_decoder(codecParameters->codec_id);
    if (!codec) {
      avformat_close_input(&formatContext);
      throw std::runtime_error("Video codec id not found");
    }

    // Create the codec context
    codecContext = avcodec_alloc_context3(codec);
    if (avcodec_parameters_to_context(codecContext, codecParameters) < 0) {
      avformat_close_input(&formatContext);
      throw std::runtime_error("Cannot copy codec parameters to context");
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
      avformat_close_input(&formatContext);
      throw std::runtime_error("Cannot open video codec context");
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
      avformat_close_input(&formatContext);
      throw std::runtime_error("Video framerate is zero");
    }
  }
  ~AVVideo() {
    if (codecContext != nullptr)
      avcodec_free_context(&codecContext);
    if (swsContext != nullptr)
      sws_freeContext(swsContext);
    if (formatContext != nullptr) {
      avformat_close_input(&formatContext);
    }
  }
};

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
  bool done_hashing = false;

  std::vector<std::thread> consumer_threads;
  unsigned int num_consumers = std::thread::hardware_concurrency();

  std::unique_ptr<AVVideo> video;
  int frameMod;

  bool verbose = false;

  vpdqHasher(std::unique_ptr<AVVideo> video) : video(std::move(video)) {}

  // Decode and add vpdqFeature to the hashes vector
  // Returns the number of frames processed (this is can be more than 1!)
  int processFrame(AVPacket* packet, int frameNumber) {
    AVFrame* frame = av_frame_alloc();
    assert(frame != nullptr);
    // TODO: check for frame good alloc
    AVFrame* targetFrame;
    try {
      targetFrame = createFrame(video->width, video->height);
    } catch (const std::runtime_error& e) {
      std::cerr << e.what() << std::endl;
      throw;
    }
    // Send the packet to the decoder
    int ret = avcodec_send_packet(video->codecContext, packet) < 0;
    // std::cout << codecContext->frame_num << std::endl;
    if (ret < 0) {
      throw std::runtime_error("Cannot send packet to decoder");
    }

    // Receive the decoded frame
    while (ret >= 0) {
      ret = avcodec_receive_frame(video->codecContext, frame);
      if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
        break;
      } else if (ret < 0) {
        throw std::runtime_error("Cannot receive frame from decoder");
      }

      if (frameNumber % frameMod == 0) {
        // Resize the frame and convert to RGB24
        sws_scale(
            video->swsContext,
            frame->data,
            frame->linesize,
            0,
            video->codecContext->height,
            targetFrame->data,
            targetFrame->linesize);

        std::unique_lock<std::mutex> lock(queue_mutex);
        AVFrame* newTargetFrame = createFrame(video->width, video->height);
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

  void hasher(AVFrame* frame, int frameNumber) {
    assert(frame != nullptr);
    assert(frame->height != 0 && frame->width != 0);
    int quality;
    pdq::hashing::Hash256 pdqHash;

    std::unique_ptr<vpdq::hashing::AbstractFrameBufferHasher> phasher =
        vpdq::hashing::FrameBufferHasherFactory::createFrameHasher(
            frame->height, frame->width);

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
        static_cast<double>(frameNumber) / video->frameRate};
    pdqHashes.push_back(feature);
    if (verbose) {
      std::cout << "PDQHash: " << pdqHash.format() << std::endl;
    }
  }

  void consumer() {
    while (true) {
      std::unique_lock<std::mutex> lock(queue_mutex);
      queue_condition.wait(
          lock, [this] { return !frame_queue.empty() || done_hashing; });
      if (frame_queue.empty() && done_hashing)
        break;
      FatFrame fatFrame = frame_queue.front();
      frame_queue.pop();
      lock.unlock();
      AVFrame* frame = fatFrame.frame;
      int frameNumber = fatFrame.frameNumber;
      hasher(frame, frameNumber);
      av_freep(frame->data);
      if (frame != nullptr)
        av_frame_free(&frame);
    }
  }

  void start() {
    auto total_frames = frame_queue.size();
    if (verbose) {
      std::cout << "Started hashing " << total_frames << " frames."
                << std::endl;
    }

    // Hash the frames
    for (decltype(num_consumers) i = 0; i < num_consumers; ++i) {
      consumer_threads.push_back(
          std::thread(std::bind(&vpdqHasher::consumer, this)));
    }

    std::unique_lock<std::mutex> lock(queue_mutex);
    done_hashing = true;
    lock.unlock();
    queue_condition.notify_all();
    for (auto& thread : consumer_threads) {
      thread.join();
    }

    if (verbose) {
      std::cout << "Finished hashing " << total_frames << " frames."
                << std::endl;
    }
  }
};

// Get pdq hashes for selected frames every secondsPerHash
bool hashVideoFile(
    const std::string& inputVideoFileName,
    std::vector<hashing::vpdqFeature>& pdqHashes,
    bool verbose,
    const double secondsPerHash,
    const int downsampleWidth,
    const int downsampleHeight) {
  auto video = std::make_unique<AVVideo>(inputVideoFileName);

  // If downsampleWidth or downsampleHeight is 0,
  // then use the video's original dimensions
  if (downsampleWidth > 0) {
    video->width = downsampleWidth;
  }
  if (downsampleHeight > 0) {
    video->height = downsampleHeight;
  }

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

  // Create the image rescaler context
  video->swsContext = sws_getContext(
      video->codecContext->width,
      video->codecContext->height,
      video->codecContext->pix_fmt,
      video->width,
      video->height,
      pixelFormat,
      SWS_LANCZOS,
      nullptr,
      nullptr,
      nullptr);

  if (video->swsContext == nullptr) {
    std::cerr << "Cannot create sws context" << std::endl;
    return false;
  }

  AVPacket* packet = av_packet_alloc();
  if (packet == nullptr) {
    std::cerr << "Cannot allocate packet" << std::endl;
    return false;
  }

  vpdqHasher hasher(std::move(video));
  hasher.verbose = verbose;

  hasher.frameMod = secondsPerHash * hasher.video->frameRate;
  if (hasher.frameMod == 0) {
    // Avoid truncate to zero on corner-case where
    // secondsPerHash = 1 and frameRate < 1.
    hasher.frameMod = 1;
  }

  // Read frames in a loop and process them
  int ret = 0;
  int frameNumber = 0;
  bool failed = false;
  while (av_read_frame(hasher.video->formatContext, packet) == 0) {
    // Check if the packet belongs to the video stream
    if (packet->stream_index == hasher.video->videoStreamIndex) {
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

  av_packet_free(&packet);

  if (failed) {
    return false;
  }

  // Hash the frames
  hasher.start();

  // Sort out of order frames by frameNumber
  std::sort(
      hasher.pdqHashes.begin(),
      hasher.pdqHashes.end(),
      [](const vpdqFeature& a, const vpdqFeature& b) {
        return a.frameNumber < b.frameNumber;
      });

  // Copy the hashes to the input vector
  pdqHashes.assign(hasher.pdqHashes.begin(), hasher.pdqHashes.end());
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
