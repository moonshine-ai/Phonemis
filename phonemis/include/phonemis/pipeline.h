#pragma once

#include "preprocessor/tools.h"
#include "tokenizer/tokenize.h"
#include "tagger/tagger.h"
#include "phonemizer/phonemizer.h"
#include <memory>

namespace phonemis {

using phonemizer::Lang;
using phonemizer::Phonemizer;
using tagger::Tagger;

// #### Main phonemization pipeline
// Manages all the phonemization parts, from preprocessing, through
// tokenization and tagging to final Phonemizer call.
// Tagger and Lexicon .json data files are theoretically optional, but
// skipping these arguments will significantly impact the phonemization quality.
class Pipeline {
public:
  explicit Pipeline(Lang language);
  
  std::u32string process(const std::string& text);

private:
  Lang language_;

  // Pipeline subcomponents
  std::unique_ptr<Phonemizer> phonemizer_ = nullptr;
  std::unique_ptr<Tagger> tagger_ = nullptr;
};

} // namespace phonemis