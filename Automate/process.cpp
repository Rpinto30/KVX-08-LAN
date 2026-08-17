#include <iostream>
#include <vector>
#include <filesystem>
#include <map>
#include "json_writte.h"

using namespace std;

string errors[] = {

};

typedef struct Line{
    int line; //1
    int column;
    string context; // $0x11} = 12;
    char command; //-

    public:
    Line(int line, int column, char command): line(line), column(column), command(command){}

    ~Line(){
        delete this;
    }
} Line;

string clear_command(string& command){
    size_t pos_slash = command.find("/");
    string pos = command.substr(0, pos_slash);
    char x = pos[0]; 
    char y = pos[pos.length()-1];
    
    char cmd = command[pos_slash+1];
    command.erase(0, pos_slash+2); 

    return { x, y, cmd };
}

/*int argc, char* argv[]*/
int main(){
    string path = std::filesystem::current_path().string();
    string command;
    map<int, Line*> lines;
    JsonWritter::TransitionsJson json;
    while (getline(std::cin, command))
    {
        if (command.empty()) continue;
        json.clear();
        
        string list_result = clear_command(command);
        auto it = lines.find(list_result[0] - '0');
        if (it == lines.end()) {
            json.set_error(
                list_result
            );
            Line* line = new Line(list_result[0]-'0', list_result[1]-'0', list_result[2]);
            lines.emplace(list_result[0]-'0', line);
        }

        if (command[0] == '@') {
            break;
        }
        else if (command[0] == '+'){
            
            
        }
        else if (command[0] == '-'){
            /* if (!new_line.empty()){
                new_line.pop_back();
            }*/
        }
        cout<<"Ejecutado"<<endl;
        json.set_output(0);
       
        json.close_json();
        json.create_json(path+"/Automate/result/transitions.json");
    }
    return 0;
}