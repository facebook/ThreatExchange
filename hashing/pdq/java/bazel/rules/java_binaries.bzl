def java_binaries(srcs, prefix, **kwargs):
    """Create multiple java_binary() targets using the same configuration for all names srcs.

    This is useful if you have a package full of scripts which are all binaries which require
    the same set of dependencies.

    For example:

        load("//bazel/rules:java_binaries.bzl", "java_binaries")

        java_binaries(
            srcs = glob(["*.java"]),
            prefix = "com.pinterest.contentsafety.tools",
            runtime_deps = [":tools"],
            testonly = 1,
        )
    """
    for src in srcs:
        if not src.endswith('.java'):
            fail("{} doesn't end with .java".format(src))
        parts = src.split('/')
        filename = parts[-1]
        classname = filename.rstrip('.java')
        native.java_binary(
            name = classname,
            main_class = "{}.{}".format(prefix, classname),
            **kwargs
        )
