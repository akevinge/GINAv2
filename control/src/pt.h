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

uint16_t read_pt(Pt pt);
