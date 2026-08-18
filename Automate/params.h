#ifndef PARAMS
#define PARAMS

typedef struct State
{
    int id;
    int transition(bool condition){
        if (condition) return id;
    }

    State(int id) : id(id) {}

} State;

#endif