#pragma once

#include <cstdint>

enum class Pt {
  kChamber,
  kInjectorGox,
  kInjectorEth,
  kEthN2Reg,
  kEthLine,
  kGoxReg,
  kGoxLine,
  kPtMax  // Not a valid PT, used for bounds checking.
};

// Reads the pressure from the specified pressure transducer in PSI.
float read_pt(Pt pt);
