#ifndef DDL_LINES
#define DDL_LINES
#include <iostream>
#include <unordered_map>
#include <functional>
#include <string>

#include "params.h"


using namespace std;

namespace ddl_lines{
    

class LineList {
private:
    Node* head;
    Node* tail;
    int next_id;                          
    std::unordered_map<int, Node*> index;

public:
    LineList() : head(nullptr), tail(nullptr), next_id(0) {}

    ~LineList() {
        Node* cur = head;
        while (cur) {
            Node* nxt = cur->next;
            delete cur->data;
            delete cur;
            cur = nxt;
        }
    }

    Node* get_head() const {
        return head;
    }

    int push_back(Line* data) {
        Node* node = new Node(next_id, data);
        if (!tail) {
            head = tail = node;
        } else {
            tail->next = node;
            node->prev = tail;
            tail = node;
        }
        data->set_parent(node);
        index[node->id] = node;
        return next_id++;
    }

    Node* emplace(int key, Line* data) {
        Node* node = new Node(key, data);
        if (!tail) {
            head = tail = node;
        } else {
            tail->next = node;
            node->prev = tail;
            tail = node;
        }
        data->set_parent(node);
        index[key] = node;
        return node;
    }

    Line* get_line(int key) {
        auto it = index.find(key);
        return it != index.end() ? it->second->data : nullptr;
    }

    Node* get_node(int id) {
        auto it = index.find(id);
        return it != index.end() ? it->second : nullptr;
    }

    /*int insert_after(int after_id, Line* new_line) {
        Node* prev_node = get_node(after_id);
        if (!prev_node) return -1; 

        Node* node = new Node(next_id, new_line);
        Node* next_node = prev_node->next;

        prev_node->next = node;
        node->prev = prev_node;
        node->next = next_node;

        if (next_node) next_node->prev = node;
        else tail = node;

        new_line->set_parent(node);
        index[node->id] = node;
        return next_id++;
    }*/

    void remove(int id) {
        Node* node = get_node(id);
        if (!node) return;

        Node* next_node = node->next;

        if (node->prev) node->prev->next = node->next;
        else head = node->next;

        if (node->next) node->next->prev = node->prev;
        else tail = node->prev;

        index.erase(id);
        delete node->data;
        delete node;

        for (Node* cur = next_node; cur != nullptr; cur = cur->next) {
            index.erase(cur->id);
            cur->id -= 1;
            cur->data->command.line_key = cur->id;
            index[cur->id] = cur;
        }
    }

    void for_each_lines(const std::function<void(Line*)>& fn) const {
        Node* cur = head;
        while (cur) {
            fn(cur->data);
            cur = cur->next;
        }
    }

    void for_each_node(const std::function<void(Node*)>& fn) const {
        Node* cur = head;
        while (cur) {
            fn(cur);
            cur = cur->next;
        }
    }

    Node* split_after(Node* current, Line* new_line) {
        if (!current) return nullptr;

        Node* next_node = current->next;

        for (Node* cur = next_node; cur != nullptr; cur = cur->next) {
            index.erase(cur->id);
            cur->id += 1;
            cur->data->command.line_key = cur->id;
            index[cur->id] = cur;
        }

        int new_key = current->id + 1;
        Node* node = new Node(new_key, new_line);

        current->next = node;
        node->prev = current;
        node->next = next_node;
        if (next_node) next_node->prev = node;
        else tail = node;

        index[new_key] = node;
        new_line->set_parent(node);
        return node;
    }

    Node* merge_with_prev(Node* current) {
    /*ddl*/
    if (!current || !current->prev) return nullptr; 

    Node* prev_node = current->prev;

    if (!prev_node->data->context.empty() && prev_node->data->context.back() == '\n') {
        prev_node->data->context.pop_back();
    }
    prev_node->data->context += current->data->context;

    Node* next_node = current->next;
    prev_node->next = next_node;
    if (next_node) next_node->prev = prev_node;
    else tail = prev_node;

    /*HASH*/
    index.erase(current->id);
    delete current->data;
    delete current;

    for (Node* cur = next_node; cur != nullptr; cur = cur->next) {
        index.erase(cur->id);
        cur->id -= 1;
        cur->data->command.line_key = cur->id;
        index[cur->id] = cur;
    }

    return prev_node;
}

    int get_id_by_position(int position) const {
        int i = 0;
        Node* cur = head;
        while (cur) {
            if (i == position) return cur->id;
            cur = cur->next;
            ++i;
        }
        return -1;
    }
};

}

#endif