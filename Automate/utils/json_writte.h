#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <fstream>
#include <filesystem>

using namespace std;
namespace fs = std::filesystem;

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
    struct TransitionJsonFragment {
    private:
        string content;
    public:
        TransitionJsonFragment(
            int no,
            string char_,
            int actual_state,
            int new_state,
            string description
        ) {
            ostringstream oss;
            oss << "{\n"
                << "\"no\": " << no << ",\n"
                << "\"char\": \"" << escape_json(char_) << "\",\n"
                << "\"actual_state\": " << actual_state << ",\n"
                << "\"new_state\": " << new_state << ",\n"
                << "\"description\": \"" << escape_json(description) << "\"\n"
                << "}";

            content = oss.str();
        }

        string get_content() const { return content; }
    };


class TransitionsJson {
    private:
        string content;
        vector<TransitionJsonFragment> transitions;
        vector<string> errors;
        bool has_error;
        bool has_transitions;
    public:
        TransitionsJson() : has_error(false), has_transitions(false){
            clear();
        }

        void set_transition(TransitionJsonFragment transition) {
            has_transitions = true;
            transitions.push_back(transition);
        }

        /* void generate_transitions(
            int cantidad,
            const vector<string>& chars,
            const vector<int>& actual_states,
            const vector<int>& new_states,
            const vector<string>& descriptions
        ) {
            for (int i = 0; i < cantidad; ++i) {
                set_transition(Transition(
                    i,
                    chars[i],
                    actual_states[i],
                    new_states[i],
                    descriptions[i]
                ));
            }
        }*/

        void clear_errors(){
            errors.clear();
        }

        void clear_transitions(){
            transitions.clear();
        }

        void set_error(const string& error_) {
            errors.push_back(error_);
            has_error = true;
        }

        void set_errors(const vector<string>& errors_) {
            for (const auto& e : errors_) {
                set_error(e);
            }
        }

        void close_json() {
            if (has_transitions){
                content += ",\n\"transitions\": [\n";
                for (size_t i = 0; i < transitions.size(); ++i) {
                    content += transitions[i].get_content();
                    if (i + 1 < transitions.size()) content += ",\n";
                }
                content += "\n]";
            }
            

            if (has_error) {
                content += ",\n\"error\": [\n";
                for (size_t i = 0; i < errors.size(); ++i) {
                    content += "\"" + escape_json(errors[i]) + "\"";
                    if (i + 1 < errors.size()) content += ",\n";
                }
                content += "\n]";
            }
            content += "\n}";
        }

        void create_json(const string& filename = "transitions.json") {
            ofstream file(filename);
            if (file.is_open()) {
                file << content;
                file.close();
            }
        }

        string get_content() const { return content; }

        void clear(){
            ostringstream oss;
            oss << "{\n" ;

            content = oss.str();
            clear_transitions();
            clear_errors();
        }

        void set_output(int output){
            content +=  "\"output\": " + to_string(output) + "\n";
        }
        
    };
}

/*
int main() {
    JsonWritter::TransitionsJson json; // "output": 0
    // Opción 1: agregar transiciones una por una con set_transition
    json.set_transition(JsonWritter::Transition(0, "$", 1, 2, "Ingreso de variable"));
    json.set_transition(JsonWritter::Transition(1, "{", 2, 3, "Abrir llave"));
    json.set_transition(JsonWritter::Transition(2, "0", 3, 4, "En variable"));
    json.set_transition(JsonWritter::Transition(3, "x", 3, 3, "En variable"));

    // El error ahora es un arreglo: puedes llamar set_error varias veces,
    // o usar set_errors con un vector para agregarlos todos de golpe.
    // Si no lo necesitas, simplemente no llames a ninguno de los dos.
    json.set_error("Was expected an } in line 46");
    json.set_error("Unexpected token 'x' in line 52");

    json.close_json();
    json.create_json("transitions.json");

    cout << json.get_content() << endl;

    return 0;
}
*/