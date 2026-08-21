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
    struct Fila{
        string comando;
        string cadena;
    };

    bool is_letter(char c){
        return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z');
    }

    bool is_number(char c){
        return (c >= '0' && c <= '9');
    }

    class Automata {
        bool valido;
        queue<Transitions> history_transitions;
        //State actual{0};
        Line* process_line;
        int actual_state;
        Passed actual_passed;

        // FIX #1: cambiado de vector<Block> a deque<Block>.
        // vector::push_back puede reubicar todo el buffer en memoria y dejar
        // "colgando" cualquier Block&/Block* que ya hayamos tomado con
        // context_stack.back() antes de llamar a push_context(). deque NO
        // invalida referencias/punteros a elementos existentes al hacer
        // push_back/pop_back, así que top/ptr_top siguen siendo válidos
        // aunque dentro de la misma llamada se empuje un nuevo contexto
        // (por ejemplo, al entrar a la cadena dentro de ${...}).
        deque<Block> context_stack;

        string bufferCadena;
        vector<string>CadenasGuardadas;

        // FIX #6: push_context ahora recibe el estado inicial del nuevo
        // bloque. Antes siempre nacía en state=0, pero cuando se entra a un
        // sub-contexto DESPUES de ya haber consumido el caracter que lo
        // dispara (ej. el '{' de ${...} ya fue leído por valid_variables),
        // el nuevo bloque debe arrancar en el estado al que ese caracter
        // ya lo habría llevado -- si no, el sub-automata se queda esperando
        // ver ese mismo caracter de nuevo y nunca avanza ("se queda en 0").
        void push_context(Passed type, int initial_state = 0){
            context_stack.push_back(Block{type, initial_state});
        }

        void pop_context(){
            if (context_stack.size() > 1) context_stack.pop_back();
        }

        // Sub-automata para cadenas: {0x48,0x4F,...} o {0x48,...,~12}
        RESULT valid_string(char c, Block*& block){
            switch(block->state){
                case 0:
                    if (c == '{') { block->state = 1; return RESULT::CONTINUE; }
                    return RESULT::FAIL;
                case 1:
                    if (is_letter(c) || is_number(c)) block->state = 2;
                    else if (c == '~') block->state = 5;
                    else return RESULT::FAIL;
                    return RESULT::CONTINUE;
                case 2:
                    if (c == ',') block->state = 3;
                    else if (c == '~') block->state = 5;
                    else if (c == '}') return RESULT::DONE;
                    else if (is_letter(c) || is_number(c)) block->state = 2;
                    else return RESULT::FAIL;
                    return RESULT::CONTINUE;
                case 3:
                    // luego de una ',' esperamos otro caracter de dato
                    if (is_letter(c) || is_number(c)) { block->state = 2; return RESULT::CONTINUE; }
                    return RESULT::FAIL;
                case 5:
                    // FIX #5: el estado 5 (después de '~', contador tipo ~12)
                    // no tenía transiciones propias y caía en el default,
                    // por lo que nunca podía cerrar con '}'. Se agrega el
                    // manejo explícito: acepta dígitos y cierra con '}'.
                    if (is_number(c)) { block->state = 5; return RESULT::CONTINUE; }
                    else if (c == '}') return RESULT::DONE;
                    return RESULT::FAIL;
                default:
                    return RESULT::FAIL;
            }
        }

        // Sub-automata para variables: ${...} = -10;
        RESULT valid_variables(char c, Block*& block){
            switch(block->state){ // que esta procesando
                case 0:
                    if (c == '$') {
                        block->state = 1;
                        block->type = IN_VARIABLE;
                        cout<<block->type<<endl;
                        return RESULT::CONTINUE;
                    }
                    return RESULT::FAIL;
                case 1:
                    if (c == '{') {
                        // FIX #4: antes de delegar en el sub-contexto IN_STRING
                        // hay que dejar preparado el estado al que se debe
                        // volver cuando esa cadena cierre (DONE -> pop_context()).
                        // Si no se avanza aquí, al volver el bloque IN_VARIABLE
                        // seguía en state == 1, que solo acepta '{' de nuevo,
                        // y el '=' que venía después causaba FAIL siempre.
                        block->state = 2;
                        // FIX #6: el '{' que acabamos de leer ya "cuenta" como
                        // la apertura de la cadena, así que el sub-automata
                        // IN_STRING debe arrancar en state=1 (el estado al que
                        // valid_string llega DESPUES de ver '{'), no en state=0
                        // (que es el que todavía espera ver el '{'). Con state=0
                        // el siguiente caracter (ej. un digito hex) no matchea
                        // ninguna transición del case 0 y el automata queda
                        // trabado ahí para siempre.
                        push_context(Passed::IN_STRING, 1);
                        return RESULT::CONTINUE;
                    }
                    return RESULT::FAIL;
                case 2:
                    if (c == '=') {
                        block->state = 3;
                        return RESULT::CONTINUE; }
                    return RESULT::FAIL;
                case 3:
                    if (c == '-' || is_number(c)) {
                        block->state = 4;
                        return RESULT::CONTINUE; }
                    return RESULT::FAIL;
                case 4:
                    if (is_number(c)) {
                        block->state = 4;
                        return RESULT::CONTINUE;
                    }
                    else if (c == ';'){
                        return RESULT::DONE;
                    }
                    return RESULT::FAIL;
                default:
                    return RESULT::FAIL;
                    break;
            }
        }


        /* void valid_comments(char c){
            switch(actual.id){
                case 0:
                    if (c == '<') actual.id = 19; //ESPECIAL, espera !
                    break;
                case 19:
                    if (c == '!')actual.id = 1901;
                    break;
                case 1901:
                    if (c == '-') actual.id = 1902; // ESPECIAL, espera -
                    break;
                case 1902:
                    if (c == '-') actual.id = 20; // ESPECIAL, espera otra vez -
                    break;
                case 20:
                    if (c == '-') actual.id = 21;
                    else if (is_letter(c) || is_number(c)) actual.id = 20;
                    break;
                case 21:
                    if (c == '-') actual.id = 2100; //ESPECIAL, espera el 2do -
                    break;
                case 2100:
                    if (c == '>') actual.id = 0;
                default: break;
            }
        }*/
        //APLICAR EL ENUM
        /*void valid_condition(char c){
            switch (actual.id)
            {
                case 0:
                    if (c == '(') actual.id = 12;
                break;
                case 4: //cadena valida
                    if (c == '|') actual.id = 901;
                    else if (c == '=') actual.id = 1001;
                    else if (c == '&') actual.id = 1101;
                    else if (c == ')') actual.id = 0; //actual id = 12
                break;
                case 901:
                    if (c == '|') actual.id = 0;
                break;
                case 1001:
                    if (c == '=') actual.id = 0;
                break;
                case 1101:
                    if (c == '&') actual.id = 0;
                break;
                default:
                    //valid_string(c);
                    break;
            }
        }*/

        // FIX #3: check_valid antes SIEMPRE delegaba en valid_variables, así
        // que una cadena suelta como {0x48,0x4F,...} (sin '$' adelante) jamás
        // podía validarse: valid_variables en state 0 exige '$' y con '{'
        // devolvía FAIL de inmediato. Ahora se decide el sub-automata según
        // el primer caracter recibido en el contexto NOTHING.
        // NOTA: falta agregar aquí '@' (bucles), '%' (condiciones) y '<'
        // (comentarios) cuando los implementes; de momento devuelven FAIL.
        RESULT check_valid(char c, Block*& block){
            if (c == '$') {
                return valid_variables(c, block);
            } else if (c == '{') {
                block->type = IN_STRING;
                return valid_string(c, block);
            }
            // TODO: '@' -> bucles, '%' -> condiciones, '<' -> comentarios
            return RESULT::FAIL;
        }

    public:
        Automata(): valido(false), actual_state(0), actual_passed(NOTHING) {
            context_stack.push_back(Block{NOTHING, 0});
        }

        bool get_output() {return valido; }
        State get_state() {
            return context_stack.back().state;
        }

        void actualizar(char c, Line* actual_line){
            //=============================ASIGNACION
            process_line = actual_line;

            cout<<"Automate, state ID: "<<actual_state<<endl;
            cout<<"Automate, Passed: "<<actual_passed<<endl;

            int prev_id = actual_state;
            Line* prev_line = process_line->get_prev_line();
            if (prev_line != nullptr){
                cout<<prev_line->last_state.id<<endl;
            }
            Block& top = context_stack.back();
            Block* ptr_top = &top;

            // FIX #2 (parte A): antes se inicializaba en RESULT::DONE, lo
            // cual es peligroso: cualquier rama del switch de abajo que no
            // esté cubierta (ej. IN_STRING) caía en "default: break;" sin
            // tocar actual_result, y quedaba como si el bloque hubiera
            // terminado con éxito, disparando pop_context()+valido=true sin
            // haber validado nada. Ahora arranca en CONTINUE.
            RESULT actual_result = RESULT::CONTINUE;
            //=============================ASIGNACION
            switch (top.type) //que esta haciendo
            {
                case NOTHING:
                    actual_result = check_valid(c, ptr_top);
                break;

                case IN_VARIABLE:
                    actual_result = valid_variables(c, ptr_top);
                break;

                // FIX #2 (parte B): faltaba el case IN_STRING. Sin esto, en
                // cuanto push_context(IN_STRING) dejaba ese tipo como tope de
                // la pila, la siguiente llamada a actualizar() caía en
                // default y "cerraba" la cadena en el primer caracter sin
                // validar nada.
                case IN_STRING:
                    actual_result = valid_string(c, ptr_top);
                break;

                default:
                    // Contextos aún no implementados (IN_COMMENT, IN_CONDITION,
                    // WAITING): por seguridad, no se asume éxito.
                    actual_result = RESULT::FAIL;
                break;
            }

            if (actual_result == RESULT::DONE) {
                pop_context();
                valido = true;
            } else if (actual_result == RESULT::FAIL) {
                valido = false;
            }


            //=============================OUTPUT
            actual_state = context_stack.back().state;
            cout<<"------------------------------------------"<<endl;
            cout<<"Automate, NEW result: "<<actual_result<<endl;
            cout<<"Automate, NEW state ID: "<<actual_state<<endl;
            cout<<"Automate, NEW Passed: "<<actual_passed<<endl;
        }

        /*void actualizar(char character, Line* actual_line){
            process_line = actual_line;
            Line* prev_line = process_line->get_prev_line();
            Block& top = context_stack.back();
            RESULT r;
            cout<<"Automate, state ID: "<<actual<<endl;
            cout<<" - Automate, Passed: "<<top.type<<endl;
            switch (top.type){
                case NOTHING:
                    r = valid_all(character, top);
                break;
                case IN_STRING:
                    r = valid_string(character, top);
                break;
                case IN_VARIABLE:
                    r = valid_variables(character, top);
                break;
                case WAITING:
                    r = valid_variables(character, top);
                break;
                default:
                    r = RESULT::CONTINUE;
                break;
            }
            int prev_id = top.state;


            if (r == RESULT::DONE) {
                pop_context();
            } else if (r == RESULT::FAIL) {
                valido = false;
            }

            actual_line->last_state.id = top.state;

            valido = ( top.state == 0);
            history_transitions.push(Transitions{character, actual, prev_id});
            cout<<"Automate, state ID: "<<prev_id<<endl;
            cout<<" - Automate, Passed: "<<top.type<<endl;
            actual = prev_id;

        }*/

        int get_actual_state(){ return context_stack.back().state; }
        queue<Transitions>* get_queue() {return &history_transitions; }
    };
}

#endif
