#ifndef AUTOMATE
#define AUTOMATE
#include <iostream>
#include <string>
#include <vector>
#include <functional>
#include <cctype>
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
        State actual{0};
        int posicionFallo;

        string bufferCadena;
        vector<string>CadenasGuardadas;

        void valid_string(char c){
            switch(actual.id){
                case 0:
                    if (c == '{') actual.id = 1;  
                    break;
                case 1:
                    if (is_letter(c) or is_number(c)) actual.id = 2;
                    else if (c == '~') actual.id = 5; 
                    break;

                case 2:
                    if (c == ',') actual.id = 3;
                    else if (c == '~') actual.id = 5;  
                    else if (c == '}') actual.id = 4;
                    else {
                        if (is_letter(c) or is_number(c)) actual.id = 2;
                        bufferCadena += c;
                    }
                    
                    break;

                case 3:
                    if (is_letter(c) or is_number(c)) actual.id = 2;
                    else if (c == '~') actual.id = 5; 
                    break;

                case 4:
                    actual.id = 0;//if (c == '}') actual.id = 0;  
                    break;

                case 5:
                    if (is_number(c)) actual.id = 6; 
                    break;

                case 6:
                    if (c == ',') actual.id = 3; 
                    else if (c == '}') actual.id = 4;
                    else
                    { 
                        if (is_number(c)) actual.id = 6;   
                        bufferCadena += c;
                    }  
                    break;

                default:
                break;
            }
        }

    public:
        Automata(): valido(false), posicionFallo(-1) {}
    
        bool get_output() {return valido; }
        State get_state() {return actual; }

        void actualizar(char character, Line* actual_line)
        {
            cout<<"Automate, state ID: "<<actual.id<<endl;
            /*switch (actual.id)
            {
                case 7:
                    if (character >= 'a' && character <= 'z'  )
                    {
                        bufferCadena += character;
                        actual.id = 7;
                    }
                    //No recuerdo muy bien para que era el igual, pero puede ser para poder pasar a almacenar otra variable por medio del "="
                    else if(character == '=' )
                    {
                        CadenasGuardadas.push_back(bufferCadena);
                        bufferCadena.clear(); 
                        actual.id = 25;
                    }
                    break;

                case 8:
                    if (character == ';') actual.id = 0;
                    break;

                case 9:
                    if (character == '|') actual.id = 0; //No es necesario que lea || juntos 
                    break;

                case 10:
                    if (character == '=') actual.id = 0 ;
                    break;

                case 11:
                    if (character == '&') actual.id = 0 ;
                    break;

                case 13:
                    actual.id = 14;
                    break;

                case 14:
                    // Bool
                    break;

                case 15:
                    if (character == ')') actual.id = character ;
                    break;

                case 16:
                    actual.id = 0;
                    break;

                case 17:
                    if(character ==  '(') actual.id = 14;
                    break;

                case 18:
                    actual.id = 0;
                    break;

                case 19:
                    if (character == '!')actual.id = 27;
                    break;

                case 27:
                    if(character == '-')actual.id = 28;
                    break;

                case 28:
                    if(character == '-') actual.id = 20;
                    break;

                case 20:
                    if (character != '-')
                    {
                        if      (character >= 'a' && character <= 'z') actual.id = 20;  
                        else if(character >= '0' && character <= '9')actual.id = 20;   
                        else{valido = false; break;}

                        bufferCadena += character;
                    }
                    else if (character == '-') actual.id = 29;  // Leyo primer caracter
                    break;

                case 29:
                    if(character == '-')actual.id = 30;
                    break;

                case 30:
                    if(character == '>')actual.id = 21;
                    break;
                case 21:
                    actual.id = 0;
                    break;

                case 22:
                    if (character == '<') actual.id = 0 ;
                    break;

                case 23:
                    if (character == '<') actual.id = 0 ;
                    break;
                case 24:
                    if (character >= 'a' && character <= 'z')
                    {
                        bufferCadena += character;
                        actual.id = 24;
                    }
                    else if(character == '=')
                    {
                        CadenasGuardadas.push_back(bufferCadena); //almacenamos la cadena
                        bufferCadena.clear();
                        actual.id = 8; //Culminamos secuencia de caracteres
                    }
                    break;

                case 25:
                    if (character != ';')
                    {
                        bufferCadena += character;
                        actual.id = 25;
                    } 
                    else if (character == ';') 
                    {
                        CadenasGuardadas.push_back(bufferCadena);
                        bufferCadena.clear();
                        actual.id = 8;
                    }
                    break;

                default:
                    break;
            }
            */
            valid_string(character);
            if (actual_line->init_state.id == -1){
                if (actual.id != 0) {
                    actual_line->init_state.id = actual.id;
                    cout<<" -------- Linea: "<<actual_line->command.line_key<<endl;
                    cout<<" - Context: "<<actual_line->context<<endl;
                    cout<<" - Estado inicial: "<<actual_line->init_state.id<<endl;
                }
            }
            if (actual.id == 0) {
                valido = true;
            } else{
                valido = false;
            }
            cout<<"Automate, AFTER ID: "<<actual.id<<endl;
            cout<<"Automate, BUFFER: "<<bufferCadena<<endl;
            
        }
    };
}

#endif