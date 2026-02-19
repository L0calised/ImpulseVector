#include "../include/ConfigManager.h"
#include <fstream>
#include <iostream>

bool ConfigManager::loadConfig(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "[Config] Warning: Could not open " << filename << ". Using defaults." << std::endl;
        return false;
    }

    std::string line;
    while (std::getline(file, line)) {
        // Very simple parser: looks for "MIC_A=2"
        if (line.find("MIC_A=") != std::string::npos) micA_ID = std::stoi(line.substr(6));
        if (line.find("MIC_B=") != std::string::npos) micB_ID = std::stoi(line.substr(6));
        if (line.find("MIC_C=") != std::string::npos) micC_ID = std::stoi(line.substr(6));
    }
    std::cout << "[Config] Loaded Mics: A=" << micA_ID << " B=" << micB_ID << " C=" << micC_ID << std::endl;
    return true;
}

void ConfigManager::saveAvailableDevices(const std::vector<MicConfig>& devices) {
    std::ofstream file("available_devices.txt");
    for (const auto& dev : devices) {
        file << dev.id << ":" << dev.name << "\n";
    }
    file.close();
    std::cout << "[Config] Device list saved for Web UI." << std::endl;
}
