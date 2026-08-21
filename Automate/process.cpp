#include <iostream>
#include <vector>
#include <filesystem>
#include <map>
#include <cmath>
#include <string>
#include <cctype>
#include <algorithm>
#include <queue>

#include "utils/dll_lines.h"
#include "utils/json_writte.h"
#include "utils/params.h"
#include "automate.h"


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

struct RangeCommand {
    int start_index = 0;
    int end_index = 0;
    string text = "";
};

//problema: unir lineas que se borran
void check_remove_line(Node* current, ddl_lines::LineList& lines){
    if (current->data->context.empty() || current->data->context == "\n"){
        lines.remove(current->id);
    }
}

int check_split_lines(Node* current, ddl_lines::LineList& lines){
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

RangeCommand parse_range_command(const string& command){
    RangeCommand r;
    size_t slash_pos = command.find('/');
    size_t semi_pos = command.find(';');
    if (slash_pos == string::npos || semi_pos == string::npos) return r;
    r.start_index = stoi(command.substr(0, slash_pos));
    r.end_index   = stoi(command.substr(slash_pos + 1, semi_pos - (slash_pos + 1)));
    r.text  = command.substr(semi_pos + 1); 
    strip_context(r.text);
    return r;
}

/*==========================ESPECIAL ACTIONS==========================*/
bool locate_global_offset(LineList& lines, int target_offset, Node*& out_node, int& out_col){
    int accumulated = 0;
    Node* node = lines.get_head();
    while (node){
        int len = (int)node->data->context.length();
        if (target_offset <= accumulated + len){
            out_node = node;
            out_col = target_offset - accumulated;
            return true;
        }
        accumulated += len;
        node = node->next;
    }
    return false;
}

void delete_one_backward(LineList& lines, Node*& node, int& col){
    if (col > 0){
        remove_char_context(node->data->context, col - 1);
        col--;
    } else {
        int boundary = 0;
        if (node->prev) {
            boundary = (int)node->prev->data->context.length();
            if (boundary > 0 && node->prev->data->context.back() == '\n') boundary--;
        }
        Node* merged = lines.merge_with_prev(node);
        node = merged;
        col = merged ? boundary : 0;
    }
}

void insert_one_forward(LineList& lines, Node*& node, int& col, char c){
    insert_char_context(node->data->context, col, string(1, c));
    node->data->command.col_key = col;
    col++;

    int split_pos = check_split_lines(node, lines);
    if (split_pos != -1){
        node = node->next; // el resto se movió a la línea siguiente
        col = 0;
    }
}

/*
1) Ajustar lineas del IDE a DDL/Hash
2) Enviar al automata el nuevo caracter ingresado
3) Capturar y enviar a json
*/
int Transitions::global_number = 0;

int main(){
    string path = std::filesystem::current_path().string();
    string command;
    LineList lines;
    JsonWritter::TransitionsJson json;
    afd::Automata automate;

    while (getline(std::cin, command))
    {
        cout<<"===================================================="<<endl;
        cout<<"Command: "<<command<<endl;
        if (command.empty()) continue;
        //==================INIT SECTION==================
        json.clear();
        ParsedCommand result = clear_command(command);
        
        if (result.cmd_key == '@') { break; }
        Node* it = lines.get_node(result.line_key);

        if (it == nullptr) {
            Line* line = new Line(result);
            it = lines.emplace(result.line_key, line);
        } 
        
        // ESPECIAL ACTION
        if (result.cmd_key == '|'){
            RangeCommand range = parse_range_command(command);
            int count = range.end_index - range.start_index;
            Node* cursor; int cursor_col;
            if (locate_global_offset(lines, range.end_index, cursor, cursor_col)){
                for (int i = 0; i < count && cursor; ++i){
                    delete_one_backward(lines, cursor, cursor_col);
                }
                it = cursor;
            }
        }

        /*
        if (result.cmd_key == '~'){
            RangeCommand range = parse_range_command(command);
            int count = range.end_index - range.start_index;

            Node* cursor; int cursor_col;
            if (locate_global_offset(lines, range.end_index, cursor, cursor_col)){
                for (int i = 0; i < count && cursor; ++i){
                    delete_one_backward(lines, cursor, cursor_col);
                }
                for (char c : range.text){
                    insert_one_forward(lines, cursor, cursor_col, c);
                }
                it = cursor;
            }
        }*/


        //=================UPDATE SECTION=================
        if (result.cmd_key == '+'){
            Node* cursor = it;
            int cursor_col = result.col_key;
            insert_one_forward(lines, cursor, cursor_col, command[0]);
            it = cursor;
        } 
        if (result.cmd_key == '-'){
            Node* cursor = it;
            int cursor_col = result.col_key;
            delete_one_backward(lines, cursor, cursor_col);
            it = cursor;
        }

        //=================PROCESS SECTION=================
        automate.actualizar(command[0], lines.get_line(result.line_key));
        while (!automate.get_queue()->empty()) {
            Transitions temp = automate.get_queue()->front(); 
            cout<<temp.char_<<endl;
            JsonWritter::TransitionJsonFragment transition{
                temp.number,
                string (1, temp.char_),
                temp.actual_state,
                temp.new_state,  
                ""
            };
            json.set_transition(transition);
            automate.get_queue()->pop(); 
        }

        /*lines.for_each_node([&](Node* temp)
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
        });*/
        
        json.set_output(automate.get_output());
        json.close_json();
        json.create_json(path+"/Automate/result/transitions.json");
        //cout<<"---------- LINEAS: "<<endl;
        //lines.for_each_lines([&](Line* line){});
    }
    return 0;
}