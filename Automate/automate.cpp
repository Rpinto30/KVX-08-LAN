<<<<<<< HEAD
#include <string.h>
#include <stdiolib.h>
#include <vector> //Para Listas
#include <iostream>
#include <map>
#include <set>

using Estado = string   //Estado == string
using Simbolo = char  //Simbolo == char


struct ClaveTransicion{
    Estado estado,
    Simbolo simbolo,
    bool operator<(const ClaveTransicion& otra)const //Decido entre la comparacion de claves que obtendre para ejecutar una comparacion y decirdir que clave va primero 
    {
        if(estado != otra.estado) return estado < otra.estado: //Cambiara a otra estado si el estado es diferente a estado
        return simbolo < otra.simbolo; //De la misma manera el simbolo lo hara
    }
};


int main()
{
    map<ClaveTransicion, Estado< transiciones; //Indico logistica para seguir las transiciones correspondientes
    set<simbolo>alfabeto = {};
    set<simbolo>grupoq2{}; //Sin compartir elemento o mas bien no se necesitan elementos repetidos hasta agregar uno similar 

    set<simbolo>numeros = {};
    set<simbolo>grupoq6{};
    
    transiciones[{"q0", '{'}] = "q1"; //Simbolo { necesario para inicializar
    transiciones[{"q1", '~' }] = "q5"; //Partiendo de q1 dos posibles casps, 1 numeors sibolo "~"
    for(char s: grupoq2)
    {

     transiciones[{"q1", s}] = "q2"; //2 Letras

    }

    for(char c >= 'a', c <= 'z', c++)
    {
        transiciones[{"q2", c}] = "q2"; //Bucle con caracteres en alfabeto
    }

    transiciones[{"q2",','}] = "q3";
    transiciones[{"q2",'~'}] = "q5";
    transiciones[{"q2", '}'}] = "q4";
    for(char s: grupoq2)
    {
        transiciones[{"q3", s}] = "q2";
    }

    for(char u: grupoq6)
    {
        transiciones[{"q5", u}] = "q6"
    }

    for(char digito = '0'; digito <= '9', ++digito)
    {
        transiciones[{"q6", digito}] = "q6";
    }

    transiciones[{"q6",','}] = "q3";
    transiciones[{"q6",'}'}] = "q4";

    set<Estado>estado_fin = {"q4"}

    Estado estado_inicial= "q0";

    set<Estado>acepta = {"q4"} //el mismo estadp final es el mismo que cumple los parametros para hecptar la cadena

    //El bufer almacenara caracter por caracter hasta encontrarse en el estado de fin
    //LAs cadenas guardadas almacenaran al bufer como una sola variante para su utlizacion en mas estados

    vector<char> buferActual; //Caracter por caracter
    vector<string> CadenaGuardada; //Cadena completa osea recopilado en el bufer hasta el fin
    


}

// Transiciones
Transiciones = {
    ("q0","0") = "q0",
    ("q0","1") = "q1", //Estructura: Si estoy en q0 y leo 1 paso a q1
    ("q1", "2") = "q2",
    ("q2", "3") = "q3",
    ("q3", "4") = "q4",
    ("q4", "5") = "q5",
    ("q5", "6") = "q6",
    ("q6", "7") = "q7",
    ("q7", "8") = "q8",
    ("q8", "9") = "q9",
    ("q9", "10") = "q10",
    ("q10","11") = "q11",
    ("q11", "12") = "q12",
    ("q12", "13") = "q13",
    ("q13", "14") = "q14",
    ("q14", "15") = "q15",
    ("q15", "16") = "q16",
    ("q16", "17") = "q17",
    ("q17", "18") = "q18",
    ("q18", "19") = "q19",
    ("q19", "20") = "q20",
    ("q20", "21") = "q21",
    ("q21", "22") = "q22",
    ("q22", "23") = "q23", //23 estados en total, transiciones requeridas
}

//Lo necesito aún??

char simular_afnd(cadena, estado_inicial, estado_aceptacion, alfabeto, transiciones) //Parametros necesarios para validar las transiciones
{
    estado_actual = estado_inicial //Iniciamos

    std::cout<<"Inicio de validación :",{cadena}<<std::endl; //Adentramos la cadena o caracter
    std ::cout<<"Estado Actual: ",{estado_actual}<<std::endl; //Iniciamos en estado 0

    for(char (simbolo): cadena) //Por cada caracter que se amacene o incluso por solo el caracter que se inserto 
    {
        if(std::find(alfabeto.begin(), alfabeto.end(), simbolo) == alfabeto.end()) //Si al inicio o fin del alfabeto no se encuentra entonces
        {
            std::cout<<"El simbolo", {simbolo}, "no pertenece al alfabeto"<<std::endl; //Imprime esto
        }

        estado_anterior = estado_actual //Ahora el estado anterior guarda el estado inicial para poder avanzar en los estados
        estado_actual = transiciones[(estado_actual, simbolo)] //Insertamos el estado actual junto a su simbolo por leer y asi avanzar por medio de las transiciones

        std::cout<<"Simbolo leído",{simbolo}, "Transición: ",{estado_anterior}, "->", {estado_actual} <<std::endl; //La transicion del estado anterior al actual


    }

    std::cout<<"Estado Final al culminar con la cadena: ", {estado_actual} <<std::endl; //El estado actual almacenra el estrado final 

    //if estado_acual in estado_aceptacion:
    //         print("Cadena Valida y aceptada")
    //         return True
    // else:
    //     print("Cadena Rechazada (no culimno un estado de aceptación)")
    //      return False

    if(estado_aceptacion.find(estado_actual) != std::string::npos)
    {
        std::cout<<"Cadena Valida y Aceptada"<<std::endl;
        return True;
    }else{
        std::cout<<"Cadena Rechazada(No culmino con el estado de acpetación)"<<std::endl;
        return False;
    }

}


//q1 Exisge un { y posterior a el puede pasar a q5 o q2
//q2 exige la ionserción de numeros o alfabeto las veces que requiera 
//q2 puede pasar a q5 o seguir con q3 esperando una ,
//q3 esta en bucle con q2 de manera que posterior a la coma puede obtener mas información
//q4 esta directamente conectado con q2 y q6 esperando la finalizacion de la cadane por medio de }
//q5 esta conectado por q1 y q2 espera ~ para inicializar una cadena numerica
//q6 solo conectado con q5 tiene la opcion de comprender el simbolo y agregar cuantos caracteres numericos sean posibles
//q6 esta conectado igual  a q3 y q4, de manera que si pasa a q3 por medio de una coma, debe de seguir agtregando ya sean simbolos 
//o pasar a q4 que es quien espera } apara finalizar con la cadena
=======
#include <iostream>
#include <string>
#include <vector>
#include <functional>

using namespace = std;

struct Fila{
    string comando;
    string cadena;
} 

typedef strcut Estado{
    int id;
} Estado

class Automata {

    bool valido = true;
    Estado actual{0}; //Este estado almacenara el historial del valor que cargo comenzando desde 0
    int posicionFallo = -1;

    string bufferCadena;
    vector<string>CadenasGuardadas;

    void evaluador(std::function<bool(const string&)>f)
    {
        evaluarCondicion = f;
    }

public:

    void get_(char character, Fila line)
     {
        if(line.comando == "{")
        {
            return actualizar(character, line)
        } 

        else if(line.comando == "@")
        {
            return actualizar(character, line)

        }

        else if (line.comando == "$")
        {
            return actualizar(character, line)

        }
        else if (line.comando == "*")
        {
            return actualizar(character, line)

        }
        else if(line.comando == "<! --")
        {
            return actualizar(character, line)

        }
        else if(line.comando == "%")
        {
            return actualizar(character, line)

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
        valido = true //Valido igual a true, mientras este en la actualizacion no se vuelva false contemplara su valor
        posicionFallo = -1//Eliminación del caracter

        int posicion = 0
        for (char c: cadena)
        {
            actualizar(c, Fila{"", cadena}) //Nos retorna el carcater que fallo el comando y la cadena

            if valido
            {
                posicionFallo = posicion;
                break; //La posicion "fallo" retorna la posicion valida
            }

            posicion ++; //Avanza
        }

        return actual.id;
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
                else {valido}; //Si no se cumple ninguna valido = false
                break;

            case 1:
            if      (character >= 'a' && character <= 'z') actual.id = 2;  

                else if(character >= '0' && character <= '9')actual.id = 2;
                else if (character == '~') actual.id = 5; 
                else {valido = false}; 
                break;

            case 2:

                if (character != ',' && character !=  '~' )
                {
                    if      (character >= 'a' && character <= 'z') actual.id = 2;  
                    else if(character >= '0' && character <= '9')actual.id = 2;   
                     else {valido = false; break;}; 

                    bufferCadena += character;
                }
                else if (character == '~') actual.id = 5;  
                else if (character == ',') actual.id = 3;  
                break;

            case 3:

                if      (character >= 'a' && character <= 'z') actual.id = 2;  
                else if(character >= '0' && character <= '9')actual.id = 2;
                else {valido = false};  
                break;

            case 4:

                if (character == '}') actual.id = 0;  
                else {valido = false};      
                break;

            case 5:

                if (character == '~') actual.id = 6;
                else {valido = false};       
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
                else{valido = false};
                break;

            case 8:
                if (character == ';') actual.id = 0;
                else {valido = false};
                break;

            case 9:
                if (character == '|') actual.id = 0; //No es necesario que lea || juntos 
                else {valido = false};
                break;

            case 10:
                if (character == '=') actual.id = 0 ;
                else {valido = false};
                break;

            case 11:
                if (character == '&') actual.id = 0 /* placeholder */;
                else {valido = false};
                break;

            // case 12:

            case 13:
                actual.id = 14;
                else {valido = false};
                break;

            case 14:
                // Bool

            case 15:
                if (character == ')') actual.id = character /* placeholder */;
                else {valido = false};
                break;

            case 16:
                actual.id = 0;
                break;

            case 17:
                if(character ==  '(') actual.id = 14;
                else {valido = false};
                break;

            case 18:
                actual.id = 0;
                break;

            case 19:
                if (character == '!')actual.id = 27;
                else{valido = false};
                break;

            case 27:
                if(character == '-')actual.id = 28;
                else{valido = false};
                break;

            case 28:
                if(character == '-')actual.id = 20
                else{valido = false};
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
                else {valido = false};
                break;

            case 29:
               if(character == '-')actual.id = 30;
               else{valido = false};
               break;

            case 30:
                if(character == '>')actual.id = 21;
                else{valido = false};
                break;


            case 21:
                actual.id = 0;
                break;

            case 22:
                if (character == '<') actual.id = 0 ;
                else {valido = false};
                break;

            case 23:
                if (character == '<') actual.id = 0 ;
                else {valido = false};
                break; //Ete esta mal


            case 24:
                if (character >= 'a' && character <= 'z')
                {
                    bufferCadena += character;
                    actual.id = 24
                }
                else if(character == '=')
                {
                    CadenasGuardadas.push_back(bufferCadena); //almacenamos la cadena
                    bufferCadena.clear();
                    actual.id = 8; //Culminamos secuencia de caracteres
                }
                else{valido = false};
                break;

            case 25:
                if (character != ';')
                {
                    bufferCadena += character;
                    actual.id = 25
                } 
                else if (character == ';') 
                {
                    CadenasGuardadas.push_back(bufferCadena);
                    bufferCadena.clear();
                    actual.id = 8;
                }
                else {valido = false};
                break;

            default:
                break;
        }

        if (actual.id == 0) {
            //valido = true;
        }
    }
}
>>>>>>> 37ad3f6ea2a099a927b34b33d81c2cc3df7893f4
