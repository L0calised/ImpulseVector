
#ifndef COMMON_H
#define COMMON_H

#include <string>
#include <vector>

// Structure to hold microphone configuration
struct MicConfig {
    int id;
    std::string name;
    bool isActive;
};

// Structure to hold the calculated location
struct Location {
    double x;
    double y;
    double angle;
    bool isGunshot; // True if ML confirms it
};

// A "Switch" to let you test the code WITHOUT the real hardware/PortAudio library first.
// Comment this line out when you are ready to link the real PortAudio .dll
//#define SIMULATION_MODE

#endif
