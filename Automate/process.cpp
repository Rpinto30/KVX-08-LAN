#include <iostream>
#include <vector>
#include <filesystem>
#include "json_writte.h"

using namespace std;

string errors[] = {

};

struct Line{
    int number; //1
    string cadena; // $0x11} = 12;
    string commando; //-
};

/*int argc, char* argv[]*/
int main(){
    string path = std::filesystem::current_path().string();
    string new_line;
    string command;
    vector<Line> lines;
    JsonWritter::TransitionsJson json;
    cout<<path<<endl;
    while (getline(std::cin, command))
    {
        if (command.empty()) continue;
        json.clear();

        if (command[0] == '@') {
            cout<<path+"/Automate/result/transitions.json"<<endl;
            break;
        }
        else if (command[0] == '+'){
            char new_ = command[1];
            new_line += new_ ;
        }
        else if (command[0] == '-'){
            if (!new_line.empty()){
                new_line.pop_back();
            }
        }
        cout<<"Ejecutado"<<endl;
        json.set_output(0);
        json.close_json();
        json.create_json(path+"/Automate/result/transitions.json");
    }
    return 0;
}