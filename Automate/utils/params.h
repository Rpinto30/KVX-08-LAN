#ifndef PARAMS
#define PARAMS
#include <iostream>
#include <algorithm> 
#include <cctype>  

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
    int line_index;
    
    Transitions(char c, int prev_state, int cur_state, int line_index): number(global_number), char_(c), actual_state(prev_state), new_state(cur_state), line_index(line_index) {
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


//ExCLUSIVO AUTOMATA

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

    bool operator==(const Block& other) const {
        return control_struct == other.control_struct
            && id_state == other.id_state
            && process == other.process;
    }
} Block;

struct AutomataContext {
    int actual_state = 0;
    CONTROL_STRUCT actual_passed;
    vector<Block> blocks;
    bool valid = true;
    bool initialized = false; 

    bool operator==(const AutomataContext& other) const {
        return actual_state == other.actual_state
            && actual_passed == other.actual_passed
            && valid == other.valid
            && blocks == other.blocks;
    }
};

//no pero por las referencias
typedef struct Line{
    string context; 
    ParsedCommand command;
    State init_state;
    State last_state;
    Node* parent;
    AutomataContext ctx_in;
    AutomataContext ctx_out;
    public:
    
    Line(ParsedCommand command): command(command), context(""), init_state(State{-1}), parent(nullptr), last_state(State{-1}) {}

    void set_context(string context){
        auto f = std::unique(context.begin(), context.end(), 
        [](char a, char b) { return a == ' ' && b == ' '; });
        
        context.erase(f, context.end());
        this->context = context;
        cout<<"Context: "<<this->context;
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
#endif