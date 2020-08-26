load("//bazel/rules:java_binaries.bzl", "java_binaries")

java_library(
    name = "tools",
    srcs = glob(["*.java"]),
    deps = [
        "//src/main/java/pdqhashing/hasher:hasher",
        "//src/main/java/pdqhashing/indexer:indexer",
        "//src/main/java/pdqhashing/types:types",
        "//src/main/java/pdqhashing/utils:utils",
    ],
    visibility = ["//src:__subpackages__"],
)

java_binaries(
    testonly = 1,
    srcs = glob(["*.java"]),
    prefix = "pdqhashing.tools",
    runtime_deps = [":tools"],
)