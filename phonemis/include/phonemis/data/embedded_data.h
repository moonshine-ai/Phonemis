// Auto-generated — do not edit
#pragma once

#include <span>
#include <string_view>
#include <utility>

namespace phonemis::data {

// Lexicon: array of (word, phonemes) pairs
// Compiled in based on PHONEMIS_LANG_US or PHONEMIS_LANG_GB
std::span<const std::pair<std::string_view, std::string_view>> get_lexicon_data();

// HMM tagger model
struct HmmEntry {
  std::string_view key1;
  std::string_view key2;
  double value;
};

std::span<const std::pair<std::string_view, double>> get_hmm_start_prob();
std::span<const HmmEntry> get_hmm_emission();
std::span<const HmmEntry> get_hmm_transition();

}  // namespace phonemis::data
