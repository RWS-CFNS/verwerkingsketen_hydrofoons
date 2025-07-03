#include <iostream>
#include <string>
#include <vector>
#include <cstdio>
#include <memory>
#include <array>

std::string exec(const char* cmd) {
    std::array<char, 128> buffer;
    std::string result;
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd, "r"), pclose);
    if (!pipe) return "ERROR";
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr)
        result += buffer.data();
    return result;
}

int main() {
    std::string list = exec("arecord -l | grep -i scarlett | grep '^card'");
    std::vector<int> foundCards;

    size_t pos = 0;
    while ((pos = list.find("card ")) != std::string::npos) {
        list = list.substr(pos + 5);
        int card = std::stoi(list);
        foundCards.push_back(card);
        std::string checkCmd = "amixer -c " + std::to_string(card) + " get 'Line In 1 Phantom Power'";
        std::string status = exec(checkCmd.c_str());
        if (status.find("[off]") != std::string::npos) {
            std::string toggleCmd = "amixer -c " + std::to_string(card) + " set 'Line In 1 Phantom Power' toggle";
            exec(toggleCmd.c_str());
        }
    }

    for (int card : foundCards)
        std::cout << card << std::endl;

    return 0;
}
