cmake_minimum_required(VERSION 3.10)
project(phonemis VERSION 1.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Language selection: US (default) or GB
set(PHONEMIS_LANG "US" CACHE STRING "Language variant: US or GB")
set_property(CACHE PHONEMIS_LANG PROPERTY STRINGS US GB)

# Source files (core library, excluding generated data)
file(GLOB CORE_SOURCE_FILES "phonemis/src/*.cpp")

# Select the correct lexicon data file based on language
if(PHONEMIS_LANG STREQUAL "GB")
  set(LEXICON_SOURCE "phonemis/src/data/lexicon_gb.cpp")
else()
  set(LEXICON_SOURCE "phonemis/src/data/lexicon_us.cpp")
endif()
set(HMM_SOURCE "phonemis/src/data/hmm_data.cpp")

# Include directories
include_directories(phonemis/include)

# Build static library
add_library(phonemis STATIC
  ${CORE_SOURCE_FILES}
  ${LEXICON_SOURCE}
  ${HMM_SOURCE}
)
target_compile_definitions(phonemis PUBLIC PHONEMIS_LANG_${PHONEMIS_LANG})

# Build test executables
add_executable(test_everything test/test_everything.cpp)
target_link_libraries(test_everything phonemis)

add_executable(test_preprocessor test/test_preprocessor.cpp)
target_link_libraries(test_preprocessor phonemis)

add_executable(test_tokenizer test/test_tokenizer.cpp)
target_link_libraries(test_tokenizer phonemis)

add_executable(test_pipeline test/test_pipeline.cpp)
target_link_libraries(test_pipeline phonemis)
