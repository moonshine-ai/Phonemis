#!/usr/bin/env python3
"""
Convert Phonemis JSON data files into C++ source files that can be
compiled directly into the binary, removing the runtime JSON dependency.

Generates:
  phonemis/src/data/lexicon_us.cpp   — US English dictionary
  phonemis/src/data/lexicon_gb.cpp   — GB English dictionary
  phonemis/src/data/hmm_data.cpp     — HMM tagger model
  phonemis/include/phonemis/data/embedded_data.h — declarations

Each dictionary is ~485K entries. Rather than putting them in a header
(which would slow every TU that includes it), they go in .cpp files that
compile into the static library, guarded by preprocessor flags.
"""
import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_OUT = PROJECT_ROOT / "phonemis" / "src" / "data"
INC_OUT = PROJECT_ROOT / "phonemis" / "include" / "phonemis" / "data"


def escape_cpp_string(s: str) -> str:
    """Escape a string for use inside a C++ raw string or regular string literal."""
    # Use regular string literals with proper escaping
    result = []
    for ch in s:
        if ch == '\\':
            result.append('\\\\')
        elif ch == '"':
            result.append('\\"')
        elif ch == '\n':
            result.append('\\n')
        elif ch == '\t':
            result.append('\\t')
        else:
            result.append(ch)
    return ''.join(result)


def generate_lexicon_cpp(dict_path: Path, lang_guard: str, output_path: Path):
    """Generate a .cpp file with the dictionary as a function returning
    a vector of pairs, which the Lexicon constructor iterates."""
    print(f"  Loading {dict_path.name}...")
    with open(dict_path, "r", encoding="utf-8") as f:
        dictionary = json.load(f)

    print(f"  Writing {output_path.name} ({len(dictionary)} entries)...")

    with open(output_path, "w", encoding="utf-8") as out:
        out.write(f'// Auto-generated from {dict_path.name} — do not edit\n')
        out.write(f'#include <phonemis/data/embedded_data.h>\n\n')
        out.write(f'#ifdef {lang_guard}\n\n')
        out.write(f'namespace phonemis::data {{\n\n')

        # Write as a function that returns a span over a static array
        out.write(f'static const std::pair<std::string_view, std::string_view> kLexiconEntries[] = {{\n')

        for i, (word, phonemes) in enumerate(dictionary.items()):
            w_esc = escape_cpp_string(word)
            p_esc = escape_cpp_string(phonemes)
            out.write(f'  {{"{w_esc}", "{p_esc}"}},\n')

        out.write(f'}};\n\n')
        out.write(f'std::span<const std::pair<std::string_view, std::string_view>> get_lexicon_data() {{\n')
        out.write(f'  return kLexiconEntries;\n')
        out.write(f'}}\n\n')
        out.write(f'}}  // namespace phonemis::data\n\n')
        out.write(f'#endif  // {lang_guard}\n')


def generate_hmm_cpp(hmm_path: Path, output_path: Path):
    """Generate a .cpp file with the HMM model data."""
    print(f"  Loading {hmm_path.name}...")
    with open(hmm_path, "r", encoding="utf-8") as f:
        hmm = json.load(f)

    start_prob = hmm["start_prob"]
    emission = hmm["emission"]
    transition = hmm["transition"]

    total_emission = sum(len(v) for v in emission.values())
    total_transition = sum(len(v) for v in transition.values())
    print(f"  Writing {output_path.name} ({len(start_prob)} tags, "
          f"{total_emission} emission pairs, {total_transition} transition pairs)...")

    with open(output_path, "w", encoding="utf-8") as out:
        out.write(f'// Auto-generated from {hmm_path.name} — do not edit\n')
        out.write(f'#include <phonemis/data/embedded_data.h>\n\n')
        out.write(f'namespace phonemis::data {{\n\n')

        # Start probabilities
        out.write(f'static const std::pair<std::string_view, double> kStartProb[] = {{\n')
        for tag, prob in start_prob.items():
            out.write(f'  {{"{escape_cpp_string(tag)}", {prob!r}}},\n')
        out.write(f'}};\n\n')

        # Emission probabilities — flat array of (tag, word, prob) triples
        out.write(f'static const HmmEntry kEmission[] = {{\n')
        for tag, words in emission.items():
            tag_esc = escape_cpp_string(tag)
            for word, prob in words.items():
                w_esc = escape_cpp_string(word)
                out.write(f'  {{"{tag_esc}", "{w_esc}", {prob!r}}},\n')
        out.write(f'}};\n\n')

        # Transition probabilities — flat array of (from_tag, to_tag, prob) triples
        out.write(f'static const HmmEntry kTransition[] = {{\n')
        for from_tag, to_tags in transition.items():
            ft_esc = escape_cpp_string(from_tag)
            for to_tag, prob in to_tags.items():
                tt_esc = escape_cpp_string(to_tag)
                out.write(f'  {{"{ft_esc}", "{tt_esc}", {prob!r}}},\n')
        out.write(f'}};\n\n')

        # Accessor functions
        out.write(f'std::span<const std::pair<std::string_view, double>> get_hmm_start_prob() {{\n')
        out.write(f'  return kStartProb;\n')
        out.write(f'}}\n\n')
        out.write(f'std::span<const HmmEntry> get_hmm_emission() {{\n')
        out.write(f'  return kEmission;\n')
        out.write(f'}}\n\n')
        out.write(f'std::span<const HmmEntry> get_hmm_transition() {{\n')
        out.write(f'  return kTransition;\n')
        out.write(f'}}\n\n')
        out.write(f'}}  // namespace phonemis::data\n')


def generate_header(output_path: Path):
    """Generate the shared header file with declarations."""
    print(f"  Writing {output_path.name}...")

    with open(output_path, "w", encoding="utf-8") as out:
        out.write("""// Auto-generated — do not edit
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
""")


def main():
    print("=" * 60)
    print("GENERATING EMBEDDED DATA FILES")
    print("=" * 60)

    SRC_OUT.mkdir(parents=True, exist_ok=True)
    INC_OUT.mkdir(parents=True, exist_ok=True)

    generate_header(INC_OUT / "embedded_data.h")

    generate_lexicon_cpp(
        DATA_DIR / "dictionaries" / "us_merged.json",
        "PHONEMIS_LANG_US",
        SRC_OUT / "lexicon_us.cpp",
    )

    generate_lexicon_cpp(
        DATA_DIR / "dictionaries" / "gb_merged.json",
        "PHONEMIS_LANG_GB",
        SRC_OUT / "lexicon_gb.cpp",
    )

    generate_hmm_cpp(
        DATA_DIR / "hmm.json",
        SRC_OUT / "hmm_data.cpp",
    )

    print("\nDone! Generated files:")
    for d in [SRC_OUT, INC_OUT]:
        for f in sorted(d.iterdir()):
            size = f.stat().st_size
            print(f"  {f.relative_to(PROJECT_ROOT)}  ({size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
