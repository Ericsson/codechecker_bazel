# src/extensions.bzl
load(
    "//src:tools.bzl",
    "register_default_codechecker",
    "register_default_python_toolchain",
)

def _initialize_tools_impl(ctx):
    # WARNING: See note below about legacy macros!
    register_default_python_toolchain()
    register_default_codechecker()

# Define the extension here
initialize_tools = module_extension(
    implementation = _initialize_tools_impl,
)
