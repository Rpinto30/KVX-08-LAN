// logica_kravnika.cpp / logica_kravnika.hpp
//
// Libreria de conectores logicos pensada para ser llamada DIRECTAMENTE por
// un validador de reglas externo, pasando bits sueltos (0/1) y recibiendo
// un bit de vuelta. No hay arboles de objetos ni construccion previa:
// cada operacion es una llamada simple, tipo funcion.
//
//   Bin resultado = Logica::OR(a, b);
//
// "and", "or", "not", "xor" son palabras reservadas en C++ (alias de
// &&, ||, !, ^), por eso los metodos se llaman AND, OR, NOT, XOR.
//Bip Bop

using Bin = bool;

class Logica {
    public:
        // NOT: unario
        static Bin NOT(Bin a) { return !a; }

        // AND, OR, XOR: operan bit a bit sobre un unico bit (a | b, a & b, a ^ b)
        static Bin AND(Bin a, Bin b) { return a & b; }
        static Bin OR (Bin a, Bin b) { return a | b; }
        static Bin XOR(Bin a, Bin b) { return a ^ b; }

        // IMPLIES (a -> b) = NOT(a) OR b
        static Bin IMPLIES(Bin a, Bin b) { return NOT(a) | b; }

        // IFF (a <-> b) = NOT(a XOR b)   (verdadero cuando a y b son iguales)
        static Bin IFF(Bin a, Bin b) { return NOT(XOR(a, b)); }

        Logica() = delete;
        Logica(const Logica&) = delete;
        Logica& operator=(const Logica&) = delete; 
};