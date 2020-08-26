// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// Step 1 of TMK 3-stage hashing pipeline:
// * vid2vstr (or ffmpeg.exe): .mp4 file to .vstr decoded stream
//   Note this can also be done using ffmpeg.
// * vstr2feat: .vstr file to .feat list of frame-featue vectors
// * feat2tmk: .feat file to .tmk list of TMK cosine/sine features
// ================================================================

#include <common/config/Flags.h>
#include <common/init/Init.h>
#include <mediaio/CvMediaReader.h>
#include <opencv2/opencv.hpp>
#include <tmk/cpp/io/tmkio.h>
#include <tmk/cpp/raster/rasterwriters.h>
#include <tmk/cpp/raster/timeresamplers.h>

using namespace std;
using namespace facebook;
using namespace facebook::tmk;
using namespace facebook::tmk::raster;

DEFINE_string(
    output_stream_file_name,
    "",
    "Output file name for decoded frames. Defaults to stdout if omitted.");

DEFINE_int32(
    output_frames_per_second,
    TMK_DEFAULT_FRAMES_PER_SECOND,
    "Number of frames per second on output. "
    "May differ from video-file frame rate.");

DEFINE_int32(
    num_threads,
    MediaBase::AUTO_SELECT_THREAD_COUNT,
    "number of threads to use, -1=default, 0=auto");

DEFINE_bool(
    no_rotate,
    false,
    "Do not unrotate rotated storage to recover display orientation."
    " For test/debug only.");

// Status codes for video hashing shell contract
enum class VideoDecodingStatus {
  OK = 0,
  FATAL = 1,
  FILE_NOT_FOUND = 4,
};

CvMediaReader* getCvMediaReaderAndMetadata(
    char* argv0,
    string inputVideoFileName,
    int numThreads,
    int& storageFrameHeight,
    int& storageFrameWidth,
    double& inputFramesPerSecond,
    RasterTransformation& rasterTransformation,
    VideoDecodingStatus& exit_rc);

// ----------------------------------------------------------------
void usage(char* argv0, int exit_rc) {
  FILE* fp = (exit_rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s [options] [input file name]\n", argv0);
  fprintf(fp, "Options:\n");
  fprintf(fp, "--output_stream_file_name {x}\n");
  fprintf(fp, "--output_frames_per_second {n}\n");
  fprintf(fp, "--num_threads {n}\n");
  exit(exit_rc);
}

// ----------------------------------------------------------------
int main(int argc, char** argv) {
  initFacebook(&argc, &argv);

  if (argc < 2) {
    usage(argv[0], 1);
  }
  string inputVideoFileName = argv[1];
  int outputFramesPerSecond = FLAGS_output_frames_per_second;
  string outputStreamFileName = FLAGS_output_stream_file_name;
  FILE* outputFp = stdout;
  if (outputStreamFileName != "") {
    outputFp = facebook::tmk::io::openFileOrDie(
        outputStreamFileName.c_str(), (char*)"wb", argv[0]);
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Acquire video-reader object and obtain video metadata.
  int storageFrameHeight;
  int storageFrameWidth;
  double inputFramesPerSecond;
  RasterTransformation rasterTransformation;
  VideoDecodingStatus exit_rc = VideoDecodingStatus::FATAL;

  CvMediaReader* preader = getCvMediaReaderAndMetadata(
      argv[0],
      inputVideoFileName,
      FLAGS_num_threads,
      storageFrameHeight,
      storageFrameWidth,
      inputFramesPerSecond,
      rasterTransformation,
      exit_rc);

  if (preader == nullptr) {
    // Error message already printed out
    return (int)exit_rc;
  }
  double inputSecondsPerFrame = 1.0 / inputFramesPerSecond;

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  std::chrono::time_point<std::chrono::system_clock> startOuter =
      std::chrono::system_clock::now();
  fprintf(stderr, "%s: %s ENTER\n", argv[0], inputVideoFileName.c_str());
  ;

  // ----------------------------------------------------------------
  // Write output frames

  // Frame storage can be rotated from the way it was acquired.
  AbstractRasterWriter* pframeWriter = RasterWriterFactory::createFrameWriter(
      FLAGS_no_rotate ? RasterTransformation::NEEDS_NO_TRANSFORMATION
                      : rasterTransformation,
      storageFrameHeight,
      storageFrameWidth);

  // Output frames-per-second can differ from what's in the input video.
  auto ptimeResampler =
      facebook::tmk::raster::TimeResamplerFactory::createTimeResampler(
          inputFramesPerSecond, outputFramesPerSecond);

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Write output header
  if (!facebook::tmk::io::writeDecodedVideoStreamFileHeader(
          outputFp,
          pframeWriter->getDisplayFrameHeight(),
          pframeWriter->getDisplayFrameWidth(),
          outputFramesPerSecond,
          argv[0])) {
    perror("fwrite");
    return (int)VideoDecodingStatus::FATAL;
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Loop over input frames.
  exit_rc = VideoDecodingStatus::OK;
  int inputFrameNumber = 0;
  int outputFrameNumber = 0;
  do {
    cv::Mat3b img(storageFrameHeight, storageFrameWidth);
    if (!preader->getFrameRgb(img)) {
      break;
    }
    // Note: imwrite("filenamegoeshere.png", img) to get frame-taps.
    // if (inputFrameNumber == 4) { imwrite("tap4.png", img); }
    double inputFrameTime = inputFrameNumber * inputSecondsPerFrame;

    if ((inputFrameNumber % 100) == 0) {
      fprintf(
          stderr,
          "%s: at frame %d timestamp %.3lf\n",
          argv[0],
          inputFrameNumber,
          inputFrameTime);
    }

    int emitCount = ptimeResampler->numberToEmit();
    for (int j = 0; j < emitCount; j++) {
      size_t fwrite_rc = pframeWriter->writeRGBTriples(img.ptr(0), outputFp);

      if (fwrite_rc != storageFrameWidth * storageFrameHeight) {
        perror("fwrite");
        fprintf(
            stderr,
            "%s: write failure at input frame number %d"
            " output frame number %d.\n",
            argv[0],
            inputFrameNumber,
            outputFrameNumber);
        fprintf(
            stderr,
            "Expected to write %d triples; write %d.\n",
            storageFrameWidth * storageFrameHeight,
            (int)fwrite_rc);
        exit_rc = VideoDecodingStatus::FATAL;
        break;
      }
      fflush(outputFp);
    }

    inputFrameNumber++;
  } while (preader->seekNextFrame());

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Clean up

  if (!preader->close()) {
    fprintf(stderr, "%s: stream-close failure\n", argv[0]);
  }
  delete preader;

  if (outputFp != stdout) {
    if (fclose(outputFp) != 0) {
      perror("fclose");
      fprintf(
          stderr,
          "%s: could not close \"%s\" for write.\n",
          argv[0],
          outputStreamFileName.c_str());
      exit(1);
    }
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  fprintf(stderr, "%s: %s EXIT\n", argv[0], inputVideoFileName.c_str());
  std::chrono::time_point<std::chrono::system_clock> endOuter =
      std::chrono::system_clock::now();
  std::chrono::duration<double> elapsedSecondsOuter = endOuter - startOuter;
  fprintf(
      stderr,
      "%s: SECONDS END TO END = %.3lf\n",
      argv[0],
      elapsedSecondsOuter.count());

  return (int)exit_rc;
}

// ----------------------------------------------------------------
CvMediaReader* getCvMediaReaderAndMetadata(
    char* argv0,
    string inputVideoFileName,
    int numThreads,
    int& storageFrameHeight,
    int& storageFrameWidth,
    double& inputFramesPerSecond,
    RasterTransformation& rasterTransformation,
    VideoDecodingStatus& exit_rc) {
  CvMediaReader* preader = new CvMediaReader();
  if (!preader->setThreadCount(numThreads)) {
    fprintf(stderr, "%s: could not set thread count on preader.\n", argv0);
    delete preader;
    exit_rc = VideoDecodingStatus::FATAL;
    return nullptr;
  }
  if (!preader->open(inputVideoFileName)) {
    fprintf(
        stderr,
        "%s: could not open filename = %s.\n",
        argv0,
        inputVideoFileName.c_str());
    delete preader;
    exit_rc = VideoDecodingStatus::FILE_NOT_FOUND;
    return nullptr;
  }

  // Obtain video metadata
  storageFrameHeight = preader->height();
  storageFrameWidth = preader->width();

  int rateNumer = -1, rateDenom = 1;
  preader->frameRate(rateNumer, rateDenom);
  inputFramesPerSecond = (float)rateNumer / (float)rateDenom;
  if (inputFramesPerSecond <= 0) {
    fprintf(
        stderr,
        "%s: non-positive input frame rate %.6lf found for \"%s\".\n",
        argv0,
        inputFramesPerSecond,
        inputVideoFileName.c_str());
    delete preader;
    exit_rc = VideoDecodingStatus::FATAL;
    return nullptr;
  }

  // The CvMediaReader transform and the RasterWriter transformations
  // are in 1-1 correspondence. However I do not want to have the tmk/raster
  // package bring in the *entire* mediaio/ package *solely* for the sake
  // of defining a single enum. Hence the remapping of enums here.
  MediaTransformation mediaTransformation = preader->getTransformation();
  rasterTransformation = RasterTransformation::NEEDS_NO_TRANSFORMATION;

  // Report
  fprintf(
      stderr,
      "%s:[vid2vstr] Filename       = %s\n",
      argv0,
      inputVideoFileName.c_str());
  fprintf(
      stderr, "%s:[vid2vstr] Storage height = %d\n", argv0, storageFrameHeight);
  fprintf(
      stderr, "%s:[vid2vstr] Storage width  = %d\n", argv0, storageFrameWidth);
  fprintf(
      stderr,
      "%s:[vid2vstr] FPS            = %d/%d = %.6lf\n",
      argv0,
      rateNumer,
      rateDenom,
      inputFramesPerSecond);

  switch (mediaTransformation) {
    case MediaTransformation::NOT_TRANSFORMED:
      rasterTransformation = RasterTransformation::NEEDS_NO_TRANSFORMATION;
      fprintf(stderr, "%s:[vid2vstr] Rotation = none\n", argv0);
      break;
    case MediaTransformation::ROTATED_CW_90:
      rasterTransformation = RasterTransformation::NEEDS_ROTATE_CW_90;
      fprintf(stderr, "%s:[vid2vstr] Rotation = CW90\n", argv0);
      // Frames were rotated counterclockwise 90 degrees from acquisition to
      // storage. They need to be rotated CW by 90 to undo that.
      break;
    case MediaTransformation::ROTATED_CCW_90:
      rasterTransformation = RasterTransformation::NEEDS_ROTATE_CCW_90;
      fprintf(stderr, "%s:[vid2vstr] Rotation = CCW90\n", argv0);
      // Frames were rotated clockwise 90 degrees from acquisition to
      // storage. They need to be rotated CCW by 90 to undo that.
      break;
    case MediaTransformation::ROTATED_180:
      rasterTransformation = RasterTransformation::NEEDS_ROTATE_180;
      // Frames were rotated 180 degrees from acquisition to storage.
      // That needs to be undone.
      fprintf(stderr, "%s:[vid2vstr] Rotation = 180\n", argv0);
      break;
    default:
      fprintf(stderr, "%s:[vid2vstr] Rotation = ???\n", argv0);
      break;
  }

  exit_rc = VideoDecodingStatus::OK;
  return preader;
}
