#ifndef AUTOMATE
#define AUTOMATE
#include <iostream>
#include <string>
#include <deque>
#include <functional>
#include <cctype>
#include <queue>
#include "utils/params.h"

using namespace std;

namespace afd{
    bool is_letter(char c){
        return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z');
    }

    bool is_hex_letter(char c){
        return (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F');
    }

    bool is_number(char c){
        return (c >= '0' && c <= '9');
    }


    class Automata{
        bool valid;
        queue<Transitions> history_transitions;
        Line* process_line;
        int actual_state;
        CONTROL_STRUCT actual_passed;
        vector<Block> blocks;

        //==================================VALIDAR
        void set_parent_case(char c, Block* &top){
            switch (c)
            {
                case '{': //string
                    top->id_state = 1;
                    push_context(IN_STRING, 1);
                break;
                case '$': //var
                    top->id_state = 7;
                    push_context(IN_CREATE_VAR, 7);
                break;
                case '<': //comment
                    top->id_state = 19;  
                    push_context(IN_COMMENT, 19);
                break;
                case '@': //loop
                    top->id_state = 17;  
                    push_context(IN_SET_VAR, 17);
                break;
                case '*': //set
                    top->id_state = 24;  
                    push_context(IN_SET_VAR, 24);
                break;
                case '%': //conditon
                    top->id_state = 13;  
                    push_context(IN_SET_VAR, 13);
                break;
                default:
                break;
            }
            top->process = IN;
        }

        void set_grandpa_string(char c, Block* &top){
            cout<<blocks.size()<<endl;
            if (blocks.size() == 2){
                if (c == ';') {
                    pop_context(top, 0);
                }
            } else{
                pop_context(top);
            }
        }

        void verify_string(char c, Block* &top){
            cout<<top->id_state<<endl;
            switch (top->id_state)
            {
                case 1:
                    if (is_hex_letter(c) || is_number(c)){
                        top->id_state = 2;
                        top->process = IN;
                    } else if (c == '~'){
                        top->id_state = 5;
                        top->process = IN;
                    } else{
                        top->process = FAIL;
                    }
                break;
                case 2:
                    if (is_hex_letter(c) || is_number(c)){
                        top->id_state = 2;
                        top->process = IN;
                    } else if (c == ','){
                        top->id_state = 3;
                        top->process = IN;
                    } 
                    else if (c == '~'){
                        top->id_state = 5;
                        top->process = IN;
                    }
                    else if (c == '}'){
                        top->id_state = 4;
                        top->process = DONE;
                        set_grandpa_string(c, top);
                    }
                    else{
                        top->process = FAIL;
                    }
                break;
                case 3:
                    if (is_hex_letter(c) || is_number(c)){
                        top->id_state = 2;
                        top->process = IN;
                    } else if (c == '~'){
                        top->id_state = 5;
                        top->process = IN;
                    } 
                    else{
                        top->process = FAIL;
                    }
                break;
                case 4:
                    top->process = DONE;
                break;
                case 5:
                    if (is_number(c)){
                        top->id_state = 6;
                        top->process = IN;
                    }else{
                        top->process = FAIL;
                    }
                break;
                case 6:
                    if (is_number(c)){
                        top->id_state = 6;
                        top->process = IN;
                    } else if (c == '}'){
                        top->id_state = 4;
                        top->process = IN;
                        set_grandpa_string(c, top);
                    }
                    else{
                        top->process = FAIL;
                    }
                break;
                default:
                break;
            }
        }

        void set_grandpa_var(char c, Block* &top){
            pop_context(top, 0);
        }

        void verify_var(char c, Block* &top){
            cout<<"Pre estado:"<<top->id_state<<endl;
            switch (top->id_state)
            {
                case 7:
                    top->id_state = 2500;
                    push_context(IN_STRING, 1);
                break;
                case 2500:
                    if (c == '='){
                        cout<<"..."<<endl;
                        top->id_state = 2501;
                        top->process = IN;
                    } else{
                        top->process = FAIL;
                    }
                break;
                case 2501:
                    if (c == '-'){
                        top->id_state = 25;
                        top->process = IN;
                    } else if (is_number(c)){
                        top->id_state = 25;
                        top->process = IN;
                    }
                    else{
                        top->process = FAIL;
                    }
                case 25:
                    if (is_number(c)){
                        top->id_state = 25;
                        top->process = IN;
                    } else if (c == ';'){
                        top->id_state = 8;
                        top->process = DONE;
                        set_grandpa_var(c, top);
                    } else{
                        top->process = FAIL;
                    }
                break;
                case 8:
                    top->process = DONE;
                break;
                default:
                break;
            }
        }

        void verify_create_var(char c, Block* &top){
            cout<<"Pre estado:"<<top->id_state<<endl;
            switch (top->id_state)
            {
                case 24:
                    top->id_state = 2500;
                    push_context(IN_STRING, 1);
                break;
                case 2500:
                    if (c == '='){
                        cout<<"..."<<endl;
                        top->id_state = 2501;
                        top->process = IN;
                    } else{
                        top->process = FAIL;
                    }
                break;
                case 2501:
                    if (c == '-'){
                        top->id_state = 25;
                        top->process = IN;
                    } else if (is_number(c)){
                        top->id_state = 25;
                        top->process = IN;
                    }
                    else{
                        top->process = FAIL;
                    }
                case 25:
                    if (is_number(c)){
                        top->id_state = 25;
                        top->process = IN;
                    } else if (c == ';'){
                        top->id_state = 8;
                        top->process = DONE;
                        set_grandpa_var(c, top);
                    } else{
                        top->process = FAIL;
                    }
                break;
                case 8:
                    top->process = DONE;
                break;
                default:
                break;
            }
        }

        void set_grandpa_comment(char c, Block* &top){
            pop_context(top, 0);
        }

        void verify_comment(char c, Block* &top){
            cout<<top->id_state<<endl;
            switch (top->id_state)
            {
                case 19:
                    if (c == '!'){
                        cout<<".."<<endl;
                        top->id_state = 1900;
                        top->process = IN;
                    } else {
                        top->process = FAIL;
                    }
                break;
                case 1900:
                    if (c == '-'){
                        top->id_state = 1901;
                        top->process = IN;
                    } else {
                        top->process = FAIL;
                    }
                break;
                case 1901:
                    if (c == '-'){
                        top->id_state = 20;
                        top->process = IN;
                    } else {
                        top->process = FAIL;
                    }
                break;
                case 20:
                    if (is_number(c)){
                        top->id_state = 20;
                        top->process = IN;
                    }else if (c == '-'){
                        top->id_state = 2000;
                        top->process = IN;
                    } else {
                        top->process = FAIL;
                    }
                break;
                case 2000:
                    if (c == '-'){
                        top->id_state = 2001;
                        top->process = IN;
                    } else {
                        top->process = FAIL;
                    }
                break;
                case 2001:
                    if (c == '>'){
                        cout<<"---"<<endl;
                        top->id_state = 21;
                        top->process = DONE;
                    } else {
                        top->process = FAIL;
                    }
                break;
                case 21:
                    set_grandpa_comment(c, top);
                break;

                default:
                break;
            }
        }

        void set_grandpa_bool(char c, Block* &top, int new_state){
            pop_context(top, new_state);
        }

        void verify_bool(char c, Block* &top, int new_state){
            cout<<top->id_state<<endl;
            switch (top->id_state)
            {
                case 22:
                    top->id_state = 1000;
                    push_context(IN_STRING, 1);
                break;
                case 1000:
                    if (c == '='){
                        top->id_state = 10000;
                        top->process = IN;
                    } else if (c == '|'){
                        top->id_state = 9000;
                        top->process = IN;
                    } else if (c == '&'){
                        top->id_state = 11000;
                        top->process = IN;
                    } else{
                        top->process = FAIL;
                    }
                break;
                case 10000:
                    if ( c == '='){
                        top->id_state = 12; //abuelo
                        push_context(IN_STRING, 1);
                    } else{
                        top->process = FAIL;
                    }
                break;
                case 9000:
                    if ( c == '|'){
                        top->id_state = 12; //abuelo
                        push_context(IN_STRING, 1);
                    } else{
                        top->process = FAIL;
                    }
                break;
                case 11000:
                    if ( c == '&'){
                        top->id_state = 12; //abuelo
                        push_context(IN_STRING, 1);
                    } else{
                        top->process = FAIL;
                    }
                break;
                case 12:
                    set_grandpa_bool(c, top, new_state); //el unico que lo pide 
                break;

                default:
                break;
            }
        }

        void set_grandpa_condition(char c, Block* &top){
            pop_context(top, 0);
        }

        void verify_condition(char c, Block* &top){
            cout<<top->id_state<<endl;
            switch (top->id_state)
            {
                case 13:
                    if (c == '('){
                        top->id_state = 15;
                        push_context(IN_BOOL, 1);
                    }else{
                        top->process = FAIL;
                    }
                break;
            
                default:
                break;
            }
        }

        void set_grandpa_loop(char c, Block* &top){
            pop_context(top, 0);
        }

        void verify_loop(char c, Block* &top){

        }

        //===================================== TOOLS
        void push_context(CONTROL_STRUCT control_struct, int start_state){
            blocks.push_back(Block{control_struct, start_state, IN});
        }

        void pop_context(Block*& top, int new_actual_state){
            if (blocks.size() > 1) {
                blocks.pop_back();
                top = &blocks.back();
                top->id_state = new_actual_state;
            }
        }

        void pop_context(Block*& top){
            if (blocks.size() > 1) {
                blocks.pop_back();
                top = &blocks.back();
            }
        }

        public: 
        Automata(): valid(false), actual_state(0), actual_passed(NOTHING) {
            blocks.push_back(Block{NOTHING, 0, DONE});
        }

        bool get_output() {return valid; }
        State get_state() {
            return blocks.back().id_state;
        }

        int get_actual_state(){ return blocks.back().id_state; }
        queue<Transitions>* get_queue() {return &history_transitions; }

        /*process_line = actual_line;
        Line* prev_line = process_line->get_prev_line();
        if (prev_line != nullptr){
            cout<<prev_line->last_state.id<<endl;
        }*/

        void actualizar(char c, Line* actual_line){
            Block* top = &blocks.back();
            if (top == nullptr) return;
            int previus_state = top->id_state;
            cout<<"Se ingreso :"<<c<<" , el estado actual: "<<previus_state<<endl;
            cout<<"Control struct: "<<top->control_struct<<endl;
            switch (top->control_struct)
            {
                case NOTHING: // q0
                    set_parent_case(c, top);
                break;
                case IN_STRING: // q1
                    if (top->process == DONE) //caso abuelo
                    {
                        set_grandpa_string(c, top);
                    }else{
                        verify_string(c, top);
                    }
                break;
                case IN_CREATE_VAR: 
                    if (top->process == DONE){
                        set_grandpa_var(c, top);
                    } else{
                        verify_var(c, top);
                    }
                break;
                case IN_SET_VAR: // q24
                    if (top->process == DONE){
                        //set_grandpa_var(c, top);
                    } else{
                        verify_create_var(c, top);
                    }
                break;
                case IN_COMMENT: // q19
                    if (top->process == DONE){
                        set_grandpa_comment(c, top);
                    } else {
                        verify_comment(c, top);
                    }
                break;
                case IN_CONDITION: // q13
                    if (top->process == DONE){
                        set_grandpa_condition(c, top);
                    } else {
                        verify_condition(c, top);
                    }
                break;
                case IN_LOOP: // q17
                    if (top->process == DONE){
                        set_grandpa_loop(c, top);
                    } else {
                        verify_loop(c, top);
                    }
                break;
                case IN_BOOL: // q...
                    if (top->process == DONE){
                        set_grandpa_bool(c, top, 15); //q15 es '('
                    } else {
                        verify_bool(c, top, 15); //q15 es '(' xd
                    }
                break;
                default:
                break;
            }

            if (top->process == DONE) {
                valid = true;
            } else {
                valid = false;
            }

            cout<<"LUEGO DEL PROCESAMIENTO el estado actual: "<<top->id_state<<endl;
            history_transitions.push(Transitions{c, previus_state, top->id_state});
        }
    };
}

#endif