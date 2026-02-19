#include "../include/AudioEngine.h"
#include <iostream>
#include <vector>

// If Simulation is OFF (commented out in Common.h), we include PortAudio
#ifndef SIMULATION_MODE
#include "../include/portaudio.h"
#endif

AudioEngine::AudioEngine() : isRunning(false) {
    #ifndef SIMULATION_MODE
    // Initialize Real Hardware Driver
    PaError err = Pa_Initialize();
    if(err != paNoError) {
        std::cerr << "[Audio] CRITICAL ERROR: PortAudio failed to start: " << Pa_GetErrorText(err) << std::endl;
    } else {
        std::cout << "[Audio] PortAudio Hardware Driver Initialized." << std::endl;
    }
    #else
    std::cout << "[Audio] Simulation Mode Active." << std::endl;
    #endif
}

AudioEngine::~AudioEngine() {
    stop();
    #ifndef SIMULATION_MODE
    Pa_Terminate();
    #endif
}

std::vector<MicConfig> AudioEngine::scanDevices() {
    std::vector<MicConfig> devices;

    #ifdef SIMULATION_MODE
        // FAKE DATA (If you forgot to comment out SIMULATION_MODE in Common.h)
        devices.push_back({0, "Microsoft Sound Mapper", true});
        devices.push_back({1, "USB Mic (Left)", true});
        devices.push_back({2, "USB Mic (Right)", true});
        devices.push_back({3, "USB Mic (Top)", true});
    #else
        // REAL HARDWARE SCANNING
        int numDevices = Pa_GetDeviceCount();
        if(numDevices < 0) {
            std::cerr << "[Audio] No devices found or driver error." << std::endl;
            return devices;
        }

        const PaDeviceInfo* deviceInfo;
        for(int i = 0; i < numDevices; i++) {
            deviceInfo = Pa_GetDeviceInfo(i);

            // We only want Microphones (Inputs), not Speakers
            if(deviceInfo->maxInputChannels > 0) {
                MicConfig mic;
                mic.id = i;
                mic.name = deviceInfo->name;
                mic.isActive = true;

                devices.push_back(mic);

                // Print to Black Console so you can see it
                std::cout << "[Found Mic] ID: " << i << " | Name: " << mic.name << std::endl;
            }
        }
    #endif

    return devices;
}

// Keep these placeholders for now
bool AudioEngine::startListening(int micA, int micB, int micC) { return true; }
std::vector<double> AudioEngine::getBuffer(int micIndex) { return std::vector<double>(); }
void AudioEngine::stop() { isRunning = false; }
