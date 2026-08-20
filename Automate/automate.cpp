#include <iostream>
#include <string>
#include <vector>
#include <functional>

using namespace std;

struct Fila{
    string comando;
    string cadena;
};

typedef struct Estado{
    int id;
} Estado;

class Automata {

    bool valido = true;
    Estado actual{0}; //Este estado almacenara el historial del valor que cargo comenzando desde 0
    int posicionFallo = -1;

    string bufferCadena;
    vector<string>CadenasGuardadas;

    void evaluador(std::function<bool(const string&)>f)
    {
        //evaluarCondicion = f;
    }

public:

    int get_(char character, Fila line)
    {
        if(line.comando == "{")
        {
            return actualizar(character, line);
        } 

        else if(line.comando == "@")
        {
            return actualizar(character, line);

        }

        else if (line.comando == "$")
        {
            return actualizar(character, line);

        }
        else if (line.comando == "*")
        {
            return actualizar(character, line);

        }
        else if(line.comando == "<! --")
        {
            return actualizar(character, line);

        }
        else if(line.comando == "%")
        {
            return actualizar(character, line);

        }
        else if (line.comando == "-")
        {
            caracter_borrado(line.cadena);
        }

        return actual.id;
    }


    void caracter_borrado(string cadena)
    {
        actual.id = 0; //Inicializamos la comparacion temporal en 0
        valido = true; //Valido igual a true, mientras este en la actualizacion no se vuelva false contemplara su valor
        posicionFallo = -1;//Eliminación del caracter

        int posicion = 0;
        for (char c: cadena)
        {
            actualizar(c, Fila{"", cadena}); //Nos retorna el carcater que fallo el comando y la cadena

            if (valido)
            {
                posicionFallo = posicion;
                break; //La posicion "fallo" retorna la posicion valida
            }

            posicion ++; //Avanza
        }

        //return actual.id;
    }

    int actualizar(char character, Fila line)
    {
        switch (actual.id)  //Id en el que permanece momentaneamente
        {
            case 0:
                if      (character == '{') actual.id = 1;  //Defino cada caracter conforme el estado que proyecta 
                else if (character == '$') actual.id = 7;  
                else if (character == '*') actual.id = 24; 
                else if (character == '<') actual.id = 19; //Solo primer caracter por ser un character :)
                else if (character == '%') actual.id = 13; 
                else if (character == '@') actual.id = 17; 
                else {valido;} //Si no se cumple ninguna valido = false
                break;

            case 1:
            if      (character >= 'a' && character <= 'z') actual.id = 2;  

                else if(character >= '0' && character <= '9')actual.id = 2;
                else if (character == '~') actual.id = 5; 
                else {valido = false;} 
                break;

            case 2:

                if (character != ',' && character !=  '~' )
                {
                    if (character >= 'a' && character <= 'z') actual.id = 2;  
                    else if(character >= '0' && character <= '9')actual.id = 2;   
                    else {
                        valido = false; 
                    } 

                    bufferCadena += character;
                }
                else if (character == '~') actual.id = 5;  
                else if (character == ',') actual.id = 3;  
                break;

            case 3:

                if      (character >= 'a' && character <= 'z') actual.id = 2;  
                else if(character >= '0' && character <= '9')actual.id = 2;
                else {valido = false;}
                break;

            case 4:

                if (character == '}') actual.id = 0;  
                else {valido = false;} 
                break;

            case 5:

                if (character == '~') actual.id = 6;
                else {valido = false;}   
                break;

            case 6:

                if (character != ',')
                { 
                    if(character >= '0' && character <= '9')actual.id = 2;   
                    else {valido = false; break;}; 

                    bufferCadena += character;
                }  
                else if (character == ',') actual.id = 3;   
                break;

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
                else{valido = false;}
                break;

            case 8:
                if (character == ';') actual.id = 0;
                else {valido = false;}
                break;

            case 9:
                if (character == '|') actual.id = 0; //No es necesario que lea || juntos 
                else {valido = false;}
                break;

            case 10:
                if (character == '=') actual.id = 0 ;
                else {valido = false;}
                break;

            case 11:
                if (character == '&') actual.id = 0 /* placeholder */;
                else {valido = false;}
                break;

            // case 12:

            case 13:
                actual.id = 14;
                //else {valido = false;}
                break;

            case 14:
                // Bool

            case 15:
                if (character == ')') actual.id = character /* placeholder */;
                else {valido = false;}
                break;

            case 16:
                actual.id = 0;
                break;

            case 17:
                if(character ==  '(') actual.id = 14;
                else {valido = false;}
                break;

            case 18:
                actual.id = 0;
                break;

            case 19:
                if (character == '!')actual.id = 27;
                else{valido = false;}
                break;

            case 27:
                if(character == '-')actual.id = 28;
                else{valido = false;}
                break;

            case 28:
                if(character == '-') actual.id = 20;
                else{valido = false;}
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
                else {valido = false;}
                break;

            case 29:
               if(character == '-')actual.id = 30;
               else{valido = false;}
               break;

            case 30:
                if(character == '>')actual.id = 21;
                else{valido = false;}
                break;


            case 21:
                actual.id = 0;
                break;

            case 22:
                if (character == '<') actual.id = 0 ;
                else {valido = false;}
                break;

            case 23:
                if (character == '<') actual.id = 0 ;
                else {valido = false;}
                break; //Ete esta mal


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
                else{valido = false;}
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
                else {valido = false;}
                break;

            default:
                break;
        }

        if (actual.id == 0) {
            //valido = true;
        }
    }
};