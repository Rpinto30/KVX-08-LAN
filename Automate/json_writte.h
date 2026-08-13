#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <fstream>

using namespace std;

namespace JsonWritter {
    string escape_json(const string& s) {
        ostringstream out;
        for (char c : s) {
            switch (c) {
                case '"':  out << "\\\""; break;
                case '\\': out << "\\\\"; break;
                case '\n': out << "\\n";  break;
                case '\t': out << "\\t";  break;
                case '\r': out << "\\r";  break;
                default:   out << c;
            }
        }
        return out.str();
    }

    struct Word_json {
    private:
        string content;
    public:
        Word_json(
            string content_,
            bool output,
            bool init_quotation,
            bool init_hyphen,
            bool contain_names,
            bool have_digits,
            bool have_special_charts_digits,
            bool next_special_chart_between_19
        ) {
            ostringstream oss;
            oss << "{\n"
                << "\"content\": \"" << escape_json(content_) << "\",\n"
                << "\"output\": " << static_cast<int>(output) << ",\n"
                << "\"init_quotation\": " << static_cast<int>(init_quotation) << ",\n"
                << "\"init_hyphen\": " << static_cast<int>(init_hyphen) << ",\n"
                << "\"contain_names\": " << static_cast<int>(contain_names) << ",\n"
                << "\"have_digits\": " << static_cast<int>(have_digits) << ",\n"
                << "\"have_special_charts_digits\": " << static_cast<int>(have_special_charts_digits) << ",\n"
                << "\"next_special_chart_between_19\": " << static_cast<int>(next_special_chart_between_19) << "\n"
                << "}";

            content = oss.str();
        }

        string get_content() const { return content; }
    };

    struct Sentence {
private:
    string content;
    vector<Word_json> words;
public:
    Sentence(
        string content_,
        bool output,
        bool init_exclamation,
        bool end_exclamation,
        bool init_interogation,
        bool end_interogation,
        bool split_by_double_dot,
        bool end_dot,
        bool last_letter
    ) {
        ostringstream oss;
        oss << "{\n"
            << "\"content\": \"" << escape_json(content_) << "\",\n"
            << "\"output\": " << static_cast<int>(output) << ",\n"
            << "\"init_exclamation\": " << static_cast<int>(init_exclamation) << ",\n"
            << "\"end_exclamation\": " << static_cast<int>(end_exclamation) << ",\n"
            << "\"init_interogation\": " << static_cast<int>(init_interogation) << ",\n"
            << "\"end_interogation\": " << static_cast<int>(end_interogation) << ",\n"
            << "\"split_by_double_dot\": " << static_cast<int>(split_by_double_dot) << ",\n"
            << "\"end_dot\": " << static_cast<int>(end_dot) << ",\n"
            << "\"last_letter\": " << static_cast<int>(last_letter) << "\n";

        content = oss.str();
    }

    void set_word(Word_json word) {
        words.push_back(word);
    }

    void close_sentence() {
        content += ",\n\"words\": [\n";
        for (size_t i = 0; i < words.size(); ++i) {
            content += words[i].get_content();
            if (i + 1 < words.size()) content += ",\n";
        }
        content += "\n]\n}";
    }

    string get_content() const { return content; }
};

    class Json {
    private:
        string content;
        vector<Sentence> sentences;
    public:
        Json(bool output) {
            ostringstream oss;
            oss << "{\n"
                << "\"output\": " << static_cast<int>(output) << "\n";

            content = oss.str();
        }

        void create_json(){
            ofstream file("proposition.json");
            if (file.is_open()) {
                file << content;
                file.close();
                //cout << "Archivo generado correctamente." << endl;
            } else {
                //cerr << "No se pudo abrir el archivo para escritura." << endl;
            }
        }

        void set_sentence(Sentence sentence) {
            sentences.push_back(sentence);
        }

        void close_json() {
            content += ",\n\"sentences\": [\n";
            for (size_t i = 0; i < sentences.size(); ++i) {
                content += sentences[i].get_content();
                if (i + 1 < sentences.size()) content += ",\n";
            }
            content += "\n]\n}";
        }

        string get_content() const { return content; }
    };
}
