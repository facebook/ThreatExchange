// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <math.h>
#include <stdio.h>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <vpdq/cpp/hashing/bufferhasher.h>
#include <vpdq/cpp/hashing/filehasher.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>

using namespace std;

namespace facebook {
namespace vpdq {
namespace hashing {

#ifndef CYTHON

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/frame.h>
#include <libavutil/imgutils.h>
#include <libavutil/mem.h>
#include <libswscale/swscale.h>
}

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
  FILE* output = fopen(filename, "wb");
  for (int y = 0; y < frame->height; y++) {
    fwrite(
        frame->data[0] + y * frame->linesize[0], 1, frame->width * 3, output);
  }
  printf(
      "Saved frame to file %s with dimensions %dx%d\n",
      filename,
      frame->width,
      frame->height);
  fclose(output);
}

// Decode and add vpdqFeature to the hashes vector
// Returns the number of frames processed or -1 if failure
static int processFrame(
    AVPacket* packet,
    AVFrame* frame,
    AVFrame* targetFrame,
    SwsContext* swsContext,
    AVCodecContext* codecContext,
    unique_ptr<vpdq::hashing::AbstractFrameBufferHasher>& phasher,
    vector<hashing::vpdqFeature>& pdqHashes,
    double framesPerSec,
    bool verbose,
    int frameNumber,
    int frameMod) {
  // Send the packet to the decoder
  int ret = avcodec_send_packet(codecContext, packet) < 0;
  if (ret < 0) {
    fprintf(stderr, "Error: Cannot send packet to decoder\n");
    return -1;
  }

  // Receive the decoded frame
  while (ret >= 0) {
    ret = avcodec_receive_frame(codecContext, frame);
    if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
      break;
    } else if (ret < 0) {
      fprintf(stderr, "Error: Cannot receive frame from decoder\n");
      return -1;
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
      // Call pdqHasher to hash the frame
      int quality;
      pdq::hashing::Hash256 pdqHash;
      if (!phasher->hashFrame(targetFrame->data[0], pdqHash, quality)) {
        fprintf(
            stderr,
            "%d: failed to hash frame buffer. Frame width or height smaller than the minimum hashable dimension.\n",
            frameNumber);
        return -1;
      }

      //  Write frame to file here for debugging:
      //  saveFrameToFile(targetFrame, "frame.rgb");

      // Append vpdq feature to pdqHashes vector
      pdqHashes.push_back(
          {pdqHash, frameNumber, quality, (double)frameNumber / framesPerSec});
      if (verbose) {
        printf("PDQHash: %s\n", pdqHash.format().c_str());
      }
    }
    frameNumber += 1;
  }
  return frameNumber;
}

// Get pdq hashes for selected frames every secondsPerHash
bool hashVideoFile(
    const string& inputVideoFileName,
    vector<hashing::vpdqFeature>& pdqHashes,
    const string& ffmpegPath,
    bool verbose,
    const double secondsPerHash,
    const int width,
    const int height,
    const double framesPerSec,
    const char* argv0) {
  std::unique_ptr<vpdq::hashing::AbstractFrameBufferHasher> phasher =
      vpdq::hashing::FrameBufferHasherFactory::createFrameHasher(height, width);
  if (phasher == nullptr) {
    fprintf(stderr, "Error: Phasher is null\n");
    return false;
  }

  // Open the input file
  AVFormatContext* formatContext = nullptr;
  if (avformat_open_input(
          &formatContext, inputVideoFileName.c_str(), nullptr, nullptr) != 0) {
    fprintf(stderr, "Error: Cannot open the video\n");
    return false;
  }

  // Retrieve stream information
  if (avformat_find_stream_info(formatContext, nullptr) < 0) {
    fprintf(stderr, "Error: Cannot find stream info\n");
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
    fprintf(stderr, "Error: No video stream found\n");
    avformat_close_input(&formatContext);
    return false;
  }

  // Get the video codec parameters
  AVCodecParameters* codecParameters =
      formatContext->streams[videoStreamIndex]->codecpar;

  // Find the video decoder
  const AVCodec* codec = avcodec_find_decoder(codecParameters->codec_id);
  if (!codec) {
    fprintf(stderr, "Error: Codec decoder not found\n");
    avformat_close_input(&formatContext);
    return false;
  }

  // Create the codec context
  AVCodecContext* codecContext = avcodec_alloc_context3(codec);
  if (avcodec_parameters_to_context(codecContext, codecParameters) < 0) {
    fprintf(stderr, "Error: Failed to copy codec parameters to context\n");
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
    fprintf(stderr, "Error: Failed to open codec\n");
    avcodec_free_context(&codecContext);
    avformat_close_input(&formatContext);
    return false;
  }

  // Create the output frame
  AVFrame* frame = av_frame_alloc();
  if (frame == nullptr) {
    avcodec_free_context(&codecContext);
    avformat_close_input(&formatContext);
    return false;
  }

  // Pixel format for the image passed to PDQ
  constexpr AVPixelFormat pixelFormat = AV_PIX_FMT_RGB24;

  // Create a frame for resizing and converting the decoded frame to RGB24
  AVFrame* targetFrame = av_frame_alloc();
  if (targetFrame == nullptr) {
    av_frame_free(&frame);
    avcodec_free_context(&codecContext);
    avformat_close_input(&formatContext);
    return false;
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
    fprintf(stderr, "Error: Failed to allocate target frame\n");
    av_frame_free(&targetFrame);
    av_frame_free(&frame);
    avcodec_free_context(&codecContext);
    avformat_close_input(&formatContext);
  }

  // Create the image rescaler context
  SwsContext* swsContext = sws_getContext(
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
    fprintf(stderr, "Error: Failed to create sws context\n");
    av_freep(targetFrame->data);
    av_frame_free(&targetFrame);
    av_frame_free(&frame);
    avcodec_free_context(&codecContext);
    avformat_close_input(&formatContext);
    return false;
  }

  AVPacket* packet = av_packet_alloc();
  if (packet == nullptr) {
    fprintf(stderr, "Error: Failed to allocate packet\n");
    sws_freeContext(swsContext);
    av_freep(targetFrame->data);
    av_frame_free(&targetFrame);
    av_frame_free(&frame);
    avcodec_free_context(&codecContext);
    avformat_close_input(&formatContext);
    return false;
  }

  int frameMod = secondsPerHash * framesPerSec;
  if (frameMod == 0) {
    // Avoid truncate to zero on corner-case with secondsPerHash = 1
    // and framesPerSec < 1.

    frameMod = 1;
  }

  // Read frames in a loop and process them
  int frameNumber = 0;
  int ret = 0;
  bool failed = false;
  while (av_read_frame(formatContext, packet) == 0) {
    // Check if the packet belongs to the video stream
    if (packet->stream_index == videoStreamIndex) {
      ret = processFrame(
          packet,
          frame,
          targetFrame,
          swsContext,
          codecContext,
          phasher,
          pdqHashes,
          framesPerSec,
          verbose,
          frameNumber,
          frameMod);

      if (ret == -1) {
        fprintf(stderr, "Error: Cannot process frame\n");
        failed = true;
        av_packet_unref(packet);
        break;
      }

      frameNumber = ret;
    }

    av_packet_unref(packet);
  }

  if (!failed) {
    // Flush decode buffer
    // See for more information:
    // https://github.com/FFmpeg/FFmpeg/blob/6a9d3f46c7fc661b86192e922ab932495d27f953/doc/examples/decode_video.c#L182

    ret = processFrame(
        packet,
        frame,
        targetFrame,
        swsContext,
        codecContext,
        phasher,
        pdqHashes,
        framesPerSec,
        verbose,
        frameNumber,
        frameMod);

    if (ret == -1) {
      failed = true;
      fprintf(stderr, "Error: Cannot process frame\n");
    }

    av_packet_unref(packet);
  }

  av_packet_free(&packet);
  sws_freeContext(swsContext);
  av_freep(targetFrame->data);
  av_frame_free(&targetFrame);
  av_frame_free(&frame);
  avcodec_free_context(&codecContext);
  avformat_close_input(&formatContext);

  if (failed) {
    return false;
  }

  return true;
}
#endif

// Get pdq hashes for selected frames every secondsPerHash
// The return boolean represents whether the hashing process
// is successful or not.
// This uses FFmpeg which does not require linking to libav* libraries.
bool hashVideoFileFFMPEG(
    const string& inputVideoFileName,
    vector<hashing::vpdqFeature>& pdqHashes,
    const string& ffmpegPath,
    bool verbose,
    const double secondsPerHash,
    const int width,
    const int height,
    const double framesPerSec,
    const char* argv0) {
  stringstream ss;

  ss << quoted(inputVideoFileName);
  string escapedInputVideoFileName = ss.str();
  // FFMPEG command to process the downsampled video

  string ffmpegLogLevel =
      verbose ? "" : "-loglevel error -hide_banner -nostats";
  string command = ffmpegPath + " " + ffmpegLogLevel + " -nostdin -i " +
      escapedInputVideoFileName + " -s " + to_string(width) + ":" +
      to_string(height) + " -an -f rawvideo -c:v rawvideo -pix_fmt rgb24" +
      " pipe:1";
  FILE* inputFp = popen(command.c_str(), "r");
  if (inputFp == nullptr) {
    fprintf(stderr, "%s: ffmpeg to generate video stream failed\n", argv0);
    return false;
  }

  bool eof = false;

  // Create the PDQ Frame Buffer Hasher
  std::unique_ptr<vpdq::hashing::AbstractFrameBufferHasher> phasher =
      vpdq::hashing::FrameBufferHasherFactory::createFrameHasher(height, width);
  if (phasher == nullptr) {
    fprintf(stderr, "Error: Phasher is null");
    pclose(inputFp);
    return false;
  }

  // Create a Frame Buffer to reuse everytime for hashing
  int numRGBTriples = height * width;
  int fno = 0;
  unique_ptr<uint8_t[]> rawFrameBuffer(new uint8_t[numRGBTriples * 3]);
  // Intentional floor operation calculate frameMod as an integer
  int frameMod = secondsPerHash * framesPerSec;
  if (frameMod == 0) {
    // Avoid truncate to zero on corner-case with secondsPerHash = 1
    // and framesPerSec < 1.
    frameMod = 1;
  }
  // Loop through the video frames
  while (!feof(inputFp)) {
    size_t fread_rc = fread(rawFrameBuffer.get(), 3, numRGBTriples, inputFp);
    if (fread_rc == 0) {
      eof = true;
    }
    if (eof) {
      break;
    }
    pdq::hashing::Hash256 pdqHash;
    if (fno % frameMod == 0) {
      if (verbose) {
        printf("selectframe %d\n", fno);
      }
      // Call pdqHasher to hash the frame
      int quality;
      if (!phasher->hashFrame(rawFrameBuffer.get(), pdqHash, quality)) {
        fprintf(
            stderr,
            "%s: failed to hash frame buffer. Frame width or height smaller than minimum hashable dimension. %d.\n",
            argv0,
            fno);
        pclose(inputFp);
        return false;
      }
      // Push to pdqHashes vector
      pdqHashes.push_back({pdqHash, fno, quality, (double)fno / framesPerSec});
      if (verbose) {
        printf("PDQHash: %s \n", pdqHash.format().c_str());
      }
    }
    fno++;
    if (fread_rc != numRGBTriples) {
      perror("fread");
      fprintf(
          stderr,
          "Expected %d RGB triples; got %d\n",
          numRGBTriples,
          (int)fread_rc);
    }
  }
  pclose(inputFp);
  return true;
}

} // namespace hashing
} // namespace vpdq
} // namespace facebook
