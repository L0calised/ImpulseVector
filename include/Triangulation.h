
#ifndef TRIANGULATION_H
#define TRIANGULATION_H

#include "Common.h"

class Triangulation {
public:
    // Main function: takes 3 audio buffers, returns X,Y
    Location calculateSource(const std::vector<double>& buffA,
                             const std::vector<double>& buffB,
                             const std::vector<double>& buffC);

private:
    // Helper to find time delay between two signals
    double getTDOA(const std::vector<double>& s1, const std::vector<double>& s2);
};

#endif
