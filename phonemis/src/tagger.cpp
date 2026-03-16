#include <phonemis/tagger/tagger.h>
#include <phonemis/data/embedded_data.h>
#include <algorithm>
#include <stdexcept>

namespace phonemis::tagger {

Tagger::Tagger() {
	// Load start probabilities from embedded data
	for (const auto& [tag_sv, prob] : data::get_hmm_start_prob()) {
		const Tag tag{std::string(tag_sv)};
		tags_.insert(tag);
		start_probs_[tag] = prob;
	}

	// Load emission probabilities from embedded data
	for (const auto& entry : data::get_hmm_emission()) {
		const Tag tag{std::string(entry.key1)};
		emission_probs_[tag][std::string(entry.key2)] = entry.value;
	}

	// Load transition probabilities from embedded data
	for (const auto& entry : data::get_hmm_transition()) {
		const Tag from_tag{std::string(entry.key1)};
		const Tag to_tag{std::string(entry.key2)};
		transition_probs_[from_tag][to_tag] = entry.value;
	}
}

void Tagger::tag(std::vector<tokenizer::Token> &sentence) const {
  // A workaround for zero probability
  constexpr double EPSILON = 1e-6;

	if (sentence.empty()) {
		return;
	}

	// Viterbi tables
  // back_pointer table allows to reconstruct the optimal path in the state (tag) graph.
	std::vector<std::unordered_map<Tag, double>> 
    v(sentence.size()); // v[t][state] -> probability
	std::vector<std::unordered_map<Tag, Tag>> 
    back_pointer(sentence.size());  // back_pointer[t][state] -> previous_state

	// Initialization
  // Calculates probabilities for the first word in the sentence.
	for (const auto& tag : tags_) {
		double start_p = start_probs_.at(tag);
    double emit_p = emission_probs_.at(tag).contains(sentence[0].text) 
                    ? emission_probs_.at(tag).at(sentence[0].text) : EPSILON;
		v[0][tag] = start_p * emit_p;

		// To make the algorithm less case-sensitive, probe the initial value for lower-case word
		if (std::isalpha(sentence[0].text[0])) {
			std::string lowerized = sentence[0].text;
			lowerized[0] = std::tolower(lowerized[0]);
			emit_p = emission_probs_.at(tag).contains(lowerized) 
                ? emission_probs_.at(tag).at(lowerized) : EPSILON;
			v[0][tag] = std::max(v[0][tag], start_p * emit_p);
		}
	}

	// Recursion
  // Processes through the rest of the sentence.
	for (size_t t = 1; t < sentence.size(); ++t) {
    const auto& word = sentence[t].text;

		for (const auto& curr_tag : tags_) {
      // Helper variables to track the best branch
			double max_prob = -1.0;
			Tag best_prev;

      double emit_p = emission_probs_.at(curr_tag).contains(word) 
                    ? emission_probs_.at(curr_tag).at(word) : EPSILON;

			for (const auto& prev_tag : tags_) {
        double trans_p = transition_probs_.at(prev_tag).contains(curr_tag)
                          ? transition_probs_.at(prev_tag).at(curr_tag) : EPSILON;
				double prob = v[t - 1][prev_tag] * trans_p * emit_p;

				if (prob > max_prob) {
					max_prob = prob;
					best_prev = prev_tag;
				}
			}

			v[t][curr_tag] = max_prob;
			back_pointer[t][curr_tag] = best_prev;
		}
	}

	// Termination
  // Selects the most probable final tag.
  // The other tags are selected by backtracking through the saved path.
	size_t last_idx = sentence.size() - 1;
	auto best_it = std::max_element(tags_.begin(), tags_.end(), [&](const auto& a, const auto& b) {
			return v[last_idx][a] < v[last_idx][b];
	});

	// Backtracking path
	Tag current_tag = *best_it;
	sentence[last_idx].tag = current_tag;

	for (size_t t = last_idx; t > 0; --t) {
		current_tag = back_pointer[t][current_tag];
		sentence[t - 1].tag = current_tag;
	}
}

} // namespace phonemis::tagger