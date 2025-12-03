#pragma once

#include <cstdint>

#include "configs/pt_config.h"

// Reads the pressure from the specified pressure transducer in PSI.
float read_pt(Pt pt);

// Tares all pressure transducers by taking the specified number of samples
// and averaging them to set a zero reference point.
void tare_all_pts(int samples, int delay_ms_between_samples = 10);