#ifndef PARAMS
#define PARAMS
#include <iostream>

using namespace std;

typedef struct State
{
    int id;
    int transition(bool condition){
        if (condition) return id;
    }

    State(int id) : id(id) {}

} State;

typedef struct ParsedCommand {
    int line_key = 0;
    int col_key = 0;
    char cmd_key = '\n';
} ParsedCommand;

typedef struct Line{
    string context; 
    ParsedCommand command;
    State init_state;

    public:
    Line(ParsedCommand command): command(command), context(""), init_state(State{-1}) {}

    void set_context(string context){
        this->context = context;
    }
    ~Line() = default;

} Line;

#endif