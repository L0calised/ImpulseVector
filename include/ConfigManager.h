
#ifndef CONFIGMANAGER_H
#define CONFIGMANAGER_H

#include "Common.h"
#include <vector>
#include <string>

class ConfigManager {
public:
    // Load mic IDs from config.txt (created by UI)
    bool loadConfig(const std::string& filename);

    // Save detected mic list for the UI to read
    void saveAvailableDevices(const std::vector<MicConfig>& devices);

    int getMicID_A() const { return micA_ID; }
    int getMicID_B() const { return micB_ID; }
    int getMicID_C() const { return micC_ID; }

private:
    int micA_ID = -1;
    int micB_ID = -1;
    int micC_ID = -1;
};

#endif
