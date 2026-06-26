Import("env")

env.Append(
    CPPDEFINES=[
        "WASHIOS_NO_EXCEPTIONS",
    ],
    CXXFLAGS=[
        "-std=gnu++17",
        "-fno-exceptions",
        "-fno-rtti",
        "-Wall",
        "-Wextra",
    ]
)
