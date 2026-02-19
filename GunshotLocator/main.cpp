#include <iostream>
#include <fstream>   // <--- THIS WAS MISSING. It fixes the "incomplete type" error.
#include <thread>
#include <chrono>
#include "include/Common.h"
#include "include/ConfigManager.h"
#include "include/AudioEngine.h"
#include "include/Triangulation.h"

using namespace std;

int main() {
    cout << "=== Hunting Detection System v1.0 ===" << endl;

    // 1. Setup Modules
    ConfigManager config;
    AudioEngine audio;
    Triangulation math;

    // 2. Hardware Scan
    cout << "--- Phase 1: Hardware Scan ---" << endl;
    vector<MicConfig> devices = audio.scanDevices();
    config.saveAvailableDevices(devices);
    cout << ">> Open your Web UI to select microphones now." << endl;
    cout << ">> Press ENTER when config.txt is ready..." << endl;
    cin.get();

    // 3. Load User Config
    if (!config.loadConfig("config.txt")) {
        cout << "Critical Error: Config not found." << endl;
        return -1;
    }

    // 4. Start System
    audio.startListening(config.getMicID_A(), config.getMicID_B(), config.getMicID_C());

    // 5. Main Loop (Simulating continuous detection)
    cout << "--- Phase 2: Monitoring Active ---" << endl;
    int eventID = 0;
    while (true) {
        // Simulate a gunshot event every 10 seconds
        this_thread::sleep_for(chrono::seconds(10));
        eventID++;

        cout << "\n[EVENT " << eventID << "] Loud noise detected!" << endl;

        // 1. Calculate Fake Coordinates
        Location loc;
        loc.x = 15.5 + (rand() % 5); // Add random jitter
        loc.y = 20.2 + (rand() % 5);

        // 2. "Save" Audio File (Create a dummy empty file for Python to find)
        //ofstream audioFile("event_audio.wav");
        //audioFile << "RIFF....WAVE"; // Fake header
        //audioFile.close();
        std::ifstream src("test_shot.wav", std::ios::binary);
        std::ofstream dst("event_audio.wav", std::ios::binary);
        dst << src.rdbuf();
        src.close();
        dst.close();

        cout << "[System] Real audio copied for analysis." << endl;
        cout << "[System] Audio recorded: event_audio.wav" << endl;

        // 3. Write Metadata for Python to pick up
        ofstream json("live_data.json");
        if (json.is_open()) {
             // We add "status": "analyzing" so the web UI knows to wait
             json << "{"
                  << "\"x\": " << loc.x << ", "
                  << "\"y\": " << loc.y << ", "
                  << "\"timestamp\": " << time(0) << ", "
                  << "\"status\": \"analyzing\""
                  << "}";
             json.close();
        }

        cout << "[System] Alert sent to Web UI." << endl;
    }
    return 0;
}
