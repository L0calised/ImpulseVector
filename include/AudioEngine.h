
#ifndef AUDIOENGINE_H
#define AUDIOENGINE_H

#include "Common.h"
#include <vector>

class AudioEngine {
public:
    AudioEngine();
    ~AudioEngine();

    // Scan for devices (wraps PortAudio)
    std::vector<MicConfig> scanDevices();

    // Start listening on the 3 selected mics
    bool startListening(int micA, int micB, int micC);

    // Get the latest audio buffer (for math processing)
    std::vector<double> getBuffer(int micIndex);

    // Stop everything
    void stop();

private:
    bool isRunning;
    // Add PortAudio stream objects here later
};

#endif
