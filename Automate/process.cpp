#include <iostream>
#include <vector>
#include <filesystem>
#include <map>
#include <cmath>
#include <string>
#include <cctype>
#include <algorithm>

#include "utils/dll_lines.h"
#include "utils/json_writte.h"
#include "params.h"

using namespace std;
using namespace ddl_lines;

string errors[] = {
    "en linea: ",
    "Se esperaba"
};


void strip_context(string& context){
    size_t pos_out = context.find('\r');
    if (pos_out != std::string::npos) 
    context.replace(pos_out, 1, "\n");
}

string strip_new_context(string context){
    size_t pos_out = context.find('\r');
    if (pos_out != std::string::npos) 
    return context.replace(pos_out, 1, "\n");
    else
    return context;
}


ParsedCommand clear_command(string& command) {
    strip_context(command);
    ParsedCommand result;
    size_t pos_slash = command.find('/');
    if (pos_slash == std::string::npos) return result;

    size_t pos_cmd = command.find_first_not_of("/0123456789", pos_slash + 1);
    if (pos_cmd == std::string::npos) return result;
    try {
        result.line_key = std::stoi(command.substr(0, pos_slash));
        result.col_key = std::stoi(command.substr(pos_slash + 1, pos_cmd - (pos_slash + 1)));
        result.cmd_key = command[pos_cmd];
        
        command.erase(0, pos_cmd+1);
        if (command.empty()) command = "";
    } catch (...) {
    }

    return result;
}

//problema: unir lineas que se borran
void check_remove_line(ddl_lines::Node* current, ddl_lines::LineList& lines){
    if (current->data->context.empty() || current->data->context == "\n"){
        lines.remove(current->id);
    }
}

int check_split_lines(ddl_lines::Node* current, ddl_lines::LineList& lines){
    string temp_context = strip_new_context(current->data->context);
    size_t split_pos = temp_context.find('\n');
    if (split_pos == string::npos || split_pos == temp_context.length()-1) return -1;

    string next_line_context = current->data->context.substr(split_pos + 1);
    current->data->context = current->data->context.substr(0, split_pos + 1);

    ParsedCommand new_cmd;
    new_cmd.col_key = 0;
    Line* new_line = new Line(new_cmd);
    new_line->set_context(next_line_context);

    Node* new_node = lines.split_after(current, new_line);
    new_node->data->command.line_key = new_node->id;

    return split_pos;
}

void insert_char_context(string& context, size_t pos, const string& new_char)
{
    if (pos > context.length()) {
        context.resize(pos, ' ');
    }
    context.insert(pos, new_char);
}

int remove_char_context(string& context, size_t pos){
    if (pos <= context.length()) {
        context.erase(pos, 1);
        return 0;
    } 
    return -1;
}

/*
1) Ajustar lineas del IDE a DDL/Hash
2) Enviar al automata el nuevo caracter ingresado
3) 
*/

int main(){
    string path = std::filesystem::current_path().string();
    string command;
    LineList lines;
    JsonWritter::TransitionsJson json;
    while (getline(std::cin, command))
    {
        if (command.empty()) continue;
        //==================INIT SECTION==================
        json.clear();
        ParsedCommand result = clear_command(command);
        
        if (result.cmd_key == '@') { break; }
        Node* it = lines.get_node(result.line_key);

        //==================INIT SECTION==================
        if (it == nullptr) {
            Line* line = new Line(result);
            it = lines.emplace(result.line_key, line);
            json.set_error("Nuevo Id: "+to_string(it->id));
        } else{
            json.set_error("ID EXISTENTE: "+ to_string(result.line_key));
        }
        
        if (result.cmd_key == '+'){
            insert_char_context(it->data->context, result.col_key, command);
            it->data->command.col_key = result.col_key;
            json.set_error("Salto ded linea en:" +to_string(check_split_lines(it, lines)));
            json.set_error(to_string(strip_new_context(it->data->context).length()));
            //check_split_lines(it->data, &lines);
        } 
        if (result.cmd_key == '-'){
            if (remove_char_context(it->data->context, result.col_key-1) != 0){
                Node* merged = lines.merge_with_prev(it);
                if (merged) it = merged;
            } else {
                check_remove_line(it, lines);
            }
        }  
        /*
        lines.for_each_node([&](Node* temp)
        {
            int id_next = (temp->next)? temp->next->id : -1;
            int id_prev = (temp->prev)? temp->prev->id : -1;
            
            JsonWritter::TransitionJsonFragment* transition = new JsonWritter::TransitionJsonFragment(
                temp->id,
                temp->data->context,
                id_next,
                id_prev,
                "Col_key: " + to_string(temp->data->command.col_key)
            );
            json.set_transition(*transition);
            delete transition;
        });
        
        string er = "";
        lines.for_each([&](int key, Line* l)
        {
            er += "Key: " +to_string(key) + "; " + l->context;
            json.set_error(er);
        });
        */
        json.set_output(0);
        json.close_json();
        json.create_json(path+"/Automate/result/transitions.json");
    }
    return 0;
}