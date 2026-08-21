#ifndef PARAMS
#define PARAMS
#include <iostream>

using namespace std;

typedef struct State
{
    int id;

    State(int id) : id(id) {}

} State;

typedef struct Transitions{
    static int global_number;
    int number;
    char char_;
    int actual_state;
    int new_state;
    string description;
    
    Transitions(char c, int prev_state, int cur_state): number(global_number), char_(c), actual_state(prev_state), new_state(cur_state) {
        global_number++;
    }

    void set_description(string description){
        this->description = description;
    }
} Transitions;

typedef struct ParsedCommand {
    int line_key = 0;
    int col_key = 0;
    char cmd_key = '\n';
} ParsedCommand;

//==================DDL==================
struct Line;
struct Node {
    int id;
    Line* data;
    Node* prev;
    Node* next;

    Node(int id_, Line* data_)
        : id(id_), data(data_), prev(nullptr), next(nullptr) {}
};

typedef struct Line{
    string context; 
    ParsedCommand command;
    State init_state;
    State last_state;
    Node* parent;
    public:
    
    Line(ParsedCommand command): command(command), context(""), init_state(State{-1}), parent(nullptr), last_state(State{-1}) {}

    void set_context(string context){
        this->context = context;
    }

    void set_actual_state(int id){
        last_state.id = id;
    }

    void set_parent(Node* node){
        this->parent = node;
    }


    Line* get_next_line() const {
        return (parent && parent->next) ? parent->next->data : nullptr;
    }

    Line* get_prev_line() const {
        return (parent && parent->prev) ? parent->prev->data : nullptr;
    }

    ~Line() = default;

} Line;

//ESCLUSIVO AUTOMATA
enum CONTROL_STRUCT{
    NOTHING, //0
    IN_STRING, //1
    IN_CREATE_VAR, //2
    IN_SET_VAR, //3
    IN_COMMENT,  //4
    IN_CONDITION,  //5
    IN_LOOP,  //6
    IN_BOOL,  //7
};

// Continue: NUEVA SECCION Y SE MANTIENE
// Done: OUTPUT 1 Y CIERRA LA SESION (POP)
// Fail: OUTPUT 0 Y CONTINUA LA SESION
enum PROCESS{
    IN, DONE, FAIL
};

typedef struct Block{
    CONTROL_STRUCT control_struct;
    int id_state;
    PROCESS process;
    Block(CONTROL_STRUCT type, int state): control_struct(type), id_state(state), process(IN) {}
    Block(CONTROL_STRUCT type, int state, PROCESS process): control_struct(type), id_state(state), process(process) {}
} Block;




#endif